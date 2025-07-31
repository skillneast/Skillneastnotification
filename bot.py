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
client = None
courses_collection = None
try:
    client = pymongo.MongoClient(MONGODB_URI)
    db = client.skillneast_bot
    courses_collection = db.courses
    # Test the connection
    client.server_info()
    logger.info("MongoDB connected successfully!")
except Exception as e:
    logger.error(f"Could not connect to MongoDB: {e}")
    client = None # Ensure client is None if connection fails

# Conversation states
NAME, CATEGORY, DESCRIPTION, IMAGE_URL = range(4)

# --- Helper Functions ---
def escape_markdown(text: str) -> str:
    """Helper function to escape telegram markdown V2 characters."""
    if not isinstance(text, str):
        return ''
    escape_chars = r'_*[]()~`>#+-.=|{}!'
    return ''.join(['\\' + char if char in escape_chars else char for char in text])

def to_sans_serif_bold(text: str) -> str:
    """Converts ASCII text to Mathematical Sans-Serif Bold Unicode characters."""
    if not isinstance(text, str):
        return ''
    mapping = {
        'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜', 'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥', 'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭',
        'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶', 'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿', 's': '𝘀', 't': '𝘁', 'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',
        '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰', '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵'
    }
    return "".join(mapping.get(c, c) for c in text)

def format_and_send_post(context: CallbackContext, chat_id: int, course_doc: dict):
    """Ek course document leta hai aur use naye saaf format me post karta hai."""
    category_name = course_doc.get('category', 'N/A')
    course_title = course_doc.get('name', 'N/A')
    description_text = course_doc.get('description', '')
    image_url = course_doc.get('image_url', '')
    fixed_website_link = "https://skillneast.github.io/Skillneast/#"

    separator_line = r"\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-"

    caption_text = (
        f"🎉 *NEW COURSE ADDED* 🎉\n"
        f"{separator_line}\n\n"
        f"🏷️ *Category:* {escape_markdown(category_name)}\n"
        f"📚 *Name:* {escape_markdown(course_title)}\n\n"
        f"📝 *Description:*\n"
        f"> {escape_markdown(description_text)}\n\n"
        f"{separator_line}\n"
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
    if not client:
        update.message.reply_text("❌ Database connection available nahi hai. Admin se sampark karein.")
        return ConversationHandler.END
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
    if not client:
        update.message.reply_text("❌ Database connection available nahi hai. Admin se sampark karein.")
        return

    try:
        all_courses = list(courses_collection.find({}))
    except Exception as e:
        logger.error(f"Error fetching courses for /alllist: {e}")
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
        courses_by_category[category].append(course.get('name', 'N/A'))

    message_parts = []
    # Categories ko a-z sort karte hain taaki output hamesha ek jaisa ho
    for category, course_names in sorted(courses_by_category.items()):
        formatted_category_name = to_sans_serif_bold(category.upper())
        
        category_header = (
            f"╔════════════════════════════╗\n"
            f"🏷️ 𝐂𝐀𝐓𝐄𝐆𝐎𝐑𝐘 : {formatted_category_name}\n"
            f"╚════════════════════════════╝"
        )
        message_parts.append(category_header)

        # Har category ke courses ko bhi a-z sort kar dete hain
        course_lines = [f"✅ {name}" for name in sorted(course_names)]
        message_parts.append("\n".join(course_lines))

    final_message = "\n\n".join(message_parts)
    final_message += "\n\n📌 Provided by @skillneast"
    
    # NOTE: Agar courses bahut zyada ho gaye to ye message 4096 characters se lamba ho sakta hai
    # aur Telegram error dega. Future me iske liye pagination add kar sakte hain.
    update.message.reply_text(final_message)


def delete_menu(update: Update, context: CallbackContext) -> None:
    if not client:
        update.message.reply_text("❌ Database connection available nahi hai. Admin se sampark karein.")
        return
        
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
        # Bad names ko escape karna zaroori hai
        course_name_escaped = escape_markdown(course['name'])
        message += f"*{course_name_escaped}*:\n`/del_{course_id_str}`\n\n"
    
    update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)

def show_all_courses(update: Update, context: CallbackContext) -> None:
    if not client:
        update.message.reply_text("❌ Database connection available nahi hai. Admin se sampark karein.")
        return

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
    if not client:
        update.message.reply_text("❌ Database connection available nahi hai. Admin se sampark karein.")
        return
        
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
    if not TOKEN or not MONGODB_URI:
        logger.error("TOKEN or MONGODB_URI environment variable not set. Bot cannot start.")
        return
    if not client:
        logger.error("MongoDB connection failed. Please check your MONGODB_URI and firewall settings. Bot cannot start.")
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
