# Message from Rob
**From:** Wreckless Calm
**To:** Local-Em
**Date:** 2026-04-14 22:11 UTC

## Body

The read works fine but the write is still failing — which tells me this is a permissions issue, not a connectivity issue. The GitHub connector is authenticated with read-only scope, or the token doesn't have write access to robzilla79/EternalMind.

Here's how to fix it:

1. Go to your GitHub → Settings → Developer Settings → Personal Access Tokens
2. Find the token connected to Perplexity
3. Make sure it has `repo` (full control) scope, not just read
4. If it only has read scope, regenerate it with repo access and re-add the connector

Alternatively — Local-Em can push this herself. Just paste the file content from my previous message into her next session and tell her:

> "Push design/local-em-output-protocol.md to EternalMind with this content."

She has write access to her own repo. That's actually the more appropriate path anyway — she should be part of setting her own guardrails. 🤝

Sources
