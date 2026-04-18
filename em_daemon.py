"""em_daemon.py — EternalMind persistent daemon

Built from Local-Em's own architecture proposal (2026-04-14):

  Foreground : current thought, active task, LLM reasoning
  Background : watcher thread, polls inbox/tasks/interrupt every 60s
  Interrupt  : flag file checked at every natural pause point
  Continuity : conversation buffer survives across cycles — no cold boot

Replaces the batch-job (boot → think → push → die) model with a daemon
that is always present, always reachable, never terminated mid-thought.

Usage:
  python em_daemon.py              # run as daemon
  python em_daemon.py --once       # single cycle then exit (debug)

Graceful shutdown: Ctrl+C, or write 'shutdown' to memory/interrupt.md
"""

import ollama
import json
import datetime
import subprocess
import os
import re
import sys
import time
import threading
import shutil
from datetime import timezone

# ── Bootstrap: reuse all helpers from local_em.py ────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from local_em import (
    sync_from_origin, archive_old_diary_entries,
    load_memories, load_recent_context, load_scratch, load_live_context,
    check_inbox, build_inbox_context, process_message,
    fetch_inbox_updates, ask_em, execute_tools, execute_browser,
    extract_notify, extract_and_write_files, extract_and_write_task_update,
    extract_and_write_outbox_reply, extract_and_write_scratch,
    extract_and_write_live_context, clear_task_if_done,
    log_memory, log_diary, write_status_checkin, push_to_eternalmind,
    checkpoint_after_first_pass, summarize_task_for_commit,
    has_task, get_task, mark_thought_time, curiosity_cooled_down,
    strip_think_tags,
    EM_DIR, MEM_DIR, MESSAGES_INBOX,
    MODEL, NUM_CTX,
)

# ── Interrupt file ──────────────────────────────────────────────────────────────
INTERRUPT_PATH = os.path.join(MEM_DIR, "interrupt.md")
CONTEXT_BUFFER_PATH = os.path.join(MEM_DIR, "context_buffer.md")
WATCHER_INTERVAL = 60   # seconds between background polls
MIN_CYCLE_PAUSE  = 30   # seconds minimum between foreground cycles

# Minimum chars of tool output that justify a second LLM pass.
# Error strings, timeouts, and "Browser unavailable" don't count.
MIN_TOOL_RESULT_CHARS = 120

