import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- البيانات الخاصة بك ---
TOKEN = "8539939791:AAHhXPoOxazUR9W88RjPX5_JUBz9TyBv4dY"
ADMIN_ID = 6640098641  # استبدل هذا الرقم بالـ ID الخاص بك (يمكنك معرفته من بوت @userinfobot)

# --- لوحة تحكم الأدمن ---
def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("إحصائيات", callback_data='stats')],
        [InlineKeyboardButton("رسالة للجميع", callback_data='broadcast')]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- أوامر البوت ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # إذا كنت أنت الأدمن، أظهر لوحة التحكم
    if user_id == ADMIN_ID:
        await update.message.reply_text("أهلاً بك يا أدمن! هذه لوحة تحكمك:", reply_markup=get_admin_keyboard())
    else:
        # للمستخدمين العاديين
        await update.message.reply_text("مرحباً بك في البوت الخاص بي!")

# --- التعامل مع الأزرار ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'stats':
        await query.edit_message_text("الإحصائيات: البوت يعمل بكفاءة على سيرفر Render.")
    elif query.data == 'broadcast':
        await query.edit_message_text("ميزة الرسالة للجميع قيد التطوير.")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("البوت يعمل الآن...")
    application.run_polling()
