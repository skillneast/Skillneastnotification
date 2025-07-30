import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Logging setup to see errors
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Environment Variables ---
TOKEN = os.environ.get("TOKEN")
APP_NAME = os.environ.get("APP_NAME")
PORT = int(os.environ.get("PORT", "8443"))

# Conversation states (Website link state hata diya gaya hai)
NAME, CATEGORY, DESCRIPTION, IMAGE_URL = range(4)

# Error handling function
def error_handler(update: object, context: CallbackContext) -> None:
    """Log Errors caused by Updates."""
    logger.error(f"Update {update} caused error {context.error}")

# /start command (Hinglish me)
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Namaste! Main aapke course post banane mein help karunga.\n"
        "Naya course add karne ke liye /new_batch command use karein."
    )

# Conversation shuru karne ka command
def new_batch_start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Chaliye naya batch add karte hain! ✨\n\nSabse pehle, course ka Name kya hai?")
    return NAME

# Name lene ka function
def get_name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text
    update.message.reply_text("Great! Ab course ki Category batao.")
    return CATEGORY

# Category lene ka function
def get_category(update: Update, context: CallbackContext) -> int:
    context.user_data['category'] = update.message.text
    update.message.reply_text("Okay. Ab course ka Description likho.")
    return DESCRIPTION

# Description lene ka function
def get_description(update: Update, context: CallbackContext) -> int:
    context.user_data['description'] = update.message.text
    update.message.reply_text("Description save ho gaya hai. Ab course ke poster ka Image URL bhejo.")
    return IMAGE_URL

# Image URL lene aur final post banane ka function
def get_image_url_and_post(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    user_data['image_url'] = update.message.text
    
    # Website link ab fix hai
    fixed_website_link = "https://skillneast.github.io/Skillneast/#"
    
    # Naya message format
    description_quoted = f"> {user_data['description']}"
    caption_text = (
        f"📌 *New Batch Added* 🥰✨\n\n"
        f"*{'Category'}:* {user_data['category']}\n"
        f"*{'Name'}:* {user_data['name']}\n\n"
        f"*{'Description'}:*\n{description_quoted}\n\n"
        f"Provided by :- @skillneast"
    )

    keyboard = [
        [InlineKeyboardButton("🖥️ Visit Now 🖥️", url=fixed_website_link)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        update.message.reply_photo(
            photo=user_data['image_url'],
            caption=caption_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup,
        )
    except Exception as e:
        logger.error(f"Failed to send photo. Error: {e}")
        update.message.reply_text(f"Photo bhejne me koi problem hui. Please check karein ki Image URL sahi hai. Error: {e}")

    user_data.clear()
    return ConversationHandler.END

# Cancel command
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Theek hai, process cancel kar diya gaya hai.')
    context.user_data.clear()
    return ConversationHandler.END

def main() -> None:
    if not TOKEN:
        logger.error("No TOKEN found. Please set it in environment variables.")
        return

    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('new_batch', new_batch_start)],
        states={
            NAME: [MessageHandler(Filters.text & ~Filters.command, get_name)],
            CATEGORY: [MessageHandler(Filters.text & ~Filters.command, get_category)],
            DESCRIPTION: [MessageHandler(Filters.text & ~Filters.command, get_description)],
            IMAGE_URL: [MessageHandler(Filters.text & ~Filters.command, get_image_url_and_post)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(conv_handler)
    dispatcher.add_error_handler(error_handler)

    logger.info("Starting bot on webhook...")
    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=TOKEN,
                          webhook_url=f"https://{APP_NAME}/{TOKEN}")
    updater.idle()

if __name__ == '__main__':
    main()
