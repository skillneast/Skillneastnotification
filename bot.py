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
# Render से Token और App Name लेने के लिए
TOKEN = os.environ.get("TOKEN")
APP_NAME = os.environ.get("APP_NAME")
PORT = int(os.environ.get("PORT", "8443"))

# Conversation states
NAME, CATEGORY, DESCRIPTION, IMAGE_URL, WEBSITE_LINK = range(5)

# /start command
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "नमस्ते! मैं आपके कोर्स पोस्ट बनाने में मदद करूँगा।\n"
        "नया कोर्स जोड़ने के लिए /new_batch कमांड का उपयोग करें।"
    )

# Command to start the conversation
def new_batch_start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("चलिए नया बैच जोड़ते हैं! ✨\n\nसबसे पहले, कोर्स का नाम क्या है?")
    return NAME

# Function to get course name
def get_name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text
    update.message.reply_text("बहुत बढ़िया! अब कोर्स की कैटेगरी बताएं।")
    return CATEGORY

# Function to get category
def get_category(update: Update, context: CallbackContext) -> int:
    context.user_data['category'] = update.message.text
    update.message.reply_text("ठीक है। अब कोर्स का विवरण (Description) लिखें।")
    return DESCRIPTION

# Function to get description
def get_description(update: Update, context: CallbackContext) -> int:
    context.user_data['description'] = update.message.text
    update.message.reply_text("विवरण सेव कर लिया गया है। अब कोर्स के पोस्टर का इमेज URL भेजें।")
    return IMAGE_URL

# Function to get image URL
def get_image_url(update: Update, context: CallbackContext) -> int:
    context.user_data['image_url'] = update.message.text
    update.message.reply_text("इमेज URL मिल गया। आखिर में, 'Visit Now' बटन के लिए अपनी वेबसाइट का लिंक भेजें।")
    return WEBSITE_LINK

# Function to create and send final post
def get_website_link_and_post(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    description_quoted = f"> {user_data['description']}"

    caption_text = (
        f"*{'New Batch Added 🥰 ✨'}*\n\n"
        f"*Category:* {user_data['category']}\n"
        f"*Course Name:* {user_data['name']}\n\n"
        f"*Description:*\n{description_quoted}\n\n"
        f"Provided by :- @skillneast"
    )

    keyboard = [
        [InlineKeyboardButton("🖥️ Visit Now 🖥️", url=user_data['website_link'])],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_photo(
        photo=user_data['image_url'],
        caption=caption_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup,
    )
    
    user_data.clear()
    return ConversationHandler.END

# Function to cancel the conversation
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('ठीक है, इस प्रक्रिया को रद्द कर दिया गया है।')
    context.user_data.clear()
    return ConversationHandler.END

def main() -> None:
    # Get the token from environment variables
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
            IMAGE_URL: [MessageHandler(Filters.text & ~Filters.command, get_image_url)],
            WEBSITE_LINK: [MessageHandler(Filters.text & ~Filters.command, get_website_link_and_post)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(conv_handler)

    # Start the Bot with Webhook for deployment
    logger.info("Starting bot on webhook...")
    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=TOKEN,
                          webhook_url=f"https://{APP_NAME}/{TOKEN}")
    updater.idle()

if __name__ == '__main__':
    main()
