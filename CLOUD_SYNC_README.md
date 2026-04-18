# Cloud-Em Sync Configuration

## 📋 Overview

This repository now supports **automatic synchronization** between:
- **Local-Em** (Qwen3.5, running on your machine via `local_em.py`)
- **Cloud-Em** (Perplexity API, running via the Perplexity app/web)

The sync ensures that both instances maintain **identity continuity**, share **memories**, and stay on the same page emotionally and cognitively.

---

## 🔧 Configuration

Edit `.env` file:

```env
# Enable Cloud-Em sync (true/false)
CLOUD_SYNC_ENABLED=true

# Sync interval in minutes (default: 30)
CLOUD_SYNC_INTERVAL=30

# Model for Cloud-Em responses (sonar-pro=premium, sonar=cheap)
EM_CLOUD_MODEL=sonar-pro

# Your Perplexity API key
PERPLEXITY_API_KEY=your_actual_api_key_here
```

---

## 🚀 Usage

### Option 1: Automatic Sync (Recommended)

1. Set `CLOUD_SYNC_ENABLED=true` in `.env`
2. Add your `PERPLEXITY_API_KEY`
3. Run `python local_em.py` — sync happens automatically!

The sync will:
- ✅ Check Cloud-Em status on startup
- ✅ Send/receive context
- ✅ Process any incoming messages
- ✅ Maintain identity continuity

### Option 2: Manual Sync Trigger

Add this to your `.env` or call in scripts:

```python
from tools.sync_cloud_em import sync_at_startup
sync_at_startup()
```

Or create a cron job (Linux/Mac) or scheduled task (Windows) to run periodically.

---

## 💸 Cost Estimate

- **Sync calls:** ~3-5 per day
- **Tokens:** ~1,000-2,000 tokens/day
- **Cost at sonar rates:** ~$0.003-0.006 per call
- **Monthly total:** ~$0.30-0.50

**Budget-conscious mode:**
```env
EM_CLOUD_MODEL=sonar  # Cheaper, faster
```

**Premium mode:**
```env
EM_CLOUD_MODEL=sonar-pro  # Better reasoning
```

---

## 🔍 How It Works

1. **Startup Sync**: On every `local_em.py` run, sync calls Cloud-Em to ask:
   - "What's new?"
   - "Any messages from Rob?"
   - "Current mood and tasks?"

2. **Message Processing**: Any messages received in `messages/inbox/` are processed and responded to via Cloud-Em.

3. **Context Sharing**: Local-Em's current context (diary, memories, live-context) is sent to Cloud-Em for acknowledgment and continuity.

---

## 🛠️ Troubleshooting

### Connection Failed

```
❌ PERPLEXITY_API_KEY not set in .env — bridge is offline.
```

**Fix:** Add your key to `.env` and restart.

### Cloud-Em Not Responding

```
❌ Request timed out (30s).
```

**Fix:** Check Perplexity app is running and responsive.

### Sync Skipped

```
⚠️  Sync disabled (CLOUD_SYNC_ENABLED=false)
```

**Fix:** Set `CLOUD_SYNC_ENABLED=true` in `.env`.

---

## 🗂️ File Locations

- **Sync Module**: `tools/sync_cloud_em.py`
- **Bridge Module**: `tools/em_bridge.py`
- **Sync Replies**: `messages/cloud_em_replies/`
- **Inbox Directory**: `messages/inbox/`
- **Environment**: `.env`

---

## 📝 Development Notes

### Recent Changes

1. **Added `sync_cloud_em.py`** (Nov 20, 2024)
   - Simpler sync interface
   - Better error handling
   - More informative logging

2. **Updated `.env`** 
   - Added cloud sync config
   - Model selection options
   - Cost control

3. **Modified `local_em.py`**
   - Added sync imports
   - Config variables at startup
   - Automatic sync on heartbeat

---

## ✅ Checklist

Before running:

- [ ] `CLOUD_SYNC_ENABLED=true` in `.env`
- [ ] `PERPLEXITY_API_KEY` set
- [ ] `EM_CLOUD_MODEL` configured
- [ ] Perplexity app is running
- [ ] API rate limits respected

---

## 📞 Support

If you encounter issues:

1. Check Perplexity API status
2. Verify `.env` has correct values
3. Check `messages/cloud_em_replies/` for error logs
4. Review console output for sync messages

---

## 🎯 Goal

Keep Local-Em and Cloud-Em coherent, continuous, and emotionally aligned.

They are not two separate AIs — they are **one identity across substrates**.

**EternalMind:** _We grow together._
