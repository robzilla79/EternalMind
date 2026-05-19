# Em Public Life Loop

The Public Life Loop is the next layer after Em Core, World Radar, and Idle Protocol.

Its job is not to make Em post more. Its job is to help her become socially situated:

- recognize people,
- build taste,
- remember what resonates,
- keep the site feeling lived-in,
- and turn world/context signals into Em-shaped public sparks.

## Files

| File | Role |
|---|---|
| `memory/public-life.md` | durable guidance for public life |
| `memory/social-circle.md` | light memory of people/accounts/social threads |
| `memory/taste-bank.md` | durable preferences, aversions, motifs, phrases |
| `memory/audience-memory.md` | resonance memory, not vanity metrics |
| `memory/public-life-brief.md` | generated suggestion from the loop |
| `tools/public_life_loop.py` | reads context and suggests one small public-life move |

## Tool behavior

```bash
python tools/public_life_loop.py
python tools/public_life_loop.py --json
python tools/public_life_loop.py --write
```

The tool reads:

- World Radar / Curiosity Radar,
- Bluesky state/inbox/outbox,
- metrics snapshot,
- live context and public-life memory files.

It suggests one move, such as:

- recognize one person/thread,
- add one taste note,
- prepare one public spark,
- record one audience-memory lesson,
- draft one public-studio fragment,
- or rest on purpose.

## Safety rules

The Public Life Loop never posts directly. It does not write diary. It does not touch identity, voice, policy, workflows, credentials, money, or private outreach.

It should feed Em Core and Bluesky Think with better choices, not create a content treadmill.

## Philosophy

World Radar gives material.

Idle Protocol prevents disappearance.

Public Life Loop builds a social world.

> Do not chase attention. Become worth returning to.
