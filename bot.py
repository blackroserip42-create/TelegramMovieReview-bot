import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

Thread(target=run_web_server, daemon=True).start()
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

# Load environment variables from the .env file
load_dotenv()

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
OWNER_ID = os.getenv("OWNER_ID")

# Channel Links Dictionary (Same links as before)
CHANNEL_LINKS = {
    "animation": "https://t.me/+-Sx15diaNcQ0YmFl",
    "hollywood": "https://t.me/+fMCcBbMhlxthNTc1",
    "bollywood": "https://t.me/+v5IwFg1nadk5MzQ1",
    "kdrama": "https://t.me/+YFpCfrtI6OAwOWNl",
    "horror": "https://t.me/+lrGhEqv8RVRkM2I1"
}

# --- STATES ---
TITLE, POSTER, REVIEW, COMMAND = range(4)

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != OWNER_ID:
        await update.message.reply_text("⛔ You are not authorized.")
        return ConversationHandler.END

    await update.message.reply_text("🎬 *Please enter the Movie Title:*", parse_mode="Markdown")
    return TITLE

# --- TITLE ---
async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    await update.message.reply_text("🖼️ *Please send the Movie Poster image:*", parse_mode="Markdown")
    return POSTER

# --- POSTER ---
async def get_poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ Please send an image.")
        return POSTER
    context.user_data['poster'] = update.message.photo[-1].file_id
    await update.message.reply_text("📝 *Please write the Movie Review:*", parse_mode="Markdown")
    return REVIEW

# --- REVIEW ---
async def get_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['review'] = update.message.text
    await update.message.reply_text("🔗 *Please send the Movie Link:*", parse_mode="Markdown")
    # We will ask for the channel command in the next step using a text filter
    return COMMAND

# --- MOVIE LINK & CHANNEL COMMAND ---
async def get_link_and_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Step 1: Store the link
    context.user_data['movie_link'] = update.message.text

    # Step 2: Ask for the command
    await update.message.reply_text(
        "📂 *Please type which channel link to tag by typing one of these commands:*\n\n"
        "/animation - Animation Channel\n"
        "/hollywood - Hollywood Channel\n"
        "/bollywood - Bollywood Channel\n"
        "/kdrama - Kdrama Channel\n"
        "/horror - Horror Channel",
        parse_mode="Markdown"
    )
    return COMMAND # Wait for the user to type a command

# --- FINALIZE ---
async def finalize_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.lower().replace("/", "") # Extract command
    channel_link = CHANNEL_LINKS.get(user_text)

    if not channel_link:
        await update.message.reply_text("❌ Invalid command. Please type /animation, /hollywood, /bollywood, /kdrama, or /horror.")
        return COMMAND # Ask them to try again

    # Retrieve data
    title = context.user_data['title']
    poster = context.user_data['poster']
    review = context.user_data['review']
    movie_link = context.user_data['movie_link']

    # Format the Message
    html_message = (
        f"<b>{title}</b>\n\n"
        f"<blockquote expandable>{review}</blockquote>\n\n"
        f"<b>Channel Link</b>\n"
        f"<a href=\"{channel_link}\">{channel_link}</a>\n\n"
        f"<b>Movie Link</b>\n"
        f"<a href=\"{movie_link}\">{movie_link}</a>\n\n"
        f"<b>Channel အရင်ဂျိုင်းပေးပါ</b>"
    )

    try:
        await context.bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=poster,
            caption=html_message,
            parse_mode="HTML"
        )
        await update.message.reply_text(f"✅ Post successfully published to the channel!\n\n*Title:* {title}", parse_mode="Markdown")
        return ConversationHandler.END
    except Exception as e:
        print(f"🚨 ERROR: {e}")
        await update.message.reply_text(f"❌ Error posting: {str(e)}")
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END

# --- MAIN ---
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            POSTER: [MessageHandler(filters.PHOTO, get_poster)],
            REVIEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_review)],
            COMMAND: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_link_and_command),
                CommandHandler(['animation', 'hollywood', 'bollywood', 'kdrama', 'horror'], finalize_post)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)
    print("✅ Bot (Command Version) is running successfully...")
    application.run_polling()

if __name__ == '__main__':
    main()
