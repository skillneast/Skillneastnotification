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
    db = client.skillneast_bot
    courses_collection = db.courses
    logger.info("MongoDB connected successfully!")
except Exception as e:
    logger.error(f"Could not connect to MongoDB: {e}")
    client = None

# Conversation states
NAME, CATEGORY, DESCRIPTION, IMAGE_URL = range(4)

# --- Helper Functions ---
def escape_markdown(text):
    """Helper function to escape telegram markdown characters"""
    escape_chars = r'_*[]()~`>#+-.=|{}!'
    return ''.join(['\\' + char if char in escape_chars else char for char in text])

def format_and_send_post(context: CallbackContext, chat_id: int, course_doc: dict):
    """Ek course document leta hai aur use naye saaf format me post karta hai."""
    category_name = course_doc.get('category', 'N/A')
    course_title = course_doc.get('name', 'N/A')
    description_text = course_doc.get('description', '')
    image_url = course_doc.get('image_url', '')
    fixed_website_link = "https://skillneast.github.io/Skillneast/#"

    # New, clean and stable format
    caption_text = (
        f"🎉 *NEW COURSE ADDED* 🎉\n"
        f"------------------------------------\n\n"
        f"🏷️ *Category:* {escape_markdown(category_name)}\n"
        f"📚 *Name:* {escape_markdown(course_title)}\n\n"
        f"📝 *Description:*\n"
        f"> {escape_markdown(description_text)}\n\n"
        f"------------------------------------\n"
        f"𖣐 *Provided By:* @skillneast"
    )

    keyboard = [[InlineKeyboardButton("🖥️ Visit Website 🖥️", url=fixed_website_link)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        context.bot.send_photo(
            chat_id=chat_id,
            photo=image_url,
            caption=caption_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Failed to send formatted post. Error: {e}")
        context.bot.send_message(chat_id=chat_id, text=f"Post banane me koi problem hui. Error: {e}")

# --- Bot Command Functions ---
def error_handler(update: object, context: CallbackContext) -> None:
    logger.error(f"Update {update} caused error {context.error}")

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Namaste! Aapke final bot me swagat hai.\n\n"
        "*/new_batch* - Naya course database me save karein.\n"
        "*/alllist* - Sabhi courses ki clean list dekhein.\n"
        "*/del* - Courses ko delete karne ke liye menu dekhein.\n"
        "*/show* - Sabhi courses ke full posts ek saath dekhein.",
        parse_mode=ParseMode.MARKDOWN
    )

# --- Conversation to Add New Course ---
def new_batch_start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Chaliye naya batch add karte hain! ✨\n\nSabse pehle, course ka Name kya hai?")
    return NAME

def get_name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text
    update.message.reply_text("Great! Ab course ki Category batao (e.g., Editing, Programming).")
    return CATEGORY

def get_category(update: Update, context: CallbackContext) -> int:
    context.user_data['category'] = update.message.text.strip().title()
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
        result = courses_collection.insert_one(course_doc)
        update.message.reply_text(f"✅ Course '{escape_markdown(user_data['name'])}' database me save ho gaya hai!", parse_mode=ParseMode.MARKDOWN_V2)
        
        newly_added_course = courses_collection.find_one({'_id': result.inserted_id})
        if newly_added_course:
            update.message.reply_text("*Yeh raha aapke naye course ka final post:*", parse_mode=ParseMode.MARKDOWN_V2)
            format_and_send_post(context, update.effective_chat.id, newly_added_course)

    except Exception as e:
        logger.error(f"Failed to save course to DB: {e}")
        update.message.reply_text("Database me save karte waqt koi problem hui.")

    user_data.clear()
    return ConversationHandler.END

# --- List, Show, and Delete Functions ---
def all_list(update: Update, context: CallbackContext) -> None:
    """Clean list dikhata hai (bina delete command ke)."""
    try:
        all_courses = list(courses_collection.find({}))
    except Exception as e:
        update.message.reply_text("Database se list laate waqt koi problem hui.")
        return

    if not all_courses:
        update.message.reply_text("Database me abhi tak koi course nahi hai.")
        return

    courses_by_category = {}
    for course in all_courses:
        category = course.get('category', 'Uncategorized')
        if category not in courses_by_category:
            courses_by_category[category] = []
        courses_by_category[category].append(course)

    message = "📚 *Here is a clean list of all courses:*\n\n"
    for category, courses in courses_by_category.items():
        message += f"✅ *{escape_markdown(category)}*\n"
        for course in courses:
            message += f"  - {escape_markdown(course['name'])}\n"
        message += "\n"
    
    update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)


def delete_menu(update: Update, context: CallbackContext) -> None:
    """Delete karne ke liye list dikhata hai."""
    try:
        all_courses = list(courses_collection.find({}))
    except Exception as e:
        update.message.reply_text("Database se list laate waqt koi problem hui.")
        return

    if not all_courses:
        update.message.reply_text("Delete karne ke liye koi course nahi hai.")
        return

    message = "🗑️ *Select a course to delete by clicking the command:*\n\n"
    for course in all_courses:
        course_id_str = str(course['_id'])
        message += f"*{escape_markdown(course['name'])}*:\n`/del_{course_id_str}`\n\n"
    
    update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)


def show_all_courses(update: Update, context: CallbackContext) -> None:
    """Sabhi courses ko full format me post karta hai."""
    try:
        all_courses = list(courses_collection.find({}))
        if not all_courses:
            update.message.reply_text("Database me post karne ke liye koi course nahi hai.")
            return

        update.message.reply_text(f"Total {len(all_courses)} courses hain. Unhe ek-ek karke post kar raha hoon...")
        for course in all_courses:
            format_and_send_post(context, update.effective_chat.id, course)
    
    except Exception as e:
        logger.error(f"Error showing all courses: {e}")
        update.message.reply_text("Courses dikhate waqt koi problem hui.")

def delete_command_handler(update: Update, context: CallbackContext) -> None:
    """Handles /del_<id> commands"""
    try:
        command_parts = update.message.text.split('_')
        if len(command_parts) != 2: return
        course_id_to_delete = command_parts[1]
        
        result = courses_collection.delete_one({'_id': ObjectId(course_id_to_delete)})
        
        if result.deleted_count > 0:
            update.message.reply_text("✅ Course database se successfully delete ho gaya hai.")
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
        logger.error("Env variables not set or DB connection failed. Bot cannot start.")
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
    dispatcher.add_handler(CommandHandler("del", delete_menu))
    dispatcher.add_handler(CommandHandler("show", show_all_courses))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^\/del_'), delete_command_handler))
    dispatcher.add_error_handler(error_handler)

    # Start the Bot
    logger.info("Starting bot on webhook...")
    updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN, webhook_url=f"https://{APP_NAME}/{TOKEN}")
    updater.idle()

if __name__ == '__main__':
    main()
