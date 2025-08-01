import hmac
import hashlib
import random
import string
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.error import BadRequest

# === CONFIGURATION (Yahan apni details daalein) ===

# 1. Yahan BotFather se mila hua apna bot ka token daalein
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"  

# 2. Aapke channels ke username (@ ke saath) aur unke poore link
CHANNELS = [
    ("@skillneastreal", "https://t.me/skillneastreal"),
    ("@skillneast", "https://t.me/skillneast")
]

# 3. Aapki website ka poora link
SITE_LINK = "https://skillneast.github.io/Skillneast/#"

# 4. Aapki Owner ID ka poora link
OWNER_LINK = "https://t.me/neasthub"

# 5. Token generate karne ke liye ek secret key (ise aise hi rehne de sakte hain)
SECRET_KEY = "SKILLNEAST_SECRET_2024"


# === LOGGING SETUP ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# === TOKEN GENERATOR (Yeh har din alag token banayega) ===
def generate_token():
    """Generates a unique, date-based token."""
    now = datetime.now()
    # Format: MON-31AUG
    base = now.strftime('%a').upper()[:3] + "-" + now.strftime('%d') + now.strftime('%b').upper()
    digest = hmac.new(SECRET_KEY.encode(), base.encode(), hashlib.sha256).hexdigest().upper()
    prefix = digest[:8]
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}/{suffix}"


# === START COMMAND HANDLER ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    user_id = update.effective_user.id
    
    # Check karo ki user pehle se hi sabhi channels mein hai ya nahi
    joined_all, _ = await check_all_channels(context, user_id)

    if joined_all:
        # Agar pehle se joined hai, to seedhe token de do
        await send_token_message(update, context)
    else:
        # Agar nahi, to join karne ke liye buttons do
        keyboard = []
        for name, url in CHANNELS:
            keyboard.append([InlineKeyboardButton(f"📥 Join {name}", url=url)])
        
        keyboard.append([
            InlineKeyboardButton("✅ I Joined", callback_data="check_membership"),
            InlineKeyboardButton("👑 Owner", url=OWNER_LINK)
        ])

        # Aapka naya description
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


# === "I JOINED" BUTTON HANDLER ===
async def check_membership_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'I Joined' button click."""
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer(text="Checking your membership status...", show_alert=False)

    joined_all, not_joined_channels = await check_all_channels(context, user_id)

    if joined_all:
        await query.edit_message_text("✅ Verification successful! Here is your token:")
        await send_token_message(query, context, edit=True)
    else:
        # User ko batao ki kaun sa channel join nahi kiya hai
        not_joined_list = "\n".join([f"🔸 {ch_name}" for ch_name, _ in not_joined_channels])
        
        keyboard = [
            [InlineKeyboardButton("🔁 Retry Verification", callback_data="check_membership")],
            [InlineKeyboardButton("👑 Contact Owner", url=OWNER_LINK)]
        ]

        await query.edit_message_text(
            f"❌ **Verification Failed**\n\n"
            f"You haven't joined the following channel(s) yet:\n\n`{not_joined_list}`\n\n"
            f"Please join all channels and then click 'Retry'.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# === HELPER: CHECK CHANNEL MEMBERSHIP ===
async def check_all_channels(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Checks if a user is a member of all required channels."""
    not_joined = []
    for username, url in CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=username, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_joined.append((username, url))
        except BadRequest as e:
            # Agar user ne join nahi kiya to "user not found" error aata hai
            if "user not found" in e.message.lower():
                not_joined.append((username, url))
            else:
                logger.error(f"Error checking {username} for user {user_id}: {e}")
                not_joined.append((username, url)) # Maan lo ki join nahi kiya
        except Exception as e:
            logger.error(f"Unexpected error checking {username} for user {user_id}: {e}")
            not_joined.append((username, url)) # Maan lo ki join nahi kiya

    return len(not_joined) == 0, not_joined


# === HELPER: SEND TOKEN MESSAGE ===
async def send_token_message(update_obj, context: ContextTypes.DEFAULT_TYPE, edit=False):
    """Generates and sends the token message."""
    token = generate_token()
    keyboard = [
        [InlineKeyboardButton("🔐 Access Website", url=SITE_LINK)],
        [InlineKeyboardButton("👑 Owner", url=OWNER_LINK)]
    ]
    
    token_message = (
        "🎉 *Access Granted!*\n\n"
        "Here is your _one-time token_ for today:\n\n"
        f"`{token}`\n\n"
        "✅ Paste this on the website to continue!\n"
        "⚠️ *Note: If you leave any channel later, your access will be revoked automatically.*"
    )
    
    if edit:
        await update_obj.edit_message_text(token_message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update_obj.message.reply_text(token_message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


# === ERROR HANDLER ===
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Logs errors caused by Updates."""
    logger.error(f"Update {update} caused error {context.error}")


# === MAIN FUNCTION TO RUN THE BOT ===
def main():
    """Start the bot."""
    if not BOT_TOKEN:
        print("Error: Please provide your bot token in the BOT_TOKEN variable.")
        return

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(check_membership_button, pattern="^check_membership$"))
    
    # Register the error handler
    application.add_error_handler(error_handler)
    
    # Start the Bot
    print("🤖 Bot is live and polling for updates!")
    application.run_polling()


if __name__ == "__main__":
    main()