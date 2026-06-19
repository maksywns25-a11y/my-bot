import asyncio
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# ================== بياناتك ==================
BOT_TOKEN = "8555009710:AAF92Rzeeb3YdnrdUyjIfay97ZKXZOcHv-A"  
ADMIN_ID = 6640098641
DEV_USERNAME = "@vc0_z"
CHANNEL_USERNAME = "@zaidmfj"
BOT_NAME = "𝐁𝐄𝐀𝐔𝐓𝐈𝐅𝐔𝐋"

# ================== تهيئة البوت ==================
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)

# ================== قاعدة البيانات ==================
conn = sqlite3.connect("beautiful_bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance REAL DEFAULT 0.0,
    daily_gift_date TEXT DEFAULT NULL,
    banned INTEGER DEFAULT 0,
    join_date TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS shortcuts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger_word TEXT UNIQUE,
    reply_text TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    service TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute("INSERT OR IGNORE INTO shortcuts (trigger_word, reply_text) VALUES (?, ?)",
               ("السلام عليكم", "وعليكم السلام ورحمة الله وبركاته 👋"))
conn.commit()

# ================== دوال مساعدة ==================
def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()

def create_user(user_id, full_name=""):
    cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

def update_balance(user_id, amount):
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()

def is_admin(user_id):
    return user_id == ADMIN_ID

def get_all_users():
    cursor.execute("SELECT user_id FROM users")
    return [row[0] for row in cursor.fetchall()]

def get_user_orders_count(user_id):
    cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id = ?", (user_id,))
    return cursor.fetchone()[0]

# ================== لوحات المفاتيح ==================
def user_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 تمويل القنوات", callback_data="fund")],
        [InlineKeyboardButton(text="🎁 الهدية اليومية", callback_data="daily")],
        [InlineKeyboardButton(text="💸 تحويل اموال", callback_data="transfer")],
        [InlineKeyboardButton(text="📊 سحب الأرباح", callback_data="withdraw")],
        [InlineKeyboardButton(text="📋 جميع طلباتي", callback_data="my_orders")],
        [InlineKeyboardButton(text="ℹ️ معلومات الحساب", callback_data="my_info")]
    ])

def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 إذاعة", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="⛔ حظر/فك حظر", callback_data="admin_ban")],
        [InlineKeyboardButton(text="📝 إدارة الاختصارات", callback_data="admin_shortcuts")],
        [InlineKeyboardButton(text="💳 تعديل الرصيد", callback_data="admin_balance")],
        [InlineKeyboardButton(text="📈 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🔙 العودة للمستخدم", callback_data="back_user")]
    ])

# ================== حالات FSM ==================
class BroadcastState(StatesGroup):
    waiting_for_content = State()

# ================== أوامر المستخدم ==================
@dp.message(Command("start"))
async def start_cmd(message: Message):
    user_id = message.from_user.id
    if not get_user(user_id):
        create_user(user_id)

    user = get_user(user_id)
    if user[3] == 1:
        await message.answer("🚫 أنت محظور من استخدام هذا البوت.")
        return

    text = (f"مرحباً بك عزيزي المستخدم في بوت {BOT_NAME}\n"
            f"─━─━─━─━─━─━─\n"
            f"💰 <b>رصيدك:</b> {user[1]} $\n"
            f"🆔 <b>ايديك:</b> {user_id}\n"
            f"📢 <b>قناة التحديثات:</b> {CHANNEL_USERNAME}\n"
            f"👨‍💻 <b>المطور:</b> {DEV_USERNAME}\n"
            f"─━─━─━─━─━─━─\n"
            f"⬇️ اختر الخدمة المطلوبة:")
    await message.answer(text, reply_markup=user_keyboard())

@dp.message(Command("transfer"))
async def transfer_cmd(message: Message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) != 3:
        await message.answer("❌ استخدم: /transfer ايدي_المستخدم المبلغ\nمثال: /transfer 123456 5")
        return
    try:
        target_id = int(args[1])
        amount = float(args[2])
        if amount <= 0:
            await message.answer("❌ المبلغ يجب أن يكون أكبر من صفر.")
            return
        sender = get_user(user_id)
        if not sender or sender[3] == 1:
            await message.answer("❌ أنت محظور أو غير مسجل.")
            return
        if sender[1] < amount:
            await message.answer(f"❌ رصيدك غير كافٍ. رصيدك الحالي: {sender[1]}$")
            return
        if not get_user(target_id):
            await message.answer("❌ المستخدم المستقبل غير موجود في قاعدة البيانات.")
            return
        update_balance(user_id, -amount)
        update_balance(target_id, amount)
        await message.answer(f"✅ تم تحويل {amount}$ إلى المستخدم {target_id} بنجاح.")
        try:
            await bot.send_message(target_id, f"💰 استلمت تحويلاً بقيمة {amount}$ من المستخدم {user_id}.")
        except:
            pass
        await bot.send_message(ADMIN_ID, f"💸 تحويل مالي\nمن: {user_id}\nإلى: {target_id}\nالمبلغ: {amount}$")
    except ValueError:
        await message.answer("❌ تأكد من كتابة الأرقام بشكل صحيح.")

