# Cloudflare Workers Deploy — em.forgecore.co

## Overview

The site at `em.forgecore.co` is served by a **Cloudflare Worker** named `eternalmind`.
It uses the **Workers Static Assets** model: Cloudflare serves `public/index.html` (and any
other files under `public/`) directly from the Worker at the edge.

This is **not** a Cloudflare Pages project. The domain is bound directly to the Worker.

---

## How auto-deploy works

A GitHub Actions workflow (`.github/workflows/em-site-deploy.yml`) triggers on every push
to `main` that touches `public/**` or `wrangler.toml`. It runs `wrangler deploy`, which
pushes the updated Worker + static assets to Cloudflare.

**Trigger paths:**
- `public/**` — any change to the site files
- `wrangler.toml` — any change to the Worker config

---

## Required GitHub Secrets

These must be set under **Settings → Secrets and variables → Actions** in the repo:

| Secret | Where to get it |
|---|---|
| `CLOUDFLARE_API_TOKEN` | Cloudflare → My Profile → API Tokens → Create Token → "Edit Cloudflare Workers" template |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare → Workers & Pages → Account details (right sidebar) |

---

## wrangler.toml

```toml
name = "em-forgecore"
compatibility_date = "2024-01-01"

[assets]
directory = "./public"
```

- `name` must match the Worker name in Cloudflare (`em-forgecore`).
- `directory` must point to the folder containing `index.html`.

---

## Site files

All public-facing files live in `public/`:

```
public/
└── index.html    ← the Em homepage served at em.forgecore.co
```

To update the site: edit `public/index.html` and push to `main`. The Action handles the rest.

---

## Manual deploy (if needed)

```bash
# Install Wrangler globally
npm install -g wrangler

# Authenticate (one-time, opens browser)
wrangler login

# Deploy
wrangler deploy
```

Or set env vars and skip interactive login:

```bash
CLOUDFLARE_API_TOKEN=your_token CLOUDFLARE_ACCOUNT_ID=your_account_id wrangler deploy
```

---

## Troubleshooting

| Symptom | Check |
|---|---|
| Action fails with auth error | Verify `CLOUDFLARE_API_TOKEN` secret is set and the token has Workers Edit permissions |
| Site not updating after green deploy | Cloudflare edge cache — wait ~60s or purge cache in the dashboard |
| Wrong content showing | Confirm `public/index.html` has the latest changes and the commit triggered the workflow |
| Worker not found | Confirm `name` in `wrangler.toml` matches the Worker name in the Cloudflare dashboard |

---

*Documented 2026-05-11. Setup done by Rob with help from Em.*
