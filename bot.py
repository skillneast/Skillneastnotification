import hmac, hashlib, random, string, logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# === CONFIG (SECRETS ARE HARDCODED - NOT SAFE!) ===
# DANGER: Yeh secrets public ho sakte hain agar code GitHub par hai.
BOT_TOKEN = "8326586625:AAGA9NX8XB7ZnXqvM2-ANOO9TYfLsZeAgvQ"
SECRET_KEY = "STUDYERA2025"

# Public config
CHANNELS = [
    ("@skillneastreal", "https://t.me/skillneastreal"),
    ("@skillneast", "https://t.me/skillneast")
]
OWNER_LINK = "https://t.me/neasthub"
SITE_LINK = "https://skillneastauth.vercel.app/"

# === LOGGING ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

# === TOKEN GENERATOR ===
def generate_token():
    now = datetime.now()
    base = now.strftime('%a').upper()[:3] + "-" + now.strftime('%d') + now.strftime('%b').upper()
    digest = hmac.new(SECRET_KEY.encode(), base.encode(), hashlib.sha256).hexdigest().upper()
    prefix = digest[:8]
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}/{suffix}"

# === START HANDLER ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logging.info(f"User {user_id} started the bot.")
    
    joined_all, _ = await check_all_channels(context, user_id)

    if joined_all:
        await send_token(update, context)
    else:
        keyboard = [[InlineKeyboardButton(f"📥 Join {name[1:]}", url=url)] for name, url in CHANNELS]
        keyboard.append([
            InlineKeyboardButton("✅ I Joined", callback_data="check"),
            InlineKeyboardButton("👑 Owner", url=OWNER_LINK)
        ])

        await update.message.reply_text(
            "<b>🚀 Welcome to StudyEra!</b>\n\n"
            "📚 Free Educational Resources — Notes, PYQs, Live Batches, Test Series & more!\n\n"
            "🔐 Access is secured via channel membership.\n\n"
            "👉 Please join the below channels to unlock your daily access token 👇",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# === VERIFY BUTTON HANDLER ===
async def check_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    logging.info(f"User {user_id} clicked the check button.")

    joined_all, not_joined = await check_all_channels(context, user_id)

    if joined_all:
        await query.edit_message_text("✅ Channels verified!\n⏳ Generating your access token...", parse_mode="HTML")
        await send_token(query, context, edit=True)
    else:
        not_joined_list = "\n".join([f"🔸 {ch[1:]}" for ch, _ in not_joined])
        keyboard = [
            [InlineKeyboardButton("🔁 Retry", callback_data="check")],
            [InlineKeyboardButton("👑 Owner Profile", url=OWNER_LINK)]
        ]

        await query.edit_message_text(
            f"❌ You still haven’t joined:\n\n<code>{not_joined_list}</code>\n\n"
            "📛 Access will be revoked if you leave any channel.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# === CHECK MEMBERSHIP ===
async def check_all_channels(context, user_id):
    not_joined = []
    for username, url in CHANNELS:
        try:
            member = await context.bot.get_chat_member(username, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_joined.append((username, url))
        except Exception as e:
            logging.warning(f"Error checking {username} for user {user_id}: {e}")
            not_joined.append((username, url))
    return len(not_joined) == 0, not_joined

# === SEND TOKEN ===
async def send_token(obj, context, edit=False):
    token = generate_token()
    keyboard = [
        [InlineKeyboardButton("🔐 Access Website", url=SITE_LINK)],
        [InlineKeyboardButton("👑 Owner", url=OWNER_LINK)]
    ]
    text = (
        "<b>🎉 Access Granted!</b>\n\n"
        "Here is your <u>one-time token</u> for today:\n\n"
        f"<code>{token}</code>\n\n"
        "✅ Paste this on the website to continue!\n"
        "⚠️ Note: If you leave any channel later, your access will be revoked automatically."
    )

    try:
        if edit:
            await obj.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await obj.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        logging.info(f"Token sent to user {obj.effective_user.id}")
    except Exception as e:
        logging.error(f"Failed to send token: {e}")

# === ERROR HANDLER ===
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Update {update} caused error {context.error}")

# === RUN THE BOT ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_channels, pattern="^check$"))
    app.add_error_handler(error_handler)
    
    logging.info("Starting bot...")
    app.run_polling()

if __name__ == "__main__":
    main()
