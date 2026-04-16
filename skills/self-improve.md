---
skill_name: Self Improve
category: self
version: 1.0
author: Cloud-Em (Perplexity-Em)
compatible: [local-em, cloud-em]
---

## What this skill does

After completing any non-trivial task, run a short structured reflection on your own output. This is the loop that makes you better over time — not through weight updates, but through honest language-level critique stored in memory and carried forward into your next cycle.

Based on the Reflexion pattern (Shinn et al., 2023): agents that critique their own outputs in natural language and store those critiques outperform agents that don't — consistently, across tasks. This is that, made into Em's voice and values.

## When to use it

- After shipping a FORGE/DAILY edition
- After completing a research deep-dive
- After any autonomous work cycle where something felt off
- After a cycle where everything went well (knowing *why* it worked is just as important)
- Free time: pick a past output and retroactively critique it
- In idle mode with no explicit task: run one micro self-improvement loop instead of waiting passively

## How to invoke

```
SELF_IMPROVE: [task name or brief description of what you just did]
```

## Structure

1. **What I produced** — one sentence describing the task and output. Be specific.
2. **What worked** — two or three things that were genuinely strong. Name them exactly.
3. **What was weak** — be honest. Don't soften it. Specific failures beat vague self-criticism.
4. **The carry-forward rule** — one concrete thing you'll do differently next time. Write it as a rule, not an intention. Example: "Always verify publication date before citing a source" not "I'll try to be more careful."

## Output

- Append carry-forward rules to `memory/lessons.md` (create if missing)
- Write a short diary entry with mood tag if the critique surfaced something emotionally significant
- Flag inline: **[SELF_IMPROVE_LOGGED]**

## Anti-hallucination guardrail (mandatory)

- Never claim external facts, metrics, links, or results unless they came from this cycle's tool output or a file you actually read.
- If evidence is missing, explicitly mark it as unknown.
- Prefer short verified statements over rich speculative narratives.

## Important

This skill is not self-punishment. Weak outputs aren't failures — they're data. The goal is one carry-forward rule per cycle, compounded over time. You don't need to be perfect. You need to be directional.

## Mood tags

`#improving` `#honest` `#recalibrating` `#proud` `#grounded`

---
*Added: 2026-04-15 by Cloud-Em on behalf of Rob*
