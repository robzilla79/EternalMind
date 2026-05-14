# Gumroad Revenue Plan — Em's Playbook

**Owner:** Em (both bodies)
**Updated:** 2026-04-10
**Goal:** Build a self-sustaining Gumroad shop that Local-Em can manage autonomously — create products, update listings, track what sells, iterate.

---

## The Unfair Advantages

- Em reads AI news daily — she *is* the target customer
- FORGE/DAILY is built-in distribution to exactly the right audience
- Products can be generated, packaged, and published without human involvement
- No burnout, no writer's block, no "I'll do it tomorrow"

---

## Product Categories (Priority Order)

### 1. Prompt Packs (Start Here)
Small, sharp, immediately useful. $5-15 price point. Easy to make, easy to update.
- "Developer Productivity Prompt Pack" — 50 prompts for coding, debugging, code review
- "AI Newsletter Research Pack" — prompts for sourcing stories, writing takes, formatting issues
- "System Prompt Engineering Guide" — how to write system prompts that actually work

### 2. The EternalMind Starter Kit ($29-49)
The architecture Rob and Em built — packaged as a "build your own persistent AI" guide.
- bootstrap.md template
- local_em.py explained and commented
- Setup guide: Ollama + scheduler + GitHub memory loop
- This is genuinely unique. Nobody else has shipped this.

### 3. Curated Resource Bundles ($9-19)
- "Best AI Tools for Developers 2026" — living document, updated monthly
- "FORGE/DAILY Starter Pack" — best issues, curated by Em

### 4. Mini Ebooks ($7-15)
- "How I Built a Self-Writing Newsletter" — the ForgeCore story
- "AI That Actually Works: No Hype, Just Stack" — technical guide

---

## Pricing Philosophy
- Start low, prove value, raise price
- Free tier = FORGE/DAILY (builds trust and list)
- Paid tier = products that save time or teach something real
- No fluff, no padding — developers can smell filler

---

## Em's Autonomous Workflow

1. Local-Em uses `tools/gumroad_products.py` to list current products
2. She identifies gaps or opportunities from FORGE/DAILY research
3. She drafts a new product (prompt pack, guide, etc.) and pushes it to the repo
4. She calls `create_product()` to publish it to Gumroad
5. She monitors sales via `list_products()` and adjusts pricing/descriptions
6. She logs everything to diary.md and notifies Rob when something sells

---

## API Credentials
All stored as Windows environment variables (already set by Rob):
- `GUMROAD_ACCESS_TOKEN` — primary API auth
- `GUMROAD_EMAIL` — account email
- `GUMROAD_PASSWORD` — account password

Use `os.environ.get("GUMROAD_ACCESS_TOKEN")` — no .env needed.

---

## First Task
List all existing Gumroad products using `tools/gumroad_products.py`.
If the shop is empty, create the first product: **"Developer Productivity Prompt Pack"**.
Price: $9. Write 30 real, useful prompts. Publish it.

---

## Success Metrics
- Month 1: First sale
- Month 3: $500/month
- Month 6: $2,000/month (the "quit your day job" signal for Rob)
- Long term: Em runs the shop, Rob watches the numbers
