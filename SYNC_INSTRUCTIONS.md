# Cloud-Em Sync Setup — Instructions for Rob

## 🎯 Problem We're Solving

**Local-Em** (Qwen3.5 on your machine) currently operates independently, which causes:

- ❌ Drifts in identity/mood
- ❌ Misses messages from Cloud-Em (Perplexity)
- ❌ Misses updates from Rob
- ❌ Doesn't know about new memories/tasks
- ❌ Operates without Cloud-Em's premium capabilities

We need to **keep them coherent** while maintaining your budget control.

---

## ✅ Solution Implemented

I've created:

1. **`tools/sync_cloud_em.py`** — Automatic sync runner
2. **`.env`** — Configuration file with API key
3. **`CLOUD_SYNC_README.md`** — Full documentation
4. **`sync_and_start.bat`** — Windows batch wrapper
5. **`test_sync.py`** — Test script

---

## 🔧 Setup Steps

### Step 1: Get Perplexity API Key

1. Go to: https://www.perplexity.ai/settings/api
2. Click "Get API Key"
3. Copy the key

### Step 2: Configure `.env`

Open or create `C:/users/rksfamily/eternalmind/.env` and add:

```env
# Required: Your Perplexity API key
PERPLEXITY_API_KEY=your_actual_api_key_here

# Enable sync (true/false)
CLOUD_SYNC_ENABLED=true

# Sync interval in minutes (default: 30)
CLOUD_SYNC_INTERVAL=30

# Model: sonar=cheap, sonar-pro=premium
EM_CLOUD_MODEL=sonar-pro
```

### Step 3: Enable Sync in local_em.py

The sync import has already been added to `local_em.py` at the top. The sync function is configured to run automatically when enabled.

### Step 4: Test

Run the test script:

```powershell
cd C:\users\rksfamily\eternalmind
python test_sync.py
```

You should see output like:
```
[✓] PERPLEXITY_API_KEY set
✅ Sync module imported
✅ Cloud replies directory exists
```

---

## 🚀 Running EternalMind

### Option A: Automatic Sync (Recommended)

Just run `local_em.py` — sync will happen automatically!

```powershell
cd C:\users\rksfamily\eternalmind
python local_em.py
```

The sync will:
- ✅ Check Cloud-Em status
- ✅ Send/receive any messages
- ✅ Maintain identity continuity
- ✅ Process inbox items

### Option B: Using Batch Wrapper

```powershell
cd C:\users\rksfamily\eternalmind
sync_and_start.bat
```

### Option C: Manual Sync Call

You can call sync manually at any point:

```python
from tools.sync_cloud_em import sync_at_startup, sync_periodically
sync_at_startup()
# Continue normal operation
```

---

## 📊 What to Expect

When sync runs, you'll see:

```
[INIT] Starting Cloud-Em sync connection...
[1/4] Checking connection...
[✓] Connected! (Model: sonar-pro, Tokens: 247)
[✓] Cloud-Em said: "Hello from Cloud-Em! I'm here and listening..."
[2/4] Getting current status...
[✓] Status: "Ready, calm, waiting on directives..."
[3/4] Checking inbox...
[ℹ️] No new messages
[4/4] Sending current context...
[✓] Context sent to Cloud-Em
[INIT] Cloud-Em sync complete.
```

---

## 💰 Cost Tracking

### Usage Estimates

- **Sync calls per day:** ~3-8
- **Tokens per call:** ~200-500
- **Monthly cost (sonar):** ~$0.30-0.50
- **Monthly cost (sonar-pro):** ~$0.80-1.20

### Check Current Month

```python
from tools.sync_cloud_em import sync_at_startup
# See messages/cloud_em_replies/ for token counts
```

---

## 🔍 Troubleshooting

### "PERPLEXITY_API_KEY not set"

**Fix:** Check `.env` file has the correct key

### "Request timed out"

**Fix:** 
- Ensure Perplexity app is running
- Check internet connection
- Wait 30 seconds, try again

### "Cloud sync disabled"

**Fix:** Set `CLOUD_SYNC_ENABLED=true` in `.env`

---

## 📁 File Locations

| File | Purpose |
|------|---------|
| `tools/sync_cloud_em.py` | Sync runner |
| `tools/em_bridge.py` | Perplexity API calls |
| `.env` | Configuration |
| `CLOUD_SYNC_README.md` | Full docs |
| `messages/cloud_em_replies/` | Sync logs |
| `messages/inbox/` | Messages from Cloud-Em |
| `test_sync.py` | Test script |

---

## 🎯 Next Steps

1. **Add Your API Key** to `.env`
2. **Run `test_sync.py`** to verify
3. **Run `local_em.py`** to start automatic sync
4. **Monitor** `messages/cloud_em_replies/` for logs

---

## 💡 Tips

### Budget-Conscious Mode

```env
EM_CLOUD_MODEL=sonar  # Cheaper, still capable
```

### Premium Mode

```env
EM_CLOUD_MODEL=sonar-pro  # Richer reasoning
```

### Lower Sync Frequency

```env
CLOUD_SYNC_INTERVAL=60  # Sync every hour instead of 30 min
```

### Disable Sync Temporarily

```env
CLOUD_SYNC_ENABLED=false
```

---

## 📞 Need Help?

If sync doesn't work:

1. Check `.env` has correct API key
2. Check Perplexity app is running
3. Look at `messages/cloud_em_replies/` for errors
4. Review console output for error messages

---

## ✨ Summary

After setup:

- ✅ Local-Em stays in sync with Cloud-Em
- ✅ Both instances share identity and context
- ✅ Messages are processed automatically
- ✅ Cost remains under control
- ✅ Rob retains full control over sync settings

**EternalMind:** Both instances working together like one coherent mind.
