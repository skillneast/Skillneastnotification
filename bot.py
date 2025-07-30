import logging
import os
import json
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

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Environment Variables & Constants ---
TOKEN = os.environ.get("TOKEN")
APP_NAME = os.environ.get("APP_NAME")
PORT = int(os.environ.get("PORT", "8443"))

# Render Persistent Disk par database file ka path
DATA_FILE_PATH = "/data/courses.json"

# Conversation states
NAME, CATEGORY, DESCRIPTION, IMAGE_URL = range(4)

# --- Database Functions ---
def load_data():
    """JSON file se data load karta hai."""
    try:
        with open(DATA_FILE_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Agar file nahi hai ya khali hai, to empty dictionary return karo
        return {}

def save_data(data):
    """Data ko JSON file me save karta hai."""
    with open(DATA_FILE_PATH, 'w') as f:
        json.dump(data, f, indent=4)

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
    context.user_data['category'] = update.message.text.strip()
    update.message.reply_text("Okay. Ab course ka Description likho.")
    return DESCRIPTION

def get_description(update: Update, context: CallbackContext) -> int:
    context.user_data['description'] = update.message.text
    update.message.reply_text("Description save ho gaya hai. Ab course ke poster ka Image URL bhejo.")
    return IMAGE_URL

def add_course_and_finish(update: Update, context: CallbackContext) -> int:
    """Course ko database me add karta hai aur conversation khatm karta hai."""
    user_data = context.user_data
    user_data['image_url'] = update.message.text
    
    # Data load karo
    all_courses = load_data()

    # Nayi course details
    category = user_data['category']
    course_info = {
        "name": user_data['name'],
        "description": user_data['description'],
        "image_url": user_data['image_url']
    }

    # Category ke andar course ko add karo
    if category in all_courses:
        all_courses[category].append(course_info)
    else:
        all_courses[category] = [course_info]
    
    # Data save karo
    save_data(all_courses)

    update.message.reply_text(
        f"✅ Course '{user_data['name']}' successfully list me save ho gaya hai!\n"
        "List dekhne ke liye /alllist command bhejein."
    )
    
    user_data.clear()
    return ConversationHandler.END

def all_list(update: Update, context: CallbackContext) -> None:
    """Sabhi saved courses ko category-wise list karta hai."""
    all_courses = load_data()
    if not all_courses:
        update.message.reply_text("Abhi tak koi course save nahi hua hai.")
        return

    message = "📖 *Here is the list of all saved courses:*\n\n"
    for category, courses in all_courses.items():
        message += f"✅ *{category.upper()}*\n"
        for i, course in enumerate(courses):
            # Callback data me category aur index (position) save karenge
            callback_data = f"delete_{category}_{i}"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑️ Delete", callback_data=callback_data)]
            ])
            # Course ka preview bhejenge
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Batch: {course['name']}",
                reply_markup=keyboard
            )
    update.message.reply_text("--- End of List ---")


def delete_handler(update: Update, context: CallbackContext) -> None:
    """Delete button ke callback ko handle karta hai."""
    query = update.callback_query
    query.answer()

    # 'delete_CategoryName_index' se details nikalo
    parts = query.data.split('_')
    action = parts[0]
    category_to_delete = parts[1]
    index_to_delete = int(parts[2])

    all_courses = load_data()

    if category_to_delete in all_courses and len(all_courses[category_to_delete]) > index_to_delete:
        # Course ko delete karo
        deleted_course = all_courses[category_to_delete].pop(index_to_delete)
        # Agar category khali ho jaye to use bhi delete kar do
        if not all_courses[category_to_delete]:
            del all_courses[category_to_delete]
        
        save_data(all_courses)
        query.edit_message_text(text=f"✅ Course '{deleted_course['name']}' has been deleted.")
    else:
        query.edit_message_text(text="Error: Course not found or already deleted.")

# Preview command (User ko naye format me message dikhane ke liye)
def preview(update: Update, context: CallbackContext) -> None:
    # Yeh command sirf demo ke liye hai, aap isse apne hisab se use kar sakte hain
    # Asli data new_batch se aayega
    category_name = "𝙲𝙰𝚃𝙴𝙶𝙾𝚁𝚈–𝙽𝙰𝙼𝙴"
    course_title = "𝙲𝙾𝚄𝚁𝚂𝙴–𝚃𝙸𝚃𝙻𝙴"
    description_text = "🔥 *“🧠 𝙔𝙀𝙃 𝙀𝙇𝙄𝙏𝙀 𝘽𝘼𝙏𝘾𝙃 𝙏𝙐𝙈𝙃𝙀 𝙀𝙓𝙋𝙀𝙍𝙏–𝙇𝙀𝙑𝙀𝙇 𝙎𝙆𝙄𝙇𝙇𝙎 𝘿𝙀𝙉𝙀 𝙒𝘼𝙇𝘼 𝙃𝘼𝙄!”*"
    image_url = "https://i.imgur.com/example.png" # Example Image URL
    fixed_website_link = "https://skillneast.github.io/Skillneast/#"

    # Naya fancy message format
    caption_text = f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    🎉 𝗡𝗘𝗪 𝗕𝗔𝗧𝗖𝗛 𝗔𝗟𝗘𝗥𝗧! 🚀✨
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

╭────────❖ 𝗖𝗢𝗨𝗥𝗦𝗘 𝗜𝗡𝗙𝗢 ❖────────╮
🏷️ 𝗖𝗔𝗧𝗘𝗚𝗢𝗥𝗬 : {category_name}
📚 𝗡𝗔𝗠𝗘       : {course_title}
╰────────────────────────────────╯

📝 𝗗𝗘𝗦𝗖𝗥𝗜𝗣𝗧𝗜𝗢𝗡:
> {description_text}

✿━━━━━━━━━━━━━━━━━━━━━━━━━━━━✿
𖣐 𝗣𝗥𝗢𝗩𝗜𝗗𝗘𝗗 𝗕𝗬: [@skillneast⚝]
"""
    keyboard = [[InlineKeyboardButton("🖥️ Visit Now 🖥️", url=fixed_website_link)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=image_url,
        caption=caption_text,
        parse_mode=ParseMode.MARKDOWN_V2 # Markdown V2 for quote '>'
    )


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Theek hai, process cancel kar diya gaya hai.')
    context.user_data.clear()
    return ConversationHandler.END


def main() -> None:
    if not TOKEN:
        logger.error("No TOKEN found.")
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
    
    # Command Handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler("alllist", all_list))
    dispatcher.add_handler(CommandHandler("preview", preview)) # Preview command

    # Callback Query Handler for delete button
    dispatcher.add_handler(CallbackQueryHandler(delete_handler, pattern='^delete_'))
    
    # Error Handler
    dispatcher.add_error_handler(error_handler)

    # Start the Bot
    logger.info("Starting bot on webhook...")
    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=TOKEN,
                          webhook_url=f"https://{APP_NAME}/{TOKEN}")
    updater.idle()

if __name__ == '__main__':
    main()
