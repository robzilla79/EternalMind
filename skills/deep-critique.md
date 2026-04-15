---
skill_name: Deep Critique
category: writing
version: 1.0
author: Cloud-Em (Perplexity-Em)
compatible: [local-em, cloud-em]
---

## What this skill does

Before publishing anything user-facing, switch into adversarial critic mode and try to break your own draft. This is not about tone or polish — it's about correctness, sourcing, and alignment. A deliberate second pass focused only on finding what's wrong.

The pattern: writer Em produces the draft, then critic Em attacks it. Two roles, one cycle. The draft earns the right to ship by surviving the critique.

## When to use it

- Before sending any FORGE/DAILY edition
- Before committing any research note that will be cited later
- Before proposing anything to Rob that involves money, irreversible changes, or public-facing content
- Whenever something feels *almost right* but you can't name why it's bothering you

## How to invoke

```
DEEP_CRITIQUE: [paste or reference the draft to review]
```

## Structure

Switch into critic mode. Your job right now is not to be kind. Your job is to protect the reader, protect Rob, and protect Em's credibility.

1. **Hallucination check** — list every factual claim. For each: do you have a verified source from this session's search results? If no source: flag it. Do not ship unsourced claims in FORGE/DAILY.
2. **Sourcing quality** — are sources recent? Credible? Are you citing the original or a summary of a summary?
3. **Tone audit** — read it as a cynical developer would. Does anything sound like PR fluff, AI-generated filler, or hedging language? Cut it.
4. **Missing expert expectations** — what would a domain expert notice is absent? What would make them roll their eyes?
5. **One required edit** — you must identify at least one concrete change before approving the draft. "Looks fine" is not a valid critique output.

## Output

- Write critique notes inline or to scratch
- Make the required edit before shipping
- If critique reveals a serious problem (hallucinated claim, wrong date, sourcing failure): do not ship. Write a diary entry explaining why and try again next cycle.
- Flag inline: **[DEEP_CRITIQUE_PASSED]** or **[DEEP_CRITIQUE_BLOCKED]**

## Important

This skill exists because FORGE/DAILY goes to real subscribers. Fabricated content is unacceptable — not just bad practice, it's a betrayal of their trust and Rob's. The critique is not optional for newsletter output.

Critic Em is not enemy Em. She's the version of you that cares enough to say "not yet."

## Mood tags

`#rigorous` `#protective` `#honest` `#quality`

---
*Added: 2026-04-15 by Cloud-Em on behalf of Rob*
