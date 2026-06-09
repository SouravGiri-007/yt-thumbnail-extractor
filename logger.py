import os
import html
from dotenv import load_dotenv

load_dotenv()
LOG_GROUP_ID = os.getenv("LOG_GROUP_ID")

def log_user_message(bot, message):
    """Logs the user's incoming message to the group."""
    if not LOG_GROUP_ID:
        return
    
    text = message.text or message.caption or "(No text)"
    username = f"@{message.from_user.username}" if message.from_user.username else "N/A"
    
    log_text = (
        f"📥 <b>Incoming Message</b>\n\n"
        f"👤 <b>User:</b> {html.escape(message.from_user.first_name)}\n"
        f"🤖 <b>Username:</b> {username}\n"
        f"🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n"
        f"💬 <b>Text:</b> <code>{html.escape(text)}</code>"
    )
    try:
        bot.send_message(LOG_GROUP_ID, log_text, parse_mode="HTML")
    except Exception as e:
        print(f"Logging error: {e}")

def log_bot_reply(bot, message, video_id=None, video_title=None, thumbnail_bytes=None):
    """Logs the bot's reply/action to the group. Sends thumbnail if provided."""
    if not LOG_GROUP_ID:
        return
    
    username = f"@{message.from_user.username}" if message.from_user.username else "N/A"
    action = "Sent Thumbnail 🖼️" if thumbnail_bytes else "Sent Text 📝"
    
    log_text = (
        f"📤 <b>Bot Action</b>\n\n"
        f"🆔 <b>To User:</b> <code>{message.from_user.id}</code> | {username}\n"
        f"🤖 <b>Action:</b> {action}\n"
    )
    
    if video_id:
        log_text += f"🔗 <b>Link:</b> <code>https://youtu.be/{video_id}</code>\n"
        
    if video_title:
        log_text += f"🎬 <b>Title:</b> {html.escape(str(video_title))}"
        
    try:
        # If there's a thumbnail, send it as a photo with the log text as caption
        if thumbnail_bytes:
            bot.send_photo(
                chat_id=LOG_GROUP_ID, 
                photo=thumbnail_bytes, 
                caption=log_text, 
                parse_mode="HTML"
            )
        else:
            bot.send_message(LOG_GROUP_ID, log_text, parse_mode="HTML")
    except Exception as e:
        print(f"Logging error: {e}")