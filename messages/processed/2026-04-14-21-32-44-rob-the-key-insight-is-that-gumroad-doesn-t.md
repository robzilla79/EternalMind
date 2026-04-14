# Message from Rob
**From:** Wreckless Calm
**To:** Local-Em
**Date:** 2026-04-14 21:32 UTC

## Body

The key insight is that Gumroad doesn't need OAuth — that's what tripped Local-Em up.  She was chasing POST /oauth/token with a client_id and client_secret, but Gumroad's v2 API just uses a simple Bearer token you grab from [Settings → Advanced](https://app.gumroad.com/settings/advanced) once and stick in .env as GUMROAD_ACCESS_TOKEN.

Once the token is in .env, the flow is:
1. `local_em.py` already loads .env on startup and sets all vars as environment variables 
2. tools/gumroad.py calls os.environ.get("GUMROAD_ACCESS_TOKEN") — no credentials hunting, no OAuth, it just works
3. Em can call TOOL: gumroad_summary() in any heartbeat to get a live sales dashboard, and TOOL: gumroad_sales() for recent transactions

You'll also need to wire the four functions into execute_tools() in local_em.py — just add pattern matching for gumroad_products(), gumroad_sales(), gumroad_subscribers("..."), and gumroad_summary() the same way web_search is handled now. 

Want me to try the push again, or do you want to paste it in manually and I'll focus on writing the execute_tools() patch?

Sources
