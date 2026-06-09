# bot.py
import os
import html
import re
import requests
import telebot
import random 
from dotenv import load_dotenv
from logger import log_user_message, log_bot_reply
# ─── Load Environment ───────────────────────────────────────
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing! Add it to .env file")

bot = telebot.TeleBot(BOT_TOKEN)


# ─── YouTube URL Patterns ───────────────────────────────────
YOUTUBE_PATTERNS = [
    # Standard watch URL
    r'(?:https?://)?(?:www\.)?youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})',
    # Short URL
    r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
    # Embed URL
    r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
    # Shorts URL
    r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
    # Live URL
    r'(?:https?://)?(?:www\.)?youtube\.com/live/([a-zA-Z0-9_-]{11})',
]

# Thumbnail quality tiers (highest → lowest)
THUMBNAIL_TIERS = [
    ("maxresdefault", "Max Resolution (1920×1080)"),
    ("sddefault",     "Standard (640×480)"),
    ("hqdefault",     "High Quality (480×360)"),
    ("mqdefault",     "Medium Quality (320×180)"),
    ("default",       "Default (120×90)"),
]

# Cool reactions for when a link is pasted
REACTIONS = ['👍', '🔥', '😎', '🤩', '👀', '🍿', '✨', '💯', '🚀', '🎯', '💅', '🤌']

def extract_video_id(text: str) -> str | None:
    """Extract YouTube video ID from a text message."""
    for pattern in YOUTUBE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def get_best_thumbnail(video_id: str) -> tuple[bytes | None, str]:
    """
    Try each thumbnail quality tier from best to worst.
    Returns (image_bytes, quality_name) or (None, error_msg).
    """
    for quality, label in THUMBNAIL_TIERS:
        url = f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200 and len(response.content) > 1000:
                # Content > 1KB means it's a real image, not YouTube's
                # 404 placeholder (which is ~900 bytes)
                return response.content, label
        except requests.RequestException:
            continue

    return None, "No thumbnail found for this video."


def get_video_info(video_id: str) -> dict:
    """Fetch basic video info using oEmbed (no API key needed)."""
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except requests.RequestException:
        pass
    return {}


# ─── Bot Handlers ───────────────────────────────────────────

# ─── Welcome Message ────────────────────────────────────────
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    log_user_message(bot, message)
    
    # 👇 Put your direct image URL here (leave as "" if you don't want an image)
    WELCOME_IMAGE_URL = "https://ibb.co/Kj5s3CZ0" 
    
    welcome_text = (
        "🎬 **YT Thumbnail Grabber** ⚡\n\n"
        "Drop a YouTube link, get the highest quality thumbnail. Simple.\n\n"
        "▸ Supports `watch`, `shorts`, `live` & `embed` links\n"
        "▸ Always grabs 1080p first 🖼️\n\n"
        "🛠️ Made by [Shane](https://github.com/SouravGiri-007)\n\n"
        "_Send a link to try it out 👇_"
    )
    
    try:
        if WELCOME_IMAGE_URL: # If you added an image URL, send photo
            bot.send_photo(
                chat_id=message.chat.id,
                photo=WELCOME_IMAGE_URL,
                caption=welcome_text,
                parse_mode="Markdown"
            )
        else: # Otherwise, just send text
            bot.reply_to(message, welcome_text, parse_mode="Markdown")
    except Exception:
        bot.reply_to(message, welcome_text, parse_mode="Markdown")
    
        log_bot_reply(bot, message, video_title="Start/Help message")

# Make sure ADMIN_ID is loaded at the top of your bot.py file
ADMIN_ID = os.getenv("ADMIN_ID")

