from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask
import threading, os, time, requests, shutil

# ======================================
# 🔑 Yaha apna Bot Token bharna hai (BotFather se mila tha)
BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"

# 🔑 Yaha apna Render URL bharna hai (jaise: https://1st-rename-bot.onrender.com/)
RENDER_URL = "PASTE_YOUR_RENDER_URL_HERE"
# ======================================

# Flask fake server (Render ke liye)
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Bot is alive 🚀"

def run_flask():
    flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

# Global thumbnail storage
THUMBNAIL_PATH = "thumbnail.jpg"

# ========== BOT HANDLERS ==========

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! Yeh rename bot chal raha hai.\n\n"
        "➡️ Koi file bhejo, main tumse naya naam puchunga.\n"
        "➡️ Koi image bhejo, main use thumbnail ke liye save kar lunga.\n"
        "➡️ Thumbnail dekhne ke liye /viewthum use karo."
    )

# Save thumbnail from images
async def save_thumbnail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]  # highest quality
    file = await context.bot.get_file(photo.file_id)
    await file.download_to_drive(THUMBNAIL_PATH)
    await update.message.reply_text("✅ Thumbnail save ho gaya hai!")

# View thumbnail
async def view_thumbnail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if os.path.exists(THUMBNAIL_PATH):
        await update.message.reply_photo(photo=InputFile(THUMBNAIL_PATH), caption="📌 Yeh tumhara current thumbnail hai.")
    else:
        await update.message.reply_text("⚠️ Tumne abhi tak koi thumbnail set nahi kiya hai.")

# Handle documents/videos
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_msg = update.message
    file_name = file_msg.document.file_name if file_msg.document else file_msg.video.file_name

    await update.message.reply_text(
        f"📂 File mili: {file_name}\n\n"
        "➡️ Reply karke naya naam bhejo (example: `newfile.mp4`)."
    )

# Rename after reply
async def rename_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Pehle ek file par reply karo.")
        return

    file_msg = update.message.reply_to_message

    if not (file_msg.document or file_msg.video):
        await update.message.reply_text("❌ Sirf documents/videos supported hain.")
        return

    new_name = update.message.text.strip()
    if not new_name:
        await update.message.reply_text("❌ Naya naam likho. Example: `newfile.pdf`")
        return

    # File download
    file = await file_msg.document.get_file() if file_msg.document else await file_msg.video.get_file()
    downloaded_path = await file.download_to_drive(custom_path=new_name)

    # Send back file
    if os.path.exists(THUMBNAIL_PATH):
        await update.message.reply_document(
            document=InputFile(downloaded_path),
            caption=f"✅ File renamed to: {new_name}",
            thumb=InputFile(THUMBNAIL_PATH)
        )
    else:
        await update.message.reply_document(
            document=InputFile(downloaded_path),
            caption=f"✅ File renamed to: {new_name}"
        )

    # Clean up local file
    os.remove(downloaded_path)

# ========== SELF PING (Keep Alive) ==========
def keep_alive():
    while True:
        try:
            requests.get(RENDER_URL)
            print("Pinged self to stay awake 🚀")
        except Exception as e:
            print("Ping failed:", e)
        time.sleep(600)  # har 10 min me ping karega

# ========== MAIN ==========
def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("viewthum", view_thumbnail))
    app.add_handler(MessageHandler(filters.PHOTO, save_thumbnail))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.VIDEO, handle_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, rename_file))

    app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()   # Flask server
    threading.Thread(target=keep_alive).start()  # Self-ping system
    run_bot()