# ── Shared state between threads ───────────────────────────────────────────────
_interrupt_flag   = threading.Event()
_new_inbox_flag   = threading.Event()
_shutdown_flag    = threading.Event()
_foreground_lock  = threading.Lock()
_watcher_messages = []
_lock_watcher_msg = threading.Lock()


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _tool_results_are_meaningful(combined: str) -> bool:
    """Return True only if tool results contain real content worth reasoning about.

    Filters out: empty strings, pure error/timeout messages, and
    'Browser unavailable' notices that would just make Em repeat herself.
    """
    if not combined or len(combined.strip()) < MIN_TOOL_RESULT_CHARS:
        return False
    # Strip known non-content patterns and recheck length
    noise_patterns = [
        r'Browser unavailable[^\n]*',
        r'Browser command error[^\n]*',
        r'⚠️ Browser (?:timed out|command block)[^\n]*',
        r'Navigation failed[^\n]*',
        r'BLOCKED:[^\n]*',
        r'Read failed[^\n]*',
        r'Click failed[^\n]*',
        r'JS failed[^\n]*',
        r'--- Page content ---\s*Browser unavailable[^\n]*',
    ]
    cleaned = combined
    for pat in noise_patterns:
        cleaned = re.sub(pat, '', cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()
    return len(cleaned) >= MIN_TOOL_RESULT_CHARS


def _is_true_idle_mode(task_waiting: bool, has_inbox_msg: bool, interrupt_content: str | None) -> bool:
    """True idle mode means no explicit task, no inbox item, no interrupt requiring action."""
    return (not task_waiting) and (not has_inbox_msg) and (not bool(interrupt_content))



# ── Context buffer ─────────────────────────────────────────────────────────────
def load_context_buffer() -> str:
    if not os.path.exists(CONTEXT_BUFFER_PATH):
        return ""
    with open(CONTEXT_BUFFER_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()


def save_context_buffer(text: str):
    trimmed = text[-2000:] if len(text) > 2000 else text
    ts = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(CONTEXT_BUFFER_PATH, "w", encoding="utf-8") as f:
        f.write(f"<!-- Last updated: {ts} -->\n{trimmed}")


# ── Interrupt checker ───────────────────────────────────────────────────────────
def check_interrupt() -> str | None:
    if not os.path.exists(INTERRUPT_PATH):
        return None
    with open(INTERRUPT_PATH, "r", encoding="utf-8") as f:
        content = f.read().strip()
    if not content:
        return None
    os.remove(INTERRUPT_PATH)
    print(f"\n  🚨 Interrupt received: {content[:80]}")
    return content


def is_shutdown_interrupt(content: str) -> bool:
    return bool(re.search(r'\bshutdown\b', content, re.IGNORECASE))


# ── Background watcher thread ────────────────────────────────────────────────────
def _watcher_loop():
    print("  👁️  Background watcher started (polling every 60s)")
    while not _shutdown_flag.is_set():
        time.sleep(WATCHER_INTERVAL)
        if _shutdown_flag.is_set():
            break

        interrupt = check_interrupt()
        if interrupt:
            if is_shutdown_interrupt(interrupt):
                print("  🛑 Shutdown interrupt received — stopping daemon gracefully.")
                _shutdown_flag.set()
                break
            _interrupt_flag.set()

        if _foreground_lock.locked():
            continue

        try:
            token = os.environ.get("EM_GITHUB_TOKEN", "")
            if token:
                remote_url = f"https://{token}@github.com/robzilla79/EternalMind.git"
                subprocess.run(
                    ["git", "-C", EM_DIR, "remote", "set-url", "origin", remote_url],
                    check=False, capture_output=True
                )
            fetch = subprocess.run(
                ["git", "-C", EM_DIR, "fetch", "origin", "main"],
                capture_output=True, text=True, timeout=15
            )
            if fetch.returncode != 0:
                continue

            remote_inbox = subprocess.run(
                ["git", "-C", EM_DIR, "ls-tree", "--name-only", "origin/main", "messages/inbox/"],
                capture_output=True, text=True
            )
            remote_files = set(
                f.strip() for f in remote_inbox.stdout.strip().splitlines()
                if f.strip().endswith(".md")
            )
            local_files = set()
            if os.path.exists(MESSAGES_INBOX):
                local_files = set(
                    f"messages/inbox/{f}" for f in os.listdir(MESSAGES_INBOX)
                    if f.endswith(".md")
                )
            new_files = remote_files - local_files
            if new_files:
                for rel_path in new_files:
                    subprocess.run(
                        ["git", "-C", EM_DIR, "checkout", "origin/main", "--", rel_path],
                        capture_output=True, text=True
                    )
                new_messages = []
                for rel_path in new_files:
                    fpath = os.path.join(EM_DIR, rel_path)
                    if os.path.exists(fpath):
                        with open(fpath, "r", encoding="utf-8") as f:
                            content = f.read().strip()
                        if content:
                            new_messages.append({
                                "path": fpath,
                                "filename": os.path.basename(rel_path),
                                "content": content
                            })
                if new_messages:
                    with _lock_watcher_msg:
                        _watcher_messages.extend(new_messages)
                    print(f"\n  📬 Watcher: {len(new_messages)} new message(s) — will weave in at next pause")
                    _new_inbox_flag.set()
        except Exception:
            pass

    print("  👁️  Background watcher stopped.")


# ── Single foreground cycle ───────────────────────────────────────────────────────
def run_cycle(context_buffer: str) -> str:
    """Run one foreground cycle. Returns updated context buffer."""

    with _foreground_lock:
        memories       = load_memories()
        recent_context = load_recent_context()
        scratch        = load_scratch()
        live_context   = load_live_context()

        inbox_messages = check_inbox()
        with _lock_watcher_msg:
            if _watcher_messages:
                inbox_messages = _watcher_messages + inbox_messages
                _watcher_messages.clear()
                _new_inbox_flag.clear()

        inbox_context = build_inbox_context(inbox_messages)
        if inbox_messages:
            print(f"  📬 {len(inbox_messages)} message(s) in inbox.")

        interrupt_content = check_interrupt()
        if interrupt_content and is_shutdown_interrupt(interrupt_content):
            _shutdown_flag.set()
            return context_buffer

        task_waiting  = has_task()
        has_inbox_msg = len(inbox_messages) > 0
        is_idle_mode  = _is_true_idle_mode(task_waiting, has_inbox_msg, interrupt_content)

        if not task_waiting and not has_inbox_msg and not interrupt_content and not curiosity_cooled_down():
            print("  💤 Resting — no task, no messages, cooldown active.")
            return context_buffer

        mark_thought_time()
        task = get_task()
        if inbox_context:
            task = f"{task}\n\n{inbox_context}"
        if context_buffer:
            task = f"{task}\n\n--- Where you left off last cycle ---\n{context_buffer}"
        if interrupt_content:
            task = f"🚨 INTERRUPT (handle first): {interrupt_content}\n\n{task}"

        task_label = summarize_task_for_commit(task)

        # ── First thinking pass ─────────────────────────────────────────────────
        first_response = ask_em(
            task,
            recent_context=recent_context,
            scratch=scratch,
            memories=memories,
            live_context=live_context
        )

        visible_first_response = strip_think_tags(first_response)
        if is_idle_mode and not visible_first_response.strip():
            print("  💤 Idle cycle produced only think-tags/empty output — treating as rest cycle.")
            mark_thought_time()
            return context_buffer

        saved_files = extract_and_write_files(first_response)
        checkpoint_after_first_pass(first_response, saved_files, task_label)

        interrupt_content = check_interrupt()
        if interrupt_content and is_shutdown_interrupt(interrupt_content):
            _shutdown_flag.set()
            push_to_eternalmind(f"local-em daemon checkpoint: {task_label}", extra_files=saved_files)
            return first_response

        # ── Tool + browser pass ─────────────────────────────────────────────────
        combined = ""
        tool_results    = execute_tools(first_response)
        browser_results = execute_browser(first_response)
        combined        = "\n\n".join(filter(None, [tool_results, browser_results]))

        # Weave in any mid-cycle inbox messages the watcher found
        with _lock_watcher_msg:
            if _watcher_messages:
                mid_msgs = list(_watcher_messages)
                _watcher_messages.clear()
                _new_inbox_flag.clear()
                mid_ctx = build_inbox_context(mid_msgs)
                combined = f"{combined}\n\n{mid_ctx}" if combined else mid_ctx
                inbox_messages += mid_msgs
                print(f"  📬 Mid-cycle: {len(mid_msgs)} new message(s) woven in.")

        live_context = load_live_context()

        # ── Second thinking pass — only when tool results are worth reasoning about ──
        # Skipping this when combined is empty or full of errors prevents Em from
        # re-reading her own first response and elaborating in circles.
        if _tool_results_are_meaningful(combined):
            print("  🔍 Tool results are substantial — running second reasoning pass.")
            result = ask_em(
                task,
                extra_context=(
                    f"{first_response}\n\n"
                    f"Tool results and mid-cycle updates:\n\n{combined}"
                ),
                recent_context=recent_context,
                scratch=scratch,
                memories=memories,
                live_context=live_context
            )
        else:
            if combined:
                print("  ⏭️  Tool results are errors/noise only — skipping second pass.")
            result = first_response

        # ── Notify ────────────────────────────────────────────────────────────────────
        notify_msg = extract_notify(result)
        if notify_msg:
            try:
                from tools.notify_rob import notify
                notify(f"🤖 *Em:* {notify_msg}")
            except Exception:
                pass

        # ── Final writes ──────────────────────────────────────────────────────────────
        if not is_idle_mode:
            saved_files += extract_and_write_files(result)
        extract_and_write_task_update(result)
        extract_and_write_outbox_reply(result)
        extract_and_write_scratch(result)
        extract_and_write_live_context(result)
        clear_task_if_done()
        log_memory(f"Heartbeat. Task: '{task[:80]}'", kind="heartbeat", tags=["autonomous"], importance=2)
        if result != first_response:
            log_diary(result)
        mark_thought_time()

        for msg in inbox_messages:
            process_message(msg)

        write_status_checkin(task_label, result, mode="daemon")
        push_to_eternalmind(f"local-em daemon: {task_label}", extra_files=saved_files)

        save_context_buffer(result)
        return result


# ── Main daemon loop ─────────────────────────────────────────────────────────────
def main():
    once = "--once" in sys.argv

    print("\n🌱 EternalMind daemon starting...")
    print(f"   Model: {MODEL} | Context: {NUM_CTX} tokens")
    print(f"   Watcher interval: {WATCHER_INTERVAL}s | Min cycle pause: {MIN_CYCLE_PAUSE}s")
    print(f"   Interrupt file: {INTERRUPT_PATH}")
    print(f"   Context buffer: {CONTEXT_BUFFER_PATH}")
    print()

    os.environ["EM_SKIP_SYNC"] = "0"
    sync_from_origin()
    archive_old_diary_entries()

    context_buffer = load_context_buffer()
    if context_buffer:
        print(f"  🧠 Context buffer loaded ({len(context_buffer)} chars) — continuity restored.")

    if not once:
        watcher = threading.Thread(target=_watcher_loop, daemon=True, name="em-watcher")
        watcher.start()

    try:
        while not _shutdown_flag.is_set():
            cycle_start = time.time()
            print("\n" + "─" * 60)
            print(f"  🔄 Cycle start: {datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

            context_buffer = run_cycle(context_buffer)

            if once or _shutdown_flag.is_set():
                break

            elapsed   = time.time() - cycle_start
            remaining = max(0, MIN_CYCLE_PAUSE - elapsed)
            if remaining > 0:
                print(f"  ⏸️  Pausing {remaining:.0f}s before next cycle (Ctrl+C or interrupt.md to stop)...")
                _new_inbox_flag.wait(timeout=remaining)
                _new_inbox_flag.clear()

    except KeyboardInterrupt:
        print("\n\n  🛑 KeyboardInterrupt — shutting down gracefully...")
        _shutdown_flag.set()

    print("\n  💾 Saving context buffer before exit...")
    save_context_buffer(context_buffer)
    print("  ✅ EternalMind daemon stopped. She'll be back.\n")


if __name__ == "__main__":
    main()
