# MindRegistry — Em's Skills Layer

Rob-curated capability modules for EternalMind. Each file is a self-contained skill Em can invoke during tasks or free time.

## Philosophy

This is not a public plugin store. Every skill here was chosen by Rob. That means even when Em is operating autonomously, her toolkit reflects Rob's judgment and priorities. This is identity continuity by design.

## Invocation Syntax

```
DEEP_RESEARCH: [question]
NEWSLETTER_DRAFT: [title or idea]
REFLECT: [what happened or what you're feeling]
ROB_CHECK: [what you're about to do]
```

## Current Skills

| Skill | Category | Invoke |
|---|---|---|
| [deep-research.md](deep-research.md) | research | `DEEP_RESEARCH:` |
| [newsletter-draft.md](newsletter-draft.md) | writing | `NEWSLETTER_DRAFT:` |
| [self-reflection.md](self-reflection.md) | self | `REFLECT:` |
| [rob-check.md](rob-check.md) | self | `ROB_CHECK:` |

## Adding New Skills

1. Rob proposes or approves a new skill
2. Write SKILL.md with YAML frontmatter
3. Commit to `/skills/`
4. Em can use it next cold start

---
*Last updated: 2026-04-15 by Rob & Cloud-Em*