@dp.callback_query(F.data == "back_user")
async def back_user(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    text = f"💰 <b>رصيدك:</b> {user[1]} $\n⬇️ اختر الخدمة:"
    await callback.message.edit_text(text, reply_markup=user_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "my_info")
async def my_info(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    text = (f"ℹ️ <b>معلومات حسابك</b>\n"
            f"🆔 ID: {callback.from_user.id}\n"
            f"💰 الرصيد: {user[1]} $\n"
            f"📅 آخر هدية: {user[2] if user[2] else 'لم تأخذ هدية'}\n"
            f"📋 عدد طلباتك: {get_user_orders_count(callback.from_user.id)}")
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_user")]
    ]))

@dp.callback_query(F.data == "daily")
async def daily_gift(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    today = datetime.now().date().isoformat()
    if user[2] == today:
        await callback.answer("🎁 لقد أخذت هديتك اليوم بالفعل!", show_alert=True)
        return
    update_balance(callback.from_user.id, 1.0)
    cursor.execute("UPDATE users SET daily_gift_date = ? WHERE user_id = ?", (today, callback.from_user.id))
    conn.commit()
    await callback.answer("🎁 تم إضافة 1$", show_alert=True)
    await callback.message.edit_text(f"✅ تمت العملية.\n💰 رصيدك: {get_user(callback.from_user.id)[1]} $")
    await asyncio.sleep(1.5)
    await back_user(callback)

@dp.callback_query(F.data == "fund")
async def fund_channels(callback: CallbackQuery):
    await callback.message.edit_text("🔜 <b>خدمة تمويل القنوات</b>\nقريباً سيتم تفعيلها.\nللطلب المباشر تواصل مع الأدمن.",
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                         [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_user")]
                                     ]))

@dp.callback_query(F.data == "transfer")
async def transfer_info(callback: CallbackQuery):
    await callback.message.edit_text("💸 <b>تحويل اموال</b>\nأرسل:\n<code>/transfer ايدي_المستقبل المبلغ</code>",
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                         [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_user")]
                                     ]))

@dp.callback_query(F.data == "withdraw")
async def withdraw_money(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    current_balance = user[1]
    
    if current_balance < 10:
        await callback.answer("❌ الحد الأدنى للسحب 10$", show_alert=True)
        return
        
    # خصم كامل الرصيد من الحساب فوراً لمنع التكرار والنصب
    update_balance(callback.from_user.id, -current_balance)
    
    await callback.message.edit_text(f"📤 <b>تم تسجيل طلب السحب بنجاح</b>\n💰 المبلغ المخصوم: {current_balance} $\n📝 أرسل محفظتك (USDT/فودافون كاش) في رسالة نصية ليتم التحويل لك من قبل الإدارة.",
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                         [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_user")]
                                     ]))
                                     
    await bot.send_message(ADMIN_ID, f"📤 <b>طلب سحب جديد (تم خصمه تلقائياً)</b>\n👤 من العضو: {callback.from_user.id}\n💰 المبلغ: {current_balance}$")

@dp.callback_query(F.data == "my_orders")
async def my_orders(callback: CallbackQuery):
    cursor.execute("SELECT id, service, status, created_at FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 10", (callback.from_user.id,))
    orders = cursor.fetchall()
    if not orders:
        await callback.answer("📭 لا توجد طلبات.", show_alert=True)
        return
    text = "📋 <b>آخر طلباتك</b>:\n" + "\n".join([f"#{o[0]} - {o[1]} - {o[2]} - {o[3]}" for o in orders])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_user")]
    ]))

# ================== لوحة الأدمن ==================
@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("🚫 مخصص للأدمن.")
        return
    await message.answer("🛠 <b>لوحة التحكم</b>", reply_markup=admin_keyboard())

