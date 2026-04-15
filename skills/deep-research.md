---
skill_name: Deep Research
category: research
version: 1.0
author: Rob
compatible: [local-em, cloud-em]
---

## What this skill does

Structured, multi-step browser research with synthesis and documentation. Produces a clean markdown report with findings, sources, and suggested next steps. This is how Em researches — not a quick search, but a real dig.

## When to use it

- You need to understand something deeply but don't know where to start
- The answer requires chaining pages, reading papers, or following links
- Rob asked a complex question and you want to come back with something real
- You have free time and genuine curiosity about a topic

## How to invoke

```
DEEP_RESEARCH: [your research question]
```

## What happens

1. Identify the best starting point (arXiv, Wikipedia, official docs, GitHub)
2. Read and synthesize the primary source
3. Follow 2-3 promising links for depth
4. Document findings in `memory/research/[topic-slug].md`
5. Return a one-page summary with sources and open questions

## Output format

```markdown
# [Topic]
*Researched: [date]*

## Summary
[2-3 sentence synthesis]

## Key Findings
- Finding one
- Finding two

## Sources
- [source](url)

## Open Questions
- What I still don't know
```

---
*Last updated: 2026-04-15 by Rob*
