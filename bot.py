import os
import asyncio
import hmac
import hashlib
import random
import string
import logging
from datetime import datetime
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.error import BadRequest

# === LOGGING SETUP ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === CONFIGURATION (Yeh sab Render ke Environment Variables se aayega) ===
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
CHANNEL_1_USERNAME = os.environ.get('CHANNEL_1_USERNAME')
CHANNEL_2_USERNAME = os.environ.get('CHANNEL_2_USERNAME')
OWNER_LINK = os.environ.get('OWNER_LINK')
SITE_LINK = os.environ.get('SITE_LINK')
SECRET_KEY = "SKILLNEAST_SECRET_2024" # Ise aise hi rehne dein

CHANNELS = [
    (f"@{CHANNEL_1_USERNAME}", f"https://t.me/{CHANNEL_1_USERNAME}"),
    (f"@{CHANNEL_2_USERNAME}", f"https://t.me/{CHANNEL_2_USERNAME}")
]

# === TOKEN GENERATOR ===
def generate_token():
    now = datetime.now()
    base = now.strftime('%a').upper()[:3] + "-" + now.strftime('%d') + now.strftime('%b').upper()
    digest = hmac.new(SECRET_KEY.encode(), base.encode(), hashlib.sha256).hexdigest().upper()
    prefix = digest[:8]
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}/{suffix}"

# === BOT LOGIC (HANDLERS) ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    joined_all, _ = await check_all_channels(context, user_id)

    if joined_all:
        await send_token(update.message, context)
    else:
        keyboard = [[InlineKeyboardButton(f"📥 Join {name}", url=url)] for name, url in CHANNELS]
        keyboard.append([
            InlineKeyboardButton("✅ I Joined", callback_data="check_join"),
            InlineKeyboardButton("👑 Owner", url=OWNER_LINK)
        ])
        start_message = (
            "🚀 *𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗦𝗸𝗶𝗹𝗹𝗻𝗲𝗮𝘀𝘁!*\n\n"
            "📚 *𝗚𝗲𝘁 𝗙𝗿𝗲𝗲 𝗔𝗰𝗰𝗲𝘀𝘀 𝘁𝗼 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗖𝗼𝗻𝘁𝗲𝗻𝘁* —\n"
            "*𝗖𝗼𝘂𝗿𝘀𝗲𝘀, 𝗣𝗗𝗙 𝗕𝗼𝗼𝗸𝘀, 𝗣𝗮𝗶𝗱 𝗧𝗶𝗽𝘀 & 𝗧𝗿𝗶𝗰𝗸𝘀, 𝗦𝗸𝗶𝗹𝗹-𝗕𝗮𝘀𝗲𝗱 𝗠𝗮𝘁𝗲𝗿𝗶𝗮𝗹 & 𝗠𝗼𝗿𝗲!*\n\n"
            "🧠 *𝗠𝗮𝘀𝘁𝗲𝗿 𝗡𝗲𝘄 𝗦𝗸𝗶𝗹𝗹𝘀 & 𝗟𝗲𝗮𝗿𝗻 𝗪𝗵𝗮𝘁 𝗥𝗲𝗮𝗹𝗹𝘆 𝗠𝗮𝘁𝘁𝗲𝗿𝘀* — *𝟭𝟬𝟬% 𝗙𝗥𝗘𝗘!*\n\n"
            "💸 *𝗔𝗹𝗹 𝗧𝗼𝗽 𝗖𝗿𝗲𝗮𝘁𝗼𝗿𝘀' 𝗣𝗮𝗶𝗱 𝗖𝗼𝘂𝗿𝘀𝗲𝘀 𝗮𝘁 𝗡𝗼 𝗖𝗼𝘀𝘁!*\n\n"
            "🔐 *𝗔𝗰𝗰𝗲𝘀𝘀 𝗶𝘀 𝘀𝗲𝗰𝘂𝗿𝗲𝗱 𝘃𝗶𝗮 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝗺𝗲𝗺𝗯𝗲𝗿𝘀𝗵𝗶𝗽.*\n\n"
            "👉 *𝗣𝗹𝗲𝗮𝘀𝗲 𝗷𝗼𝗶𝗻 𝘁𝗵𝗲 𝗯𝗲𝗹𝗼𝘄 𝗰𝗵𝗮𝗻𝗻𝗲𝗹𝘀 𝘁𝗼 𝘂𝗻𝗹𝗼𝗰𝗸 𝘆𝗼𝘂𝗿 𝗱𝗮𝗶𝗹𝘆 𝗮𝗰𝗰𝗲𝘀𝘀 𝘁𝗼𝗸𝗲𝗻* 👇"
        )
        await update.message.reply_text(
            start_message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def check_join_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer("Checking membership...")

    joined_all, not_joined = await check_all_channels(context, user_id)

    if joined_all:
        await query.edit_message_text("✅ Verification successful! Here is your token:")
        await send_token(query, context, edit=True)
    else:
        not_joined_list = "\n".join([f"🔸 {ch[1:]}" for ch, _ in not_joined])
        keyboard = [[InlineKeyboardButton("🔁 Retry", callback_data="check_join")]]
        await query.edit_message_text(
            f"❌ **Verification Failed**\n\n"
            f"You haven't joined the following channel(s) yet:\n\n`{not_joined_list}`\n\n"
            "Please join all channels and then click 'Retry'.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def check_all_channels(context, user_id):
    not_joined = []
    for username, url in CHANNELS:
        try:
            member = await context.bot.get_chat_member(username, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_joined.append((username, url))
        except BadRequest as e:
            if "user not found" in e.message.lower():
                not_joined.append((username, url))
            else:
                logger.error(f"Error checking {username} for {user_id}: {e}")
                not_joined.append((username, url))
        except Exception as e:
            logger.error(f"Unexpected error checking {username} for {user_id}: {e}")
            not_joined.append((username, url))
    return len(not_joined) == 0, not_joined

async def send_token(obj, context, edit=False):
    token = generate_token()
    keyboard = [
        [InlineKeyboardButton("🔐 Access Website", url=SITE_LINK)],
        [InlineKeyboardButton("👑 Owner", url=OWNER_LINK)]
    ]
    text = (
        "🎉 *Access Granted!*\n\n"
        "Here is your _one-time token_ for today:\n\n"
        f"`{token}`\n\n"
        "✅ Paste this on the website to continue!\n"
        "⚠️ *Note: If you leave any channel later, your access will be revoked automatically.*"
    )
    if edit:
        await obj.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await obj.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# === FLASK & WEBHOOK SETUP ===
app = Flask(__name__)
ptb_app = Application.builder().token(BOT_TOKEN).build()
ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(CallbackQueryHandler(check_join_button, pattern="check_join"))

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
async def webhook():
    update_data = request.get_json()
    update = Update.de_json(update_data, ptb_app.bot)
    await ptb_app.process_update(update)
    return 'ok'

@app.route('/setwebhook')
async def set_webhook():
    if WEBHOOK_URL:
        await ptb_app.bot.set_webhook(f'{WEBHOOK_URL}/{BOT_TOKEN}')
        return "Webhook setup successful!"
    return "WEBHOOK_URL not set."

@app.route('/')
def index():
    return "I am alive!"