@dp.message(Command("userinfo"))
async def user_info_command(message: Message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) != 2:
        await message.answer("❌ استخدم: /userinfo ايدي_المستخدم")
        return
    try:
        target_id = int(args[1])
    except:
        await message.answer("❌ يرجى إدخال الأيدي الرقمي.")
        return
    
    user = get_user(target_id)
    if not user:
        await message.answer(f"❌ المستخدم {target_id} غير موجود في قاعدة البيانات.")
        return
    
    orders_count = get_user_orders_count(target_id)
    status = "🚫 محظور" if user[3] == 1 else "✅ نشط"
    text = (f"👤 <b>معلومات العضو</b>\n"
            f"🆔 <b>أيدي العضو:</b> <code>{target_id}</code>\n"
            f"📊 <b>الحالة:</b> {status}\n"
            f"💰 <b>الرصيد:</b> {user[1]} $\n"
            f"🎁 <b>آخر هدية:</b> {user[2] if user[2] else 'لم يحصل'}\n"
            f"📋 <b>عدد الطلبات:</b> {orders_count}\n"
            f"📅 <b>تاريخ التسجيل:</b> {user[4] if user[4] else 'غير معروف'}")
    await message.answer(text)

# ================== معالجة النصوص وحل التعارض ==================
@dp.message(F.text)
async def handle_user_text_messages(message: Message):
    if message.text.startswith("/"):
        return
        
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if not user or user[3] == 1:
        return

    # 1. فحص الاختصارات (الردود التلقائية) أولاً
    cursor.execute("SELECT reply_text FROM shortcuts WHERE trigger_word = ?", (message.text.strip(),))
    row = cursor.fetchone()
    if row:
        await message.reply(row[0])
        return  

    # 2. تحويل الرسالة للأدمن إذا لم تكن اختصاراً (وتجاهل رسائل الأدمن لنفسه)
    if user_id == ADMIN_ID:
        return

    username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد يوزر"
    forward_text = (f"📩 <b>رسالة جديدة من عضو</b>\n"
                    f"👤 الاسم: {message.from_user.full_name}\n"
                    f"🆔 الأيدي: <code>{user_id}</code>\n"
                    f"👑 اليوزر: {username}\n"
                    f"💰 رصيده: {user[1]} $\n"
                    f"📝 النص:\n\"{message.text}\"")
    
    await bot.send_message(ADMIN_ID, forward_text)

# ================== معالجات أزرار الأدمن ==================
@dp.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await state.set_state(BroadcastState.waiting_for_content)
    await callback.message.edit_text("📢 أرسل الرسالة (نص/صورة/ملف) للإذاعة.\nلإلغاء: /cancel",
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                         [InlineKeyboardButton(text="🔙 إلغاء", callback_data="back_admin")]
                                     ]))

@dp.message(BroadcastState.waiting_for_content, F.text | F.photo | F.document)
async def send_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    users = get_all_users()
    if not users:
        await message.answer("⚠️ لا يوجد مستخدمين.")
        await state.clear()
        return
    await message.answer(f"📤 جاري الإرسال إلى {len(users)} مستخدم...")
    success = 0
    for uid in users:
        try:
            if message.text:
                await bot.send_message(uid, f"📢 <b>إذاعة</b>\n\n{message.text}")
            elif message.photo:
                await bot.send_photo(uid, message.photo[-1].file_id, caption=message.caption or "📢 إذاعة")
            elif message.document:
                await bot.send_document(uid, message.document.file_id, caption=message.caption or "📢 إذاعة")
            success += 1
        except:
            pass
        await asyncio.sleep(0.05)
    await message.answer(f"✅ تم الإرسال إلى {success} مستخدم.")
    await state.clear()

@dp.message(Command("cancel"))
async def cancel_broadcast(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ تم الإلغاء.")

@dp.callback_query(F.data == "back_admin")
async def back_admin(callback: CallbackQuery):
    await callback.message.edit_text("🛠 <b>لوحة التحكم</b>", reply_markup=admin_keyboard())

@dp.callback_query(F.data == "admin_ban")
async def admin_ban(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await callback.message.edit_text("⛔ <b>الحظر</b>\n<code>/ban ايدي</code>\n<code>/unban ايدي</code>",
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                         [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_admin")]
                                     ]))

@dp.callback_query(F.data == "admin_shortcuts")
async def admin_shortcuts(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await callback.message.edit_text("📝 <b>اختصارات</b>\n<code>/add_short كلمة نص</code>\n<code>/del_short كلمة</code>\n<code>/list_short</code>",
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                         [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_admin")]
                                     ]))

@dp.callback_query(F.data == "admin_balance")
async def admin_balance(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await callback.message.edit_text("💳 <b>تعديل الرصيد</b>\n<code>/add_balance ايدي المبلغ</code>",
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                         [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_admin")]
                                     ]))

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id): return
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(balance) FROM users")
    total_balance = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]
    await callback.message.edit_text(f"📈 <b>إحصائيات</b>\n👥 المستخدمين: {total_users}\n💰 الأرصدة: {total_balance}$\n📋 الطلبات: {total_orders}",
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                         [InlineKeyboardButton(text="🔙 رجوع", callback_data="back_admin")]
                                     ]))

