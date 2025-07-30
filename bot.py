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
    CallbackQueryHandler,
)
import pymongo
from bson.objectid import ObjectId

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Environment Variables & Constants ---
TOKEN = os.environ.get("TOKEN")
APP_NAME = os.environ.get("APP_NAME")
PORT = int(os.environ.get("PORT", "8443"))
MONGODB_URI = os.environ.get("MONGODB_URI")

# --- MongoDB Connection ---
try:
    client = pymongo.MongoClient(MONGODB_URI)
    db = client.skillneast_bot # Database ka naam
    courses_collection = db.courses # Collection ka naam
    logger.info("MongoDB connected successfully!")
except Exception as e:
    logger.error(f"Could not connect to MongoDB: {e}")
    client = None

# Conversation states
NAME, CATEGORY, DESCRIPTION, IMAGE_URL = range(4)

# --- Bot Functions ---
def error_handler(update: object, context: CallbackContext) -> None:
    logger.error(f"Update {update} caused error {context.error}")

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Namaste! Naya course add karne ke liye /new_batch use karein.\n"
        "Sabhi saved courses dekhne ke liye /alllist use karein."
    )

def new_batch_start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Chaliye naya batch add karte hain! ✨\n\nSabse pehle, course ka Name kya hai?")
    return NAME

def get_name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text
    update.message.reply_text("Great! Ab course ki Category batao (e.g., Editing, Programming).")
    return CATEGORY

def get_category(update: Update, context: CallbackContext) -> int:
    context.user_data['category'] = update.message.text.strip().title() # Title case me save hoga
    update.message.reply_text("Okay. Ab course ka Description likho.")
    return DESCRIPTION

def get_description(update: Update, context: CallbackContext) -> int:
    context.user_data['description'] = update.message.text
    update.message.reply_text("Description save ho gaya hai. Ab course ke poster ka Image URL bhejo.")
    return IMAGE_URL

def add_course_and_finish(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    user_data['image_url'] = update.message.text
    
    course_doc = {
        "category": user_data['category'],
        "name": user_data['name'],
        "description": user_data['description'],
        "image_url": user_data['image_url']
    }
    
    try:
        courses_collection.insert_one(course_doc)
        update.message.reply_text(f"✅ Course '{user_data['name']}' successfully database me save ho gaya hai!")
    except Exception as e:
        logger.error(f"Failed to save course to DB: {e}")
        update.message.reply_text("Database me save karte waqt koi problem hui.")

    user_data.clear()
    return ConversationHandler.END

def all_list(update: Update, context: CallbackContext) -> None:
    try:
        all_courses = list(courses_collection.find({}))
    except Exception as e:
        logger.error(f"Failed to fetch courses from DB: {e}")
        update.message.reply_text("Database se list laate waqt koi problem hui.")
        return

    if not all_courses:
        update.message.reply_text("Database me abhi tak koi course nahi hai.")
        return

    # Courses ko category se group karo
    courses_by_category = {}
    for course in all_courses:
        category = course.get('category', 'Uncategorized')
        if category not in courses_by_category:
            courses_by_category[category] = []
        courses_by_category[category].append(course)

    message = "📖 *Here is the list of all courses:*\n\n"
    for category, courses in courses_by_category.items():
        message += f"✅ *{category.upper()}*\n"
        for course in courses:
            # MongoDB ki unique ID ko string me convert karo
            course_id_str = str(course['_id'])
            message += f"    - {course['name']}  [/del_{course_id_str}]\n"
    
    update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

def delete_command_handler(update: Update, context: CallbackContext) -> None:
    """Handles /del_<id> commands"""
    try:
        # Command se ID nikalo, e.g., /del_60b8d2...
        command_parts = update.message.text.split('_')
        if len(command_parts) != 2:
            update.message.reply_text("Invalid delete format. Use the format from /alllist.")
            return

        course_id_to_delete = command_parts[1]
        
        result = courses_collection.delete_one({'_id': ObjectId(course_id_to_delete)})
        
        if result.deleted_count > 0:
            update.message.reply_text("✅ Course successfully delete ho gaya hai.")
        else:
            update.message.reply_text("❌ Course nahi mila. Shayad pehle hi delete ho chuka hai.")
    
    except Exception as e:
        logger.error(f"Error deleting course: {e}")
        update.message.reply_text("Course delete karte waqt koi problem hui.")


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Theek hai, process cancel kar diya gaya hai.')
    context.user_data.clear()
    return ConversationHandler.END

def main() -> None:
    if not TOKEN or not MONGODB_URI or not client:
        logger.error("Environment variables not set or DB connection failed. Bot cannot start.")
        return

    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('new_batch', new_batch_start)],
        states={
            NAME: [MessageHandler(Filters.text & ~Filters.command, get_name)],
            CATEGORY: [MessageHandler(Filters.text & ~Filters.command, get_category)],
            DESCRIPTION: [MessageHandler(Filters.text & ~Filters.command, get_description)],
            IMAGE_URL: [MessageHandler(Filters.text & ~Filters.command, add_course_and_finish)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler("alllist", all_list))
    # Delete command handler: /del_... se shuru hone wale commands ko pakdega
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^\/del_'), delete_command_handler))
    dispatcher.add_error_handler(error_handler)

    # Start the Bot
    logger.info("Starting bot on webhook...")
    updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN, webhook_url=f"https://{APP_NAME}/{TOKEN}")
    updater.idle()

if __name__ == '__main__':
    main()
