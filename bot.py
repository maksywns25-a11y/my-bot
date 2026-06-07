import json
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = '8555009710:AAE0Tccg6FqTqKt1XA9V-QN3W8Wy8FAOhYo'
ADMIN_ID = 6640098641
DB_FILE = "users_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    db = load_db()
    if user_id not in db:
        db[user_id] = {"status": "free", "uploads": 0, "date": str(datetime.now().date())}
        save_db(db)
    
    keyboard = [["رفع بوت", "نقاطي"], ["تواصل مع المطور"]]
    await update.message.reply_text("أهلاً بك في منصة الاستضافة!", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def handle_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    db = load_db()
    user_data = db.get(user_id, {"status": "free", "uploads": 0, "date": str(datetime.now().date())})
    
    if user_data["date"] != str(datetime.now().date()):
        user_data["uploads"] = 0
        user_data["date"] = str(datetime.now().date())
    
    if user_data["status"] == "free" and user_data["uploads"] >= 3:
        await update.message.reply_text("❌ لقد تجاوزت الحد اليومي (3 مرات). اشترك في الباقة المدفوعة!")
        return

    user_data["uploads"] += 1
    db[user_id] = user_data
    save_db(db)
    
    file = await update.message.document.get_file()
    await update.message.reply_text(f"✅ تم رفع البوت! (الاستخدام: {user_data['uploads']}/3)")
    await context.bot.send_document(chat_id=ADMIN_ID, document=file.file_id, caption=f"📥 بوت جديد من {user_id}")

async def set_pro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        if context.args:
            target_id = context.args[0]
            db = load_db()
            if target_id in db:
                db[target_id]["status"] = "pro"
                save_db(db)
                await update.message.reply_text(f"✅ تم تفعيل الباقة المدفوعة للمستخدم {target_id}")
            else:
                await update.message.reply_text("⚠️ المستخدم غير موجود في القاعدة.")
        else:
            await update.message.reply_text("استخدم الأمر هكذا: /set_pro [user_id]")

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_pro", set_pro))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_files))
    application.run_polling()