# ─── Handle all user messages ───────────────────────────────
@bot.message_handler(func=lambda message: message.chat.type == "private")
def handle_message(message):
    video_id = extract_video_id(message.text)

    # If YOU (the admin) send a message that is NOT a YouTube link, just ignore it
    if str(message.from_user.id) == ADMIN_ID and not video_id:
        return

    # ──────────────────────────────────────────────────────
    # 1. IF IT'S A YOUTUBE LINK -> FETCH THUMBNAIL
    
    # ──────────────────────────────────────────────────────
    if video_id:
        log_user_message(bot, message)

        # Random Reaction
        try:
            chosen_reaction = random.choice(REACTIONS)
            bot.set_message_reaction(
                chat_id=message.chat.id,
                message_id=message.message_id,
                reaction=[telebot.types.ReactionTypeEmoji(chosen_reaction)]
            )
        except Exception:
            pass 

        # Status Messages
        status_msg = bot.reply_to(message, "Fetching thumbnail... ⏳")

        thumbnail_bytes, quality_or_error = get_best_thumbnail(video_id)

        if not thumbnail_bytes:
            bot.edit_message_text("❌ Failed to fetch thumbnail.", chat_id=status_msg.chat.id, message_id=status_msg.message_id)
            log_bot_reply(bot, message, video_id=video_id, video_title=f"Failed: {quality_or_error}")
            return

        bot.edit_message_text("Sending... 📤", chat_id=status_msg.chat.id, message_id=status_msg.message_id)

        video_info = get_video_info(video_id)
        video_title = video_info.get("title", "Unknown Title")
        channel_name = video_info.get("author_name", "Unknown Channel")

        caption = (
            f"🖼️ **Thumbnail** — `{quality_or_error}`\n\n"
            f"🎬 **{video_title}**\n"
            f"📺 _{channel_name}_\n\n"
            f"🔗 [Watch on YouTube](https://youtu.be/{video_id})"
        )

        try:
            bot.send_photo(chat_id=message.chat.id, photo=thumbnail_bytes, caption=caption, parse_mode="Markdown")
        except telebot.apihelper.ApiException:
            bot.send_document(chat_id=message.chat.id, document=thumbnail_bytes, visible_file_name=f"{video_id}_thumbnail.jpg")

        bot.delete_message(chat_id=status_msg.chat.id, message_id=status_msg.message_id)
        log_bot_reply(bot, message, video_id=video_id, video_title=video_title, thumbnail_bytes=thumbnail_bytes)
        
        return # Stop here, don't run the Livegram code below

    # ──────────────────────────────────────────────────────
    # 2. IF IT'S NOT A YOUTUBE LINK -> DIY LIVEGRAM (Forward to you)
    # ──────────────────────────────────────────────────────
    log_user_message(bot, message)
    
    try:
        # Forward the user's message to you
        bot.forward_message(chat_id=ADMIN_ID, from_chat_id=message.chat.id, message_id=message.message_id)
        
        # Escape name to prevent parsing crashes (e.g., names with _ or .)
        safe_name = html.escape(message.from_user.first_name)
        safe_id = message.from_user.id
        
        # Send yourself a guide on how to reply (using HTML instead of Markdown)
        bot.send_message(
            ADMIN_ID, 
            f"↩️ <i>Reply to the message above to chat with</i> {safe_name} (<code>{safe_id}</code>)", 
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Forwarding error: {e}")

    


# ─── DIY LIVEGRAM: Send Admin's reply back to User ─────────
@bot.message_handler(func=lambda message: str(message.from_user.id) == ADMIN_ID and message.reply_to_message)
def handle_admin_reply(message):
    """When you reply to a forwarded message, it sends it back to the user."""
    if message.reply_to_message.forward_from:
        user_id = message.reply_to_message.forward_from.id
        try:
            bot.send_message(user_id, message.text)
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to send: {e}")
    else:
        bot.reply_to(message, "❌ Couldn't find the user. They might have privacy settings blocking this.")


# ─── Start the Bot ──────────────────────────────────────────
# ─── Start the Bot ──────────────────────────────────────────
if __name__ == "__main__":
    print("🤖 YouTube Thumbnail Bot is running...")
    bot.delete_webhook()   # ← This removes Livegram's webhook
    bot.infinity_polling()