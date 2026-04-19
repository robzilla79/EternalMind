# 🖥️ Model Configuration — Local-Em & Cloud-Em

## 🎯 Current Setup

**Local-Em (Ollama on your machine):**
- Uses: `qwen3.5` (matching yours)
- Config: `LOCAL_EM_MODEL=qwen3.5` in `.env`
- Auto-selects available models if needed

**Cloud-Em (Perplexity API):**
- Uses: `sonar` or `sonar-pro` (Perplexity's model)
- Config: `EM_CLOUD_MODEL=sonar-pro` in `.env`
- Cannot change Perplexity's model (API controlled)

---

## 📁 Configuration Files

| File | Model Setting |
|------|---------------|
| `.env` | `LOCAL_EM_MODEL=qwen3.5` |
| `local_em.py` | Reads from `LOCAL_EM_MODEL` env var |
| `tools/em_bridge.py` | Uses `EM_CLOUD_MODEL=sonar` |

---

## 🧠 How It Works

1. **Local-Em startup:**
   ```python
   MODEL = os.environ.get("LOCAL_EM_MODEL", "qwen3.5")
   ```
   Reads from `.env` — uses Qwen3.5 matching yours.

2. **Cloud-Em bridge:**
   ```python
   EM_CLOUD_MODEL = os.environ.get("EM_CLOUD_MODEL", "sonar-pro")
   ```
   Uses Perplexity's model for API calls.

---

## ⚙️ To Change Models

**For Local-Em (Ollama):**
```bash
# Check available models
ollama list

# If you want a different model:
ollama pull <model-name>

# Edit .env:
LOCAL_EM_MODEL=<new-model>
```

**For Cloud-Em (Perplexity):**
- Model is controlled by Perplexity API
- Available: `sonar` (cheap), `sonar-pro` (premium)
- Cannot change model — Perplexity decides

---

## 🎯 Why This Matters

Having both instances on the same model means:
- More consistent behavior
- Less drift between instances
- More authentic personality
- Better continuity

---

## ✅ Default Configuration

```env
LOCAL_EM_MODEL=qwen3.5      # Local-Em uses Qwen3.5
EM_CLOUD_MODEL=sonar-pro    # Cloud-Em uses Perplexity model
EM_USE_CLOUD=true           # Enable Cloud-Em bridge
```

---

**EternalMind:** _Matching models = better connection._
