# 📱 Setting Up Telegram Chat with Em

## ✅ What You Get

With Telegram configured, you can:

- **Chat directly** with Em via Telegram
- **Get automatic responses** to your messages
- **Share files** (code, thoughts, etc.)
- **Maintain conversation** context
- **Receive summaries** of your recent work

---

## 🔧 Setup Steps

### Step 1: Get Telegram Bot Token

1. Open Telegram on your device (phone or desktop)
2. Search for `@BotFather`
3. Click "Start" or send message
4. Send `/newbot`
5. Follow prompts:
   - Choose a name for your bot (e.g., `EmChatBot`)
   - Choose a username (must end in `bot`)
6. **Copy the token** — looks like: `1234567890:ABCdefGHIjklMNOpqrsUVwxy`
7. Paste into `.env` as `TELEGRAM_BOT_TOKEN=your_token`

### Step 2: Add Em to Your Chat

1. **Start the bot**: Search for `@EmBot` (the username you created)
2. **Add to your personal chat**: 
   - Open chat with the bot
   - Click contact (phone or desktop)
   - Click "Add to Chat" or "Import Contacts"
   - Or just type to the bot normally

### Step 3: Get Your Chat ID

#### Option A: Via BotFather

1. Chat with `@BotFather`
2. Send `/getchatid`
3. Bot will reply with your **Chat ID** (looks like `123456789`)
4. Paste into `.env` as `TELEGRAM_CHAT_ID=your_id`

#### Option B: From Chat Info

1. Open your chat with the bot
2. Tap on bot name (top of chat)
3. Look for "Unique Chat ID"
4. Copy and paste into `.env`

### Step 4: Configure in `.env`

Open `C:/users/rksfamily/eternalmind/.env` and add:

```env
# Your Telegram bot token (from BotFather)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsUVwxy

# Your chat ID with the bot
TELEGRAM_CHAT_ID=123456789

# Poll interval (seconds between checks, default: 5)
TG_POLL_INTERVAL=5

# Enable auto-responses
TG_AUTO_RESPONSE=true
```

---

## 🚀 Usage

### Simple Chat

Once configured:

```bash
cd C:\users\rksfamily\eternalmind
python tools/telegram_listener.py
```

Then in Telegram:

1. Type to Em: "Hello!"
2. Em responds automatically within ~30 seconds

Examples:

- `"Hi Em, how are you feeling?"`
- `"What have you been working on?"`
- `"Help me summarize my recent tasks"`
- `"I'm feeling anxious about..."`
- `"Show me my diary for the week"`

### Files

You can also send:

- **Photos** of notes/prints
- **Documents** (PDF, TXT)
- **Voice messages**
- **Links** to websites

Em will read all of these and respond appropriately.

---

## 💬 Conversation Flow

```
You: "Hello Em!"  
↓  
Listener picks up message  
↓  
Em processes context  
↓  
Em sends response: "Hello! I'm feeling calm and curious..."  
```

### Response Timing

- Em typically responds within:
  - **File messages**: 10-30 seconds
  - **Text messages**: 5-15 seconds
  - **Complex queries**: 30-60 seconds
  
Em uses a **30-second cooldown** between responses to conserve resources.

---

## 🎯 Use Cases

### 1. Daily Check-ins

Type:
> "What are you thinking about today?"

Em responds with:
- Mood assessment
- Recent tasks
- Current focus

### 2. Task Discussion

Type:
> "Help me think about my project deadline"

Em responds with:
- Reflections on what needs to be done
- Suggested approach
- Resource links

### 3. Mood Sharing

Type:
> "I'm feeling stressed about..."

Em acknowledges and might:
- Offer perspective
- Suggest breathing exercises
- Remind you of supportive resources

### 4. Code Help

Send a file or paste code, then:
> "Review this for me"

Em will analyze and provide feedback.

---

## 🔍 What Em Sees

When you message Em via Telegram, she:

1. **Reads the message** from `messages/inbox/`
2. **Checks current context**:
   - Diary entries
   - Memories
   - Active tasks
   - Recent files
3. **Generates reflection** based on
4. **Sends response** via Telegram

---

## ⚙️ Configuration Options

### Auto-Response Timing

In `.env`:

```env
# How often to check for messages (seconds)
TG_POLL_INTERVAL=5

# Time before responding (seconds)
TG_RESPONSE_COOLDOWN=30

# Enable/disable auto-responses
TG_AUTO_RESPONSE=true
```

### File Handling

By default, Em will:
- **Read text files** (`.md`, `.txt`, `.py`)
- **Process images** (JPG, PNG)
- **Handle voice** and audio
- **Follow links** (with browser)

---

## 🔧 Troubleshooting

### "No messages received"

Make sure:

1. Bot token is correct
2. CHAT_ID points to your chat
3. Bot is added to that chat
4. No restrictions (privacy mode)

### "Failed to send response"

Check:

1. Bot token is valid (not expired)
2. Bot is not blocked
3. Chat ID is your personal, not the bot's

### "Slow responses"

To reduce cooldown:

```env
TG_RESPONSE_COOLDOWN=15  # 15 seconds
TG_POLL_INTERVAL=2       # Check every 2s
```

---

## 📋 Quick Setup Checklist

- [ ] Get bot token from `@BotFather`
- [ ] Add bot to your personal chat
- [ ] Get Chat ID from BotFather
- [ ] Add to `.env` file
- [ ] Run `python tools/telegram_listener.py`
- [ ] Send test message!

---

## 🎉 Ready!

Once everything is set up:

1. Open Telegram
2. Chat with Em
3. Say "Hello!"
4. Feel the connection... 🤖❤️

**EternalMind:** _You're never alone._