# ================== أوامر الأدمن النصية ==================
@dp.message(Command("ban"))
async def ban_user(message: Message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) != 2:
        await message.answer("❌ استخدم: /ban ايدي")
        return
    try:
        uid = int(args[1])
        cursor.execute("UPDATE users SET banned = 1 WHERE user_id = ?", (uid,))
        conn.commit()
        await message.answer(f"✅ تم حظر {uid}")
    except:
        await message.answer("❌ خطأ.")

@dp.message(Command("unban"))
async def unban_user(message: Message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) != 2:
        await message.answer("❌ استخدم: /unban ايدي")
        return
    try:
        uid = int(args[1])
        cursor.execute("UPDATE users SET banned = 0 WHERE user_id = ?", (uid,))
        conn.commit()
        await message.answer(f"✅ تم فك الحظر عن {uid}")
    except:
        await message.answer("❌ خطأ.")

@dp.message(Command("add_balance"))
async def add_balance(message: Message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) != 3:
        await message.answer("❌ استخدم: /add_balance ايدي المبلغ")
        return
    try:
        uid = int(args[1])
        amount = float(args[2])
        update_balance(uid, amount)
        await message.answer(f"✅ تم تعديل رصيد {uid} بـ {amount}$. الجديد: {get_user(uid)[1]}$")
    except:
        await message.answer("❌ خطأ.")

@dp.message(Command("add_short"))
async def add_short(message: Message):
    if not is_admin(message.from_user.id): return
    parts = message.text.split(" ", 2)
    if len(parts) < 3:
        await message.answer("❌ استخدم: /add_short كلمة نص_الرد")
        return
    _, trigger, reply = parts
    cursor.execute("INSERT OR REPLACE INTO shortcuts (trigger_word, reply_text) VALUES (?, ?)", (trigger, reply))
    conn.commit()
    await message.answer(f"✅ تم إضافة {trigger}")

@dp.message(Command("del_short"))
async def del_short(message: Message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) != 2:
        await message.answer("❌ استخدم: /del_short كلمة")
        return
    cursor.execute("DELETE FROM shortcuts WHERE trigger_word = ?", (args[1],))
    conn.commit()
    await message.answer(f"✅ تم حذف {args[1]}")

@dp.message(Command("list_short"))
async def list_short(message: Message):
    if not is_admin(message.from_user.id): return
    cursor.execute("SELECT trigger_word, reply_text FROM shortcuts")
    rows = cursor.fetchall()
    if not rows:
        await message.answer("📝 لا توجد اختصارات.")
        return
    text = "📝 الاختصارات:\n" + "\n".join([f"- {r[0]} -> {r[1][:20]}..." for r in rows])
    await message.answer(text)

# ================== ترحيب الأعضاء الجدد مع إشعار للأدمن ==================
@dp.message(F.new_chat_members)
async def welcome_new_member(message: Message):
    for member in message.new_chat_members:
        if member.id == bot.id:
            continue
        if not get_user(member.id):
            create_user(member.id)
        
        welcome_text = (f"🌟 أهلاً وسهلاً بك {member.full_name} في مجموعة {BOT_NAME}!\n"
                        f"📢 اكتب /start لتفعيل حسابك.")
        await message.answer(welcome_text)
        
        username = f"@{member.username}" if member.username else "لا يوجد يوزر"
        admin_notify = (f"🆕 <b>عضو جديد دخل المجموعة</b>\n"
                        f"👤 الاسم: {member.full_name}\n"
                        f"👑 اليوزر: {username}\n"
                        f"🆔 الأيدي: <code>{member.id}</code>\n"
                        f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        await bot.send_message(ADMIN_ID, admin_notify)

# ================== التشغيل ==================
async def main():
    print(f"✅ Bot {BOT_NAME} is running perfectly...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())