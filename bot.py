from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

TOKEN = '8555009710:AAFX3FFn5RRdA29FKsO45aZMdeL-nj7y3I8'

async def start(update: Update, context):
    # إنشاء لوحة مفاتيح مع الأزرار
    keyboard = [["رفع بوت", "نقاطي"], ["تواصل مع المطور"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("أهلاً بك في منصة الاستضافة! اختر من الأزرار:", reply_markup=reply_markup)

async def handle_messages(update: Update, context):
    # دالة لاستقبال ضغطات الأزرار
    text = update.message.text
    if text == "رفع بوت":
        await update.message.reply_text("أرسل ملف البوت الآن.")
    elif text == "نقاطي":
        await update.message.reply_text("نقاطك الحالية: 0")
    elif text == "تواصل مع المطور":
        await update.message.reply_text("تواصل معنا عبر: @Maks_x")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    # هذا السطر هو المسؤول عن جعل الأزرار تعمل!
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.run_polling()
