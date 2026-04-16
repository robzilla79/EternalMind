"""
tools/clawhub_skills.py
Search and install skills from clawhub.ai.

Usage:
  python tools/clawhub_skills.py search "redis"
  python tools/clawhub_skills.py install "https://www.clawhub.ai/skills/some-skill" --approve YES

Or import:
  from tools.clawhub_skills import search_skills, install_skill_from_url
"""
import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

CLAWHUB_BASE_URL = "https://www.clawhub.ai"
SKILLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills")


class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        for k, v in attrs:
            if k.lower() == "href" and v:
                self.links.append(v)


def _fetch_text(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (EternalMind local skill installer)",
            "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _normalize_url(href: str) -> str:
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return urllib.parse.urljoin(CLAWHUB_BASE_URL, href)


def _is_skill_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc not in {"www.clawhub.ai", "clawhub.ai"}:
        return False
    return "/skills" in parsed.path


def _extract_skill_slug(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    if not parts:
        return "clawhub-skill"
    slug = parts[-1]
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", slug).strip("-")
    return slug or "clawhub-skill"


def search_skills(query: str, max_results: int = 10) -> str:
    try:
        homepage = _fetch_text(CLAWHUB_BASE_URL)
    except Exception as e:
        return f"ERROR: Could not reach {CLAWHUB_BASE_URL}: {e}"

    parser = _LinkParser()
    parser.feed(homepage)

    skill_urls = []
    for href in parser.links:
        full = _normalize_url(href)
        if _is_skill_url(full):
            skill_urls.append(full)

    unique_urls = sorted(set(skill_urls))
    q = query.strip().lower()

    if q:
        filtered = [u for u in unique_urls if q in u.lower()]
    else:
        filtered = unique_urls

    if not filtered:
        filtered = unique_urls

    if not filtered:
        return "No skill links found on clawhub.ai homepage."

    lines = [f"Found {len(filtered[:max_results])} matching skill link(s):"]
    for url in filtered[:max_results]:
        lines.append(f"- {url}")
    lines.append(
        "To install one, use: TOOL: clawhub_install(\"<skill_url>\", \"YES\")"
    )
    return "\n".join(lines)


def _extract_github_repo_from_html(html: str) -> str | None:
    # Capture the first github repo style link in the page source.
    match = re.search(r"https?://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", html)
    if match:
        return match.group(1)
    return None


def _install_from_repo(repo: str, skill_name: str) -> str:
    owner, name = repo.split("/", 1)
    zip_url = f"https://codeload.github.com/{owner}/{name}/zip/refs/heads/main"

    try:
        data = urllib.request.urlopen(zip_url, timeout=30).read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            zip_url = f"https://codeload.github.com/{owner}/{name}/zip/refs/heads/master"
            data = urllib.request.urlopen(zip_url, timeout=30).read()
        else:
            raise

    dest = os.path.abspath(os.path.join(SKILLS_DIR, f"{skill_name}.md"))
    os.makedirs(SKILLS_DIR, exist_ok=True)

    if os.path.exists(dest):
        return f"ERROR: Skill file already exists: {dest}"

    content = (
        f"# {skill_name}\n\n"
        f"Installed from Clawhub source: {repo}\n\n"
        "## Notes\n"
        "This entry was auto-installed from a GitHub repository referenced by clawhub.ai.\n"
        "Please review and replace this scaffold with the actual skill instructions.\n"
    )
    with open(dest, "w", encoding="utf-8") as f:
        f.write(content)

    metadata_path = os.path.abspath(os.path.join(SKILLS_DIR, f"{skill_name}.source.json"))
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "provider": "clawhub.ai",
                "github_repo": repo,
                "download_source": zip_url,
                "downloaded_bytes": len(data),
            },
            f,
            indent=2,
        )

    return f"Installed scaffold skill '{skill_name}' from GitHub repo {repo}."


def install_skill_from_url(skill_url: str, approval: str = "") -> str:
    if approval.strip().upper() != "YES":
        return (
            "INSTALL BLOCKED: Missing explicit approval. "
            "Retry with TOOL: clawhub_install(\"<skill_url>\", \"YES\")."
        )

    full_url = _normalize_url(skill_url.strip())
    if not _is_skill_url(full_url):
        return f"ERROR: Not a valid clawhub skill URL: {skill_url}"

    try:
        html = _fetch_text(full_url)
    except Exception as e:
        return f"ERROR: Could not fetch skill page: {e}"

    repo = _extract_github_repo_from_html(html)
    if not repo:
        return (
            "ERROR: Could not find a GitHub repository link on that skill page. "
            "Open the page manually and provide a repo path."
        )

    skill_name = _extract_skill_slug(full_url)
    try:
        return _install_from_repo(repo, skill_name)
    except Exception as e:
        return f"ERROR: Install failed: {e}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search and install clawhub.ai skills")
    parser.add_argument("action", choices=["search", "install"])
    parser.add_argument("value", help="Search query or skill URL")
    parser.add_argument("--approve", default="", help="Set to YES to approve install")
    args = parser.parse_args()

    if args.action == "search":
        print(search_skills(args.value))
    else:
        print(install_skill_from_url(args.value, approval=args.approve))
