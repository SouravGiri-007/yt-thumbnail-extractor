# 🎬 YT Thumbnail Grabber

Send a YouTube link, get the thumbnail. That's it.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file:
```env
BOT_TOKEN=your_bot_token
ADMIN_ID=your_telegram_id
LOG_GROUP_ID=your_log_group_id  # optional
```

```bash
python bot.py
```

> Get your `BOT_TOKEN` from [@BotFather](https://t.me/BotFather)

## Features
- 🖼️ Grabs highest quality thumbnail available
- 🔗 Supports `watch`, `shorts`, `live`, `youtu.be` links
- 📬 Non-link messages get forwarded to admin

---
Made by [Shane](https://github.com/SouravGiri-007)
