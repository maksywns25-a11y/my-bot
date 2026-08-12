# Colored by 𝙾𝙳 (@vc0_z)
import logging
import sqlite3
import os
import random
import string
import aiohttp
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# ===================== الإعدادات =====================
BOT_TOKEN = "8737729245:AAE8K12iJqLIvxbaNMsiaYekfyH4RHjosqA"
ADMIN_ID = 6640098641
USER_ID = 6640098641
DB_PATH = "data/users.db"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# حالات المحادثة
WAITING_ADD_SECTION = 1
WAITING_ADD_SERVICE = 2
WAITING_ADD_SERVICE_SMM = 3
WAITING_ADD_CHANNEL_POINTS = 4
WAITING_ADD_FORCED_CHANNEL = 5
WAITING_ADD_SMM = 6
WAITING_ADD_ORDERS_CHANNEL = 7
WAITING_ADD_LOG_CHANNEL = 8
WAITING_SEARCH_USER = 9
WAITING_SERVICE_LINK = 10
WAITING_SELECT_SERVICE_SECTION = 11
WAITING_BROADCAST = 12
WAITING_FREE_SERVICE = 13
WAITING_WHEEL_PRIZE = 14
WAITING_QUICK_LINK = 15
WAITING_INVITE_LIMIT = 16
WAITING_INVITE_POINTS = 17
WAITING_CHANNEL_SETTINGS = 18
WAITING_BROADCAST_MESSAGE = 19
WAITING_TERMS = 20
WAITING_SELL_NUMBER = 21
WAITING_CHARGE_STARS = 22
WAITING_CHARGE_CASH = 23
WAITING_TRANSFER_ID = 24
WAITING_TRANSFER_AMOUNT = 25
WAITING_USE_CODE = 26
WAITING_ADD_BALANCE_ID = 27
WAITING_ADD_BALANCE_AMOUNT = 28
WAITING_REMOVE_BALANCE_ID = 29
WAITING_REMOVE_BALANCE_AMOUNT = 30
WAITING_SMM_ORDER_LINK = 31
WAITING_SERVICE_QUANTITY = 32
WAITING_SERVICE_LINK_ONLY = 33

# ===================== قاعدة البيانات =====================
def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS sections (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, icon TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS services (id INTEGER PRIMARY KEY AUTOINCREMENT, section_name TEXT, name TEXT, icon TEXT, price INTEGER DEFAULT 0, min_order INTEGER DEFAULT 1, max_order INTEGER DEFAULT 100, description TEXT, service_id TEXT, smm_site TEXT, is_free INTEGER DEFAULT 0, daily_limit INTEGER DEFAULT 0, is_store INTEGER DEFAULT 0, guarantee TEXT DEFAULT NULL, delivery_time TEXT DEFAULT NULL, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS points_channels (id INTEGER PRIMARY KEY AUTOINCREMENT, channel_id TEXT, name TEXT, link TEXT, points INTEGER DEFAULT 50, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS forced_channels (id INTEGER PRIMARY KEY AUTOINCREMENT, channel_id TEXT, name TEXT, link TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS smm_sites (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, api_url TEXT, api_key TEXT, is_active INTEGER DEFAULT 0, balance REAL DEFAULT 0, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders_channels (id INTEGER PRIMARY KEY AUTOINCREMENT, channel_id TEXT, name TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS log_channels (id INTEGER PRIMARY KEY AUTOINCREMENT, channel_id TEXT, name TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, balance INTEGER DEFAULT 0, joined_date TEXT, completed_orders INTEGER DEFAULT 0, daily_claimed TEXT DEFAULT NULL, referrer_id INTEGER DEFAULT NULL, accepted_terms INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, service_id INTEGER, service_name TEXT, link TEXT, quantity INTEGER DEFAULT 1, price INTEGER DEFAULT 0, smm_order_id TEXT DEFAULT NULL, status TEXT DEFAULT 'pending', created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, channel_id TEXT, channel_name TEXT, channel_link TEXT, points INTEGER DEFAULT 10, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS wheel_prizes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, points INTEGER, weight INTEGER DEFAULT 1, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS quick_links (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE, points INTEGER, max_uses INTEGER, used_count INTEGER DEFAULT 0, created_at TEXT, expires_at TEXT DEFAULT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS invite_codes (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE, points INTEGER, max_users INTEGER, used_count INTEGER DEFAULT 0, created_by INTEGER, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bot_settings (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT)''')
    
    columns_to_add = [
        ("users", "daily_claimed", "TEXT DEFAULT NULL"),
        ("users", "referrer_id", "INTEGER DEFAULT NULL"),
        ("users", "accepted_terms", "INTEGER DEFAULT 0"),
        ("services", "is_free", "INTEGER DEFAULT 0"),
        ("services", "daily_limit", "INTEGER DEFAULT 0"),
        ("services", "is_store", "INTEGER DEFAULT 0"),
        ("services", "guarantee", "TEXT DEFAULT NULL"),
        ("services", "delivery_time", "TEXT DEFAULT NULL"),
        ("smm_sites", "balance", "REAL DEFAULT 0"),
        ("orders", "price", "INTEGER DEFAULT 0"),
        ("orders", "smm_order_id", "TEXT DEFAULT NULL")
    ]
    
    for table, col_name, col_type in columns_to_add:
        try:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass
    
    default_prizes = [
        ("🟤 10 نقطة عادي", 10, 30),
        ("⚪ 25 نقطة جيد", 25, 20),
        ("🟢 50 نقطة ممتاز", 50, 15),
        ("🔵 100 نقطة رائع", 100, 10),
        ("🟡 200 نقطة كبير", 200, 6),
        ("🟠 500 نقطة ضخم", 500, 3),
        ("🔴 1000 نقطة جائزة كبرى", 1000, 1)
    ]
    
    for name, points, weight in default_prizes:
        try:
            c.execute("INSERT OR IGNORE INTO wheel_prizes (name, points, weight, created_at) VALUES (?, ?, ?, ?)",
                      (name, points, weight, datetime.now().isoformat()))
        except:
            pass
    
    conn.commit()
    conn.close()
    print("✅ قاعدة البيانات جاهزة!")

init_db()

# ===================== دوال SMM API =====================
async def smm_api_request(site_id, action, params):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT api_url, api_key FROM smm_sites WHERE id = ?", (site_id,))
    site = c.fetchone()
    conn.close()
    
    if not site:
        return None
    
    api_url = site[0]
    api_key = site[1]
    
    url = f"{api_url}{action}"
    params['key'] = api_key
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=params) as response:
                return await response.json()
    except:
        return None

async def smm_order(site_id, service_id, link, quantity):
    params = {
        'action': 'add',
        'service': service_id,
        'link': link,
        'quantity': quantity
    }
    return await smm_api_request(site_id, '', params)

# ===================== دوال قاعدة البيانات =====================
def add_section(name, icon):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("INSERT INTO sections (name, icon, created_at) VALUES (?, ?, ?)", (name, icon, now))
    conn.commit()
    conn.close()

def get_sections():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, icon FROM sections ORDER BY created_at DESC")
    sections = c.fetchall()
    conn.close()
    return sections

def add_service(section_name, name, icon, price, min_order, max_order, description, service_id=None, smm_site=None, is_free=0, daily_limit=0, is_store=0, guarantee=None, delivery_time=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("""INSERT INTO services 
                 (section_name, name, icon, price, min_order, max_order, description, service_id, smm_site, is_free, daily_limit, is_store, guarantee, delivery_time, created_at) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
              (section_name, name, icon, price, min_order, max_order, description, service_id, smm_site, is_free, daily_limit, is_store, guarantee, delivery_time, now))
    conn.commit()
    conn.close()

def get_services_by_section(section_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT id, name, icon, price, min_order, max_order, description, service_id, smm_site, is_free, daily_limit, is_store, guarantee, delivery_time FROM services WHERE section_name = ? ORDER BY created_at DESC", (section_name,))
        services = c.fetchall()
    except:
        services = []
    conn.close()
    return services

def get_store_services():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT id, name, icon, price, min_order, max_order, description, service_id, smm_site, is_free, daily_limit, guarantee, delivery_time FROM services WHERE is_store = 1 ORDER BY created_at DESC")
        services = c.fetchall()
    except:
        services = []
    conn.close()
    return services

def get_service_by_id(service_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, section_name, name, icon, price, min_order, max_order, description, service_id, smm_site, is_free, daily_limit, is_store, guarantee, delivery_time FROM services WHERE id = ?", (service_id,))
    service = c.fetchone()
    conn.close()
    return service

def add_points_channel(channel_id, name, link, points):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("INSERT INTO points_channels (channel_id, name, link, points, created_at) VALUES (?, ?, ?, ?, ?)", 
              (channel_id, name, link, points, now))
    conn.commit()
    conn.close()

def get_points_channels():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, channel_id, name, link, points FROM points_channels")
    channels = c.fetchall()
    conn.close()
    return channels

def add_forced_channel(channel_id, name, link):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("INSERT INTO forced_channels (channel_id, name, link, created_at) VALUES (?, ?, ?, ?)", 
              (channel_id, name, link, now))
    conn.commit()
    conn.close()

def get_forced_channels():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, channel_id, name, link FROM forced_channels")
    channels = c.fetchall()
    conn.close()
    return channels

def add_smm_site(name, api_url, api_key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("INSERT INTO smm_sites (name, api_url, api_key, created_at) VALUES (?, ?, ?, ?)", 
              (name, api_url, api_key, now))
    conn.commit()
    conn.close()

def get_smm_sites():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT id, name, api_url, api_key, is_active, balance FROM smm_sites")
        sites = c.fetchall()
    except:
        sites = []
    conn.close()
    return sites

def set_active_smm_site(site_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE smm_sites SET is_active = 0")
    c.execute("UPDATE smm_sites SET is_active = 1 WHERE id = ?", (site_id,))
    conn.commit()
    conn.close()

def get_active_smm_site():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT id, name, api_url, api_key FROM smm_sites WHERE is_active = 1")
        site = c.fetchone()
    except:
        site = None
    conn.close()
    return site

def add_orders_channel(channel_id, name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("INSERT INTO orders_channels (channel_id, name, created_at) VALUES (?, ?, ?)", 
              (channel_id, name, now))
    conn.commit()
    conn.close()

def get_orders_channels():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, channel_id, name FROM orders_channels")
    channels = c.fetchall()
    conn.close()
    return channels

def add_log_channel(channel_id, name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("INSERT INTO log_channels (channel_id, name, created_at) VALUES (?, ?, ?)", 
              (channel_id, name, now))
    conn.commit()
    conn.close()

def get_log_channels():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, channel_id, name FROM log_channels")
    channels = c.fetchall()
    conn.close()
    return channels

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def add_user(user_id, username, first_name, referrer_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, balance, joined_date, completed_orders, referrer_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, first_name, 0, now, 0, referrer_id))
    
    if referrer_id:
        c.execute("UPDATE users SET balance = balance + 50 WHERE user_id = ?", (referrer_id,))
    
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def update_balance(user_id, amount):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_completed_orders(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM orders WHERE user_id = ? AND status = 'completed'", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def get_all_users_count():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count

def get_all_orders_count():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM orders")
    count = c.fetchone()[0]
    conn.close()
    return count

def get_pending_orders_count():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
    count = c.fetchone()[0]
    conn.close()
    return count

def get_today_orders_count():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT COUNT(*) FROM orders WHERE date(created_at) = ?", (today,))
    count = c.fetchone()[0]
    conn.close()
    return count

def get_total_points_used():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT SUM(price) FROM orders WHERE status = 'completed'")
    result = c.fetchone()
    conn.close()
    return result[0] if result and result[0] else 0

def get_today_points_used():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT SUM(price) FROM orders WHERE status = 'completed' AND date(created_at) = ?", (today,))
    result = c.fetchone()
    conn.close()
    return result[0] if result and result[0] else 0

def get_total_referrals():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE referrer_id IS NOT NULL")
    count = c.fetchone()[0]
    conn.close()
    return count

def add_order(user_id, service_id, service_name, link, quantity, price, smm_order_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("INSERT INTO orders (user_id, service_id, service_name, link, quantity, price, smm_order_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (user_id, service_id, service_name, link, quantity, price, smm_order_id, now))
    conn.commit()
    conn.close()

def get_daily_claimed(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT daily_claimed FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def set_daily_claimed(user_id, date):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET daily_claimed = ? WHERE user_id = ?", (date, user_id))
    conn.commit()
    conn.close()

def add_task(channel_id, channel_name, channel_link, points):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute("INSERT INTO tasks (channel_id, channel_name, channel_link, points, created_at) VALUES (?, ?, ?, ?, ?)",
              (channel_id, channel_name, channel_link, points, now))
    conn.commit()
    conn.close()

def get_tasks():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, channel_id, channel_name, channel_link, points FROM tasks ORDER BY created_at DESC")
    tasks = c.fetchall()
    conn.close()
    return tasks

def get_accepted_terms(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT accepted_terms FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def set_accepted_terms(user_id, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET accepted_terms = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    conn.close()

def add_wheel_prize(name, points, weight):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO wheel_prizes (name, points, weight, created_at) VALUES (?, ?, ?, ?)",
              (name, points, weight, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_wheel_prizes():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, points, weight FROM wheel_prizes ORDER BY points ASC")
    prizes = c.fetchall()
    conn.close()
    return prizes

def delete_wheel_prize(prize_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM wheel_prizes WHERE id = ?", (prize_id,))
    conn.commit()
    conn.close()

def get_wheel_total_weight():
    prizes = get_wheel_prizes()
    return sum(p[3] for p in prizes) if prizes else 0

def spin_wheel():
    prizes = get_wheel_prizes()
    total_weight = get_wheel_total_weight()
    if total_weight == 0 or not prizes:
        return None
    
    rand = random.randint(1, total_weight)
    cumulative = 0
    for prize in prizes:
        cumulative += prize[3]
        if rand <= cumulative:
            return prize
    return None

def generate_random_code(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def add_quick_link(code, points, max_uses):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO quick_links (code, points, max_uses, created_at) VALUES (?, ?, ?, ?)",
              (code, points, max_uses, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_quick_link(code):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, points, max_uses, used_count FROM quick_links WHERE code = ?", (code,))
    link = c.fetchone()
    conn.close()
    return link

def use_quick_link(code):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE quick_links SET used_count = used_count + 1 WHERE code = ?", (code,))
    conn.commit()
    conn.close()

def add_invite_code(code, points, max_users, created_by):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO invite_codes (code, points, max_users, created_by, created_at) VALUES (?, ?, ?, ?, ?)",
              (code, points, max_users, created_by, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_invite_code(code):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, points, max_users, used_count FROM invite_codes WHERE code = ?", (code,))
    invite = c.fetchone()
    conn.close()
    return invite

def use_invite_code(code):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE invite_codes SET used_count = used_count + 1 WHERE code = ?", (code,))
    conn.commit()
    conn.close()

def get_bot_setting(key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM bot_settings WHERE key = ?", (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def set_bot_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO bot_settings (key, value, updated_at) VALUES (?, ?, ?)",
              (key, value, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# ===================== لوحات المفاتيح =====================
def main_menu_keyboard(completed=0):
    keyboard = [
        [InlineKeyboardButton("الخدمات", callback_data="services", style="success")],
        [InlineKeyboardButton("تمويل قناتك", callback_data="fund_channel", style="success")],
        [
            InlineKeyboardButton(" تجميع نقاط", callback_data="collect_points", style="primary"),
            InlineKeyboardButton("شحن نقاط", callback_data="charge_points", style="primary")
        ],
        [
            InlineKeyboardButton("استخدام كود", callback_data="use_code", style="success"),
            InlineKeyboardButton("حسابي", callback_data="my_account", style="success")
        ],
        [
            InlineKeyboardButton("فحص طلب", callback_data="check_order", style="primary"),
            InlineKeyboardButton("طلباتي", callback_data="my_orders", style="primary")
        ],
        [
            InlineKeyboardButton("تحويل نقاط", callback_data="transfer_points", style="danger"),
            InlineKeyboardButton("شروط الاستخدام", callback_data="terms", style="danger")
        ],
        [InlineKeyboardButton("متجر البوت", callback_data="store", style="success")],
        [InlineKeyboardButton(f"✅ الطلبات المكتملة: {completed}", callback_data="completed_orders")],
        [InlineKeyboardButton("لوحة التحكم", callback_data="admin_panel", style="danger")]
    ]
    return InlineKeyboardMarkup(keyboard)

def terms_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("موافقة", callback_data="accept_terms", style="primary"),
            InlineKeyboardButton("رفض", callback_data="reject_terms", style="danger")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def collect_points_keyboard():
    keyboard = [
        [InlineKeyboardButton("الهدية اليومية", callback_data="daily_gift", style="primary")],
        [InlineKeyboardButton("رابط الدعوة", callback_data="invite_link", style="primary")],
        [InlineKeyboardButton("عجلة الحظ", callback_data="lucky_wheel", style="primary")],
        [InlineKeyboardButton("قائمة المهام (ربح النقاط)", callback_data="tasks_list")],
        [InlineKeyboardButton("بيع أرقام مقابل نقاط", callback_data="sell_numbers", style="primary")],
        [InlineKeyboardButton("TOP LEVEL", callback_data="top_level", style="danger")],
        [InlineKeyboardButton("رجوع", callback_data="back_main", style="primary")]
    ]
    return InlineKeyboardMarkup(keyboard)

def charge_points_keyboard():
    keyboard = [
        [InlineKeyboardButton(" شحن عبر النجوم", callback_data="charge_stars", style="danger")],
        [InlineKeyboardButton("شحن عبر كاش", callback_data="charge_cash", style="primary")],
        [InlineKeyboardButton("رجوع", callback_data="back_main", style="primary")]
    ]
    return InlineKeyboardMarkup(keyboard)

def tasks_keyboard():
    tasks = get_tasks()
    keyboard = []
    
    if tasks:
        for task in tasks:
            keyboard.append([InlineKeyboardButton(
                f"📢 {task[2]} - {task[4]} نقطة", 
                callback_data=f"task_{task[0]}"
            )])
    else:
        keyboard.append([InlineKeyboardButton("لا توجد مهام حالياً", callback_data="no_tasks", style="primary")])
    
    keyboard.append([InlineKeyboardButton("رجوع", callback_data="collect_points", style="primary")])
    return InlineKeyboardMarkup(keyboard)

def services_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("انستا", callback_data="service_انستا", style="primary"),
            InlineKeyboardButton("تيك توك", callback_data="service_تيك توك", style="primary")
        ],
        [
            InlineKeyboardButton(" يوتيوب", callback_data="service_يوتيوب", style="primary"),
            InlineKeyboardButton("تليجرام", callback_data="service_تليجرام", style="primary")
        ],
        [
            InlineKeyboardButton("تويتر", callback_data="service_تويتر", style="primary"),
            InlineKeyboardButton("فيسبوك", callback_data="service_فيسبوك", style="primary")
        ],
        [
            InlineKeyboardButton("واتساب", callback_data="service_واتساب", style="primary"),
            InlineKeyboardButton("سناب شات", callback_data="service_سناب شات", style="primary")
        ],
        [InlineKeyboardButton("ثريدز", callback_data="service_ثريدز", style="primary")],
        [InlineKeyboardButton("خدمات مجانية", callback_data="service_خدمات مجانية", style="success")],
        [InlineKeyboardButton("رجوع", callback_data="back_main", style="primary")]
    ]
    return InlineKeyboardMarkup(keyboard)

def service_buttons_keyboard(section_name, services):
    keyboard = []
    
    if services:
        for svc in services:
            is_free = "🎁" if svc[10] == 1 else ""
            keyboard.append([InlineKeyboardButton(
                f"{svc[2]} {svc[1]} - {svc[3]} نقطة {is_free}", 
                callback_data=f"buy_service_{svc[0]}"
            )])
    else:
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="services")])
    
    return InlineKeyboardMarkup(keyboard)

def store_services_keyboard():
    services = get_store_services()
    keyboard = []
    
    if services:
        for svc in services:
            keyboard.append([InlineKeyboardButton(
                f"{svc[2]} {svc[1]} - {svc[3]} نقطة", 
                callback_data=f"buy_store_service_{svc[0]}"
            )])
    else:
        keyboard.append([InlineKeyboardButton("لا يوجد خدمات حالياً", callback_data="no_store_service", style="primary")])
    
    keyboard.append([InlineKeyboardButton("رجوع", callback_data="back_main", style="primary")])
    return InlineKeyboardMarkup(keyboard)

def service_detail_keyboard(service_id):
    keyboard = [
        [InlineKeyboardButton("رجوع", callback_data=f"back_to_service_{service_id}", style="primary")],
        [InlineKeyboardButton("إلغاء", callback_data="services", style="danger")]
    ]
    return InlineKeyboardMarkup(keyboard)

def store_service_detail_keyboard(service_id):
    keyboard = [
        [InlineKeyboardButton("رجوع", callback_data=f"back_to_store_service_{service_id}", style="primary")],
        [InlineKeyboardButton("إلغاء", callback_data="store", style="danger")]
    ]
    return InlineKeyboardMarkup(keyboard)

def fund_channel_keyboard():
    keyboard = [
        [InlineKeyboardButton("ابدأ تمويل قناتي", callback_data="start_fund", style="success")],
        [InlineKeyboardButton("حملاتي", callback_data="my_campaigns", style="primary")],
        [InlineKeyboardButton("رجوع", callback_data="back_main", style="primary")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("إدارة الأقسام", callback_data="admin_sections", style="primary"),
            InlineKeyboardButton("إضافة خدمات", callback_data="admin_add_service", style="primary")
        ],
        [
            InlineKeyboardButton("إدارة المتجر والخدمات", callback_data="admin_store_services", style="primary"),
            InlineKeyboardButton("قنوات النقاط", callback_data="admin_points_channels", style="primary")
        ],
        [
            InlineKeyboardButton("قنوات إجباري", callback_data="admin_forced_channels", style="primary"),
            InlineKeyboardButton("مواقع SMM", callback_data="admin_smm_sites", style="success")
        ],
        [
            InlineKeyboardButton("قنوات الطلبات", callback_data="admin_orders_channels", style="primary"),
            InlineKeyboardButton("قناة السجل", callback_data="admin_log_channels", style="primary")
        ],
        [
            InlineKeyboardButton("إدارة المستخدمين", callback_data="admin_users", style="primary"),
            InlineKeyboardButton("الإحصائيات", callback_data="admin_stats", style="primary")
        ],
        [
            InlineKeyboardButton("إذاعة جماعية", callback_data="admin_broadcast", style="primary"),
            InlineKeyboardButton("خدمات مجانية", callback_data="admin_free_services", style="success")
        ],
        [
            InlineKeyboardButton("عجلة الحظ", callback_data="admin_wheel", style="primary"),
            InlineKeyboardButton("رابط نقاط سريع", callback_data="admin_quick_link", style="primary")
        ],
        [
            InlineKeyboardButton("أكواد الدعوة", callback_data="admin_invite_codes", style="primary"),
            InlineKeyboardButton("التحديثات/الدعم", callback_data="admin_settings", style="primary")
        ],
        [
            InlineKeyboardButton("إضافة رصيد", callback_data="admin_add_balance", style="primary"),
            InlineKeyboardButton("خصم رصيد", callback_data="admin_remove_balance", style="danger")
        ],
        [
            InlineKeyboardButton("رجوع", callback_data="back_main", style="primary")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_to_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("رجوع", callback_data="back_main", style="primary")]
    ]
    return InlineKeyboardMarkup(keyboard)

def select_section_keyboard():
    sections_list = [
        ("انستا", "انستا"),
        ("تيك توك", "تيك توك"),
        ("يوتيوب", "يوتيوب"),
        ("تليجرام", "تليجرام"),
        ("تويتر", "تويتر"),
        ("فيسبوك", "فيسبوك"),
        ("واتساب", "واتساب"),
        ("سناب شات", "سناب شات"),
        ("ثريدز", "ثريدز"),
        ("خدمات مجانية", "خدمات مجانية")
    ]
    
    keyboard = []
    for name, value in sections_list:
        keyboard.append([InlineKeyboardButton(f"📌 {name}", callback_data=f"select_section_{value}")])
    
    keyboard.append([InlineKeyboardButton("رجوع", callback_data="back_main", style="primary")])
    return InlineKeyboardMarkup(keyboard)

def admin_stats_keyboard():
    keyboard = [
        [InlineKeyboardButton("رجوع", callback_data="back_main", style="primary")]
    ]
    return InlineKeyboardMarkup(keyboard)

def wheel_admin_keyboard():
    prizes = get_wheel_prizes()
    total_weight = get_wheel_total_weight()
    
    keyboard = []
    for p in prizes:
        percent = (p[3] / total_weight * 100) if total_weight > 0 else 0
        keyboard.append([InlineKeyboardButton(
            f"{'✅'} {p[1]} نقطة ({p[2]}) — {percent:.1f}%",
            callback_data=f"wheel_delete_{p[0]}"
        )])
    
    keyboard.append([InlineKeyboardButton("إضافة جائزة", callback_data="wheel_add", style="primary")])
    keyboard.append([InlineKeyboardButton("رجوع", callback_data="back_main", style="primary")])
    return InlineKeyboardMarkup(keyboard)

def invite_codes_keyboard():
    keyboard = [
        [InlineKeyboardButton("إنشاء كود جديد", callback_data="invite_create", style="primary")],
        [InlineKeyboardButton("رجوع", callback_data="back_main", style="primary")]
    ]
    return InlineKeyboardMarkup(keyboard)

def broadcast_keyboard():
    keyboard = [
        [InlineKeyboardButton("الكل", callback_data="broadcast_all", style="primary")],
        [InlineKeyboardButton("غير نشطين 7 أيام", callback_data="broadcast_inactive", style="success")],
        [InlineKeyboardButton("رصيد أقل من 50", callback_data="broadcast_low_balance", style="danger")],
        [InlineKeyboardButton("رجوع", callback_data="back_main", style="primary")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ===================== معالجات البوت =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    referrer_id = None
    
    if context.args:
        arg = context.args[0]
        if arg.startswith("ref_"):
            try:
                referrer_id = int(arg.replace("ref_", ""))
            except:
                pass
        elif arg.startswith("gift_"):
            code = arg.replace("gift_", "")
            link = get_quick_link(code)
            if link:
                points = link[1]
                max_uses = link[2]
                used_count = link[3]
                if max_uses == 0 or used_count < max_uses:
                    update_balance(user.id, points)
                    use_quick_link(code)
                    await update.message.reply_text(f"🎁 تم تفعيل الهدية! +{points} نقطة")
                    return
                else:
                    await update.message.reply_text("❌ هذا الرابط انتهى صلاحيته")
                    return
        elif arg.startswith("invite_"):
            code = arg.replace("invite_", "")
            invite = get_invite_code(code)
            if invite:
                points = invite[1]
                max_users = invite[2]
                used_count = invite[3]
                if max_users == 0 or used_count < max_users:
                    update_balance(user.id, points)
                    use_invite_code(code)
                    await update.message.reply_text(f"🎉 تم تفعيل كود الدعوة! +{points} نقطة")
                    return
                else:
                    await update.message.reply_text("❌ هذا الكود انتهى صلاحيته")
                    return
    
    add_user(user.id, user.username or "NoUsername", user.first_name or "User", referrer_id)
    
    if get_accepted_terms(user.id) == 0:
        await update.message.reply_text(
            "📜 **شروط استخدام البوت**\n\n"
            "• يمنع استخدام البوت لأغراض غير قانونية\n"
            "• النقاط غير قابلة للاسترداد نقداً\n"
            "• يحق للإدارة تعليق الحساب عند المخالفة\n"
            "• مدة التنفيذ تختلف حسب الخدمة\n"
            "• البوت غير مسؤول عن أي حظر من المنصات\n"
            "• جميع المعاملات نهائية\n\n"
            "✅ باستخدامك للبوت فأنت توافق على هذه الشروط",
            reply_markup=terms_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    balance = get_balance(user.id)
    completed = get_completed_orders(user.id)
    
    welcome = f"""
👋 مرحباً بك في فولو ـ 𝐅𝐎𝐋𝐎

🔹 تفكيك بنفسك هي أول خطوة نحو كل ما تريد تحقيقه.

💰 رصيدك: {balance:,} نقطة
🆔 إيديك: {user.id}

⚡ أسرع بوت خدمات - أسعار منافسة - دعم متواصل

📌 اختر من القائمة 👇
"""
    
    await update.message.reply_text(
        welcome,
        reply_markup=main_menu_keyboard(completed),
        parse_mode="Markdown"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "accept_terms":
        set_accepted_terms(user_id, 1)
        balance = get_balance(user_id)
        completed = get_completed_orders(user_id)
        welcome = f"""
👋 مرحباً بك في فولو ـ 𝐅𝐎𝐋𝐎

🔹 تفكيك بنفسك هي أول خطوة نحو كل ما تريد تحقيقه.

💰 رصيدك: {balance:,} نقطة
🆔 إيديك: {user_id}

⚡ أسرع بوت خدمات - أسعار منافسة - دعم متواصل

📌 اختر من القائمة 👇
"""
        await query.edit_message_text(
            welcome,
            reply_markup=main_menu_keyboard(completed),
            parse_mode="Markdown"
        )
        return
    
    elif data == "reject_terms":
        await query.edit_message_text(
            "❌ يجب الموافقة على الشروط لاستخدام البوت.\n"
            "📌 استخدم /start مرة أخرى للموافقة.",
            parse_mode="Markdown"
        )
        return
    
    if data == "back_main":
        balance = get_balance(user_id)
        completed = get_completed_orders(user_id)
        welcome = f"""
👋 مرحباً بك في فولو ـ 𝐅𝐎𝐋𝐎

🔹 تفكيك بنفسك هي أول خطوة نحو كل ما تريد تحقيقه.

💰 رصيدك: {balance:,} نقطة
🆔 إيديك: {user_id}

⚡ أسرع بوت خدمات - أسعار منافسة - دعم متواصل

📌 اختر من القائمة 👇
"""
        await query.edit_message_text(
            welcome,
            reply_markup=main_menu_keyboard(completed),
            parse_mode="Markdown"
        )
        return
    
    elif data == "services":
        await query.edit_message_text(
            "📋 **أهلاً بك في قسم الخدمات**\n\nاختر الخدمة التي تريدها 👇",
            reply_markup=services_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    elif data.startswith("service_"):
        section_name = data.replace("service_", "")
        services = get_services_by_section(section_name)
        
        if services:
            msg = f"👋 | مرحباً بك في قسم : {section_name}\n🛍 | اختر ما تريد من الخدمات :👇"
            await query.edit_message_text(
                msg,
                reply_markup=service_buttons_keyboard(section_name, services),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                f"📌 **خدمة {section_name}**\n\n"
                "❌ عذراً، لا توجد خدمات حالياً\n"
                "📢 سيتم إضافة الخدمات قريباً\n\n"
                "🔙 يمكنك الرجوع للقائمة الرئيسية",
                reply_markup=service_buttons_keyboard(section_name, services),
                parse_mode="Markdown"
            )
        return
    
    elif data.startswith("buy_service_"):
        service_id = int(data.replace("buy_service_", ""))
        service = get_service_by_id(service_id)
        
        if not service:
            await query.edit_message_text(
                "❌ الخدمة غير موجودة",
                reply_markup=services_keyboard(),
                parse_mode="Markdown"
            )
            return
        
        balance = get_balance(user_id)
        section_name = service[1]
        name = service[2]
        icon = service[3]
        price = service[4]
        min_order = service[5]
        max_order = service[6]
        description = service[7]
        is_free = service[10] if len(service) > 10 else 0
        guarantee = service[13] if len(service) > 13 and service[13] else "ضمان البوت"
        delivery_time = service[14] if len(service) > 14 and service[14] else "خلال 24 ساعة"
        
        can_order = balance // price if price > 0 else 0
        
        if is_free == 1:
            msg = f"""
🎁 **خدمة مجانية**

📌 **القسم:** {section_name}
📌 **الخدمة:** {icon} {name}

📝 **الوصف:** {description}
━━━━━━━━━━━━━━━

📌 **الخطوة 1:** أرسل الرابط:
"""
        else:
            msg = f"""
🎁 **{icon} {name}**

📝 **الوصف:** {description}
💰 **السعر:** {price} نقطة / وحدة
📉 **الحد الأدنى:** {min_order}
📈 **الحد الأقصى:** {max_order:,}
💳 **رصيدك:** {balance:,} نقطة
🛡️ **الضمان:** {guarantee}
⏱️ **وقت التسليم التقريبي:** {delivery_time}
━━━━━━━━━━━━━━━

📌 **الخطوة 1:** أرسل الرابط:
"""
        
        context.user_data['service_id'] = service_id
        context.user_data['action'] = 'waiting_service_link'
        
        await query.edit_message_text(
            msg,
            reply_markup=service_detail_keyboard(service_id),
            parse_mode="Markdown"
        )
        return WAITING_SERVICE_LINK_ONLY
    
    elif data == "store":
        services = get_store_services()
        if services:
            await query.edit_message_text(
                "🛒 **متجر البوت**\n\n📌 اختر الخدمة التي تريدها 👇",
                reply_markup=store_services_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "🛒 **متجر البوت**\n\n📌 لا توجد خدمات حالياً\n📢 سيتم إضافة الخدمات قريباً",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
        return
    
    elif data == "no_store_service":
        await query.answer("📌 لا توجد خدمات في المتجر حالياً")
        return
    
    elif data.startswith("buy_store_service_"):
        service_id = int(data.replace("buy_store_service_", ""))
        service = get_service_by_id(service_id)
        
        if not service:
            await query.edit_message_text(
                "❌ الخدمة غير موجودة",
                reply_markup=store_services_keyboard(),
                parse_mode="Markdown"
            )
            return
        
        balance = get_balance(user_id)
        name = service[2]
        icon = service[3]
        price = service[4]
        min_order = service[5]
        max_order = service[6]
        description = service[7]
        guarantee = service[12] if len(service) > 12 and service[12] else "ضمان البوت"
        delivery_time = service[13] if len(service) > 13 and service[13] else "خلال 24 ساعة"
        
        can_order = balance // price if price > 0 else 0
        
        msg = f"""
🎁 **{icon} {name}**

📝 **الوصف:** {description}
💰 **السعر:** {price} نقطة / وحدة
📉 **الحد الأدنى:** {min_order}
📈 **الحد الأقصى:** {max_order:,}
💳 **رصيدك:** {balance:,} نقطة
🛡️ **الضمان:** {guarantee}
⏱️ **وقت التسليم التقريبي:** {delivery_time}
━━━━━━━━━━━━━━━

📌 **الخطوة 1:** أرسل الرابط:
"""
        
        context.user_data['service_id'] = service_id
        context.user_data['action'] = 'waiting_store_link'
        
        await query.edit_message_text(
            msg,
            reply_markup=store_service_detail_keyboard(service_id),
            parse_mode="Markdown"
        )
        return WAITING_SMM_ORDER_LINK
    
    elif data.startswith("back_to_store_service_"):
        services = get_store_services()
        if services:
            await query.edit_message_text(
                "🛒 **متجر البوت**\n\n📌 اختر الخدمة التي تريدها 👇",
                reply_markup=store_services_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "🛒 **متجر البوت**\n\n📌 لا توجد خدمات حالياً",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
        return
    
    elif data.startswith("back_to_service_"):
        service_id = int(data.replace("back_to_service_", ""))
        service = get_service_by_id(service_id)
        if service:
            section_name = service[1]
            services = get_services_by_section(section_name)
            msg = f"👋 | مرحباً بك في قسم : {section_name}\n🛍 | اختر ما تريد من الخدمات :👇"
            await query.edit_message_text(
                msg,
                reply_markup=service_buttons_keyboard(section_name, services),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "📋 **أهلاً بك في قسم الخدمات**",
                reply_markup=services_keyboard(),
                parse_mode="Markdown"
            )
        return
    
    elif data == "no_service":
        await query.answer("⚠️ لا توجد خدمات في هذا القسم حالياً")
        return
    
    elif data == "fund_channel":
        await query.edit_message_text(
            "🚀 **تمويل قناتك**\n\n"
            "زِد عدد أعضاء قناتك! يضيف البوت قناتك كاشتراك إجباري على كل المستخدمين حتى تصل للعدد المطلوب.\n\n"
            "💰 سعر العضو: 5 نقطة\n"
            "📉 الحد الأدنى: 1 | 📈 الحد الأقصى: 5,000\n"
            "📡 القنوات الممولة حالياً: 0/20\n\n"
            "⚠️ يجب أن يكون البوت أدمن بقناتك بصلاحية دعوة المستخدمين عبر رابط.",
            reply_markup=fund_channel_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    elif data == "collect_points":
        await query.edit_message_text(
            "⭐ **تجميع نقاط**\n\nاختر طريقة تجميع النقاط 👇",
            reply_markup=collect_points_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    elif data == "charge_points":
        await query.edit_message_text(
            "💳 **شحن نقاط**\n\nاختر طريقة الشحن 👇",
            reply_markup=charge_points_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    elif data == "charge_stars":
        await query.edit_message_text(
            "⭐ **شحن عبر النجوم**\n\n"
            "📌 قم بإرسال عدد النجوم التي تريد شحنها\n\n"
            "💰 1 نجمة = 100 نقطة\n"
            "💰 5 نجوم = 550 نقطة (خصم 10%)\n"
            "💰 10 نجوم = 1200 نقطة (خصم 20%)\n\n"
            "✏️ أرسل عدد النجوم:",
            reply_markup=charge_points_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'charge_stars'
        return WAITING_CHARGE_STARS
    
    elif data == "charge_cash":
        await query.edit_message_text(
            "💳 **شحن عبر كاش**\n\n"
            "📌 قم بإرسال المبلغ الذي تريد شحنه\n\n"
            "💰 10 جنيه = 1000 نقطة\n"
            "💰 50 جنيه = 5500 نقطة (خصم 10%)\n"
            "💰 100 جنيه = 12000 نقطة (خصم 20%)\n\n"
            "📌 للتواصل مع الدعم: @TeleRaiseSupport\n\n"
            "✏️ أرسل المبلغ:",
            reply_markup=charge_points_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'charge_cash'
        return WAITING_CHARGE_CASH
    
    elif data == "daily_gift":
        today = datetime.now().strftime("%Y-%m-%d")
        claimed = get_daily_claimed(user_id)
        
        if claimed == today:
            await query.edit_message_text(
                "🎁 **الهدية اليومية**\n\n"
                "❌ لقد حصلت على الهدية اليومية بالفعل!\n"
                "⏳ انتظر حتى الغد للحصول على هدية جديدة.",
                reply_markup=collect_points_keyboard(),
                parse_mode="Markdown"
            )
        else:
            points = random.randint(10, 50)
            update_balance(user_id, points)
            set_daily_claimed(user_id, today)
            
            await query.edit_message_text(
                f"🎁 **الهدية اليومية**\n\n"
                f"✅ تم منحك {points} نقطة!\n\n"
                f"💰 رصيدك الحالي: {get_balance(user_id):,} نقطة\n\n"
                f"⏳ عد غداً للحصول على هدية جديدة!",
                reply_markup=collect_points_keyboard(),
                parse_mode="Markdown"
            )
        return
    
    elif data == "invite_link":
        await query.edit_message_text(
            "🔗 **رابط الدعوة**\n\n"
            f"📌 ادعُ أصدقائك للبوت واحصل على نقاط!\n\n"
            f"🔗 رابطك المخصص:\n"
            f"`https://t.me/TeleRaiseProBot?start=ref_{user_id}`\n\n"
            "💰 لكل صديق يدخل عن طريقك تحصل على 50 نقطة!\n\n"
            "📊 عدد المدعوين: 0",
            reply_markup=collect_points_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    elif data == "lucky_wheel":
        prize = spin_wheel()
        
        if prize:
            points = prize[2]
            name = prize[1]
            update_balance(user_id, points)
            msg = f"🎡 **عجلة الحظ**\n\n"
            msg += f"🎉 تهانينا! لقد ربحت {name}!\n"
            msg += f"💰 +{points} نقطة\n"
            msg += f"💳 رصيدك الحالي: {get_balance(user_id):,} نقطة"
        else:
            msg = f"🎡 **عجلة الحظ**\n\n"
            msg += f"😅 للأسف، لم تربح أي نقطة هذه المرة.\n"
            msg += f"🔄 جرب حظك مرة أخرى!"
        
        await query.edit_message_text(
            msg,
            reply_markup=collect_points_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    elif data == "tasks_list":
        tasks = get_tasks()
        if tasks:
            await query.edit_message_text(
                "📋 **قائمة المهام (ربح النقاط)**\n\n"
                "📌 اشترك في القنوات التالية للحصول على نقاط:\n\n"
                "اختر قناة للاشتراك 👇",
                reply_markup=tasks_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "📋 **قائمة المهام (ربح النقاط)**\n\n"
                "📌 لا توجد مهام حالياً\n"
                "⏳ سيتم إضافة مهام قريباً",
                reply_markup=collect_points_keyboard(),
                parse_mode="Markdown"
            )
        return
    
    elif data.startswith("task_"):
        task_id = int(data.replace("task_", ""))
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT channel_id, channel_name, channel_link, points FROM tasks WHERE id = ?", (task_id,))
        task = c.fetchone()
        conn.close()
        
        if task:
            await query.edit_message_text(
                f"📢 **مهمة: {task[1]}**\n\n"
                f"🔗 رابط القناة: {task[2]}\n"
                f"💰 المكافأة: {task[3]} نقطة\n\n"
                f"📌 الخطوة 1: اضغط على الرابط واشترك في القناة\n"
                f"📌 الخطوة 2: ارسل تأكيد الاشتراك\n\n"
                f"✏️ أرسل `/confirm` بعد الاشتراك",
                reply_markup=tasks_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "❌ المهمة غير موجودة",
                reply_markup=collect_points_keyboard(),
                parse_mode="Markdown"
            )
        return
    
    elif data == "no_tasks":
        await query.answer("📌 لا توجد مهام حالياً")
        return
    
    elif data == "sell_numbers":
        await query.edit_message_text(
            "💰 **بيع أرقام مقابل نقاط**\n\n"
            "📌 يمكنك بيع أرقامك مقابل نقاط!\n\n"
            "📌 الأرقام المتاحة:\n"
            "• 010xxxxxxx - 1000 نقطة\n"
            "• 011xxxxxxx - 800 نقطة\n"
            "• 012xxxxxxx - 600 نقطة\n\n"
            "✏️ أرسل الرقم الذي تريد بيعه:",
            reply_markup=collect_points_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'sell_number'
        return WAITING_SELL_NUMBER
    
    elif data == "top_level":
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_id, username, first_name, balance FROM users ORDER BY balance DESC LIMIT 10")
        users = c.fetchall()
        conn.close()
        
        msg = "🏆 **TOP LEVEL**\n\n"
        msg += "📊 ترتيب المستخدمين حسب النقاط:\n\n"
        
        emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for i, user in enumerate(users):
            name = user[2] or user[1] or f"User{user[0]}"
            msg += f"{emojis[i] if i < 10 else '•'} {name} - {user[3]:,} نقطة\n"
        
        await query.edit_message_text(
            msg,
            reply_markup=collect_points_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    elif data == "transfer_points":
        await query.edit_message_text(
            "🔄 **تحويل نقاط**\n\n"
            "📌 لتحويل النقاط لأحد المستخدمين:\n\n"
            "✏️ أرسل معرف المستخدم (ID):",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'transfer_id'
        return WAITING_TRANSFER_ID
    
    elif data == "use_code":
        await query.edit_message_text(
            "🎫 **استخدام كود**\n\n"
            "📌 أدخل الكود الذي لديك:\n\n"
            "✏️ أرسل الكود:",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'use_code'
        return WAITING_USE_CODE
    
    elif data == "my_account":
        balance = get_balance(user_id)
        completed = get_completed_orders(user_id)
        text = f"👤 **حسابي**\n\n"
        text += f"🆔 المعرف: {user_id}\n"
        text += f"💰 الرصيد: {balance:,} نقطة\n"
        text += f"✅ الطلبات المكتملة: {completed}\n"
        await query.edit_message_text(
            text,
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    elif data == "check_order":
        await query.edit_message_text(
            "🔍 **فحص طلب**\n\n"
            "📌 أدخل رقم الطلب للتحقق:\n"
            "مثال: `#123`\n\n"
            "✏️ أرسل رقم الطلب:",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    elif data == "my_orders":
        await query.edit_message_text(
            "📦 **طلباتي**\n\n"
            "لا توجد طلبات حتى الآن.",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    elif data == "terms":
        await query.edit_message_text(
            "📜 **شروط استخدام البوت**\n\n"
            "• يمنع استخدام البوت لأغراض غير قانونية\n"
            "• النقاط غير قابلة للاسترداد نقداً\n"
            "• يحق للإدارة تعليق الحساب عند المخالفة\n"
            "• مدة التنفيذ تختلف حسب الخدمة\n"
            "• البوت غير مسؤول عن أي حظر من المنصات\n"
            "• جميع المعاملات نهائية\n\n"
            "✅ باستخدامك للبوت فأنت توافق على هذه الشروط",
            reply_markup=terms_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    elif data == "completed_orders":
        completed = get_completed_orders(user_id)
        await query.edit_message_text(
            f"✅ **الطلبات المكتملة**\n\n"
            f"📊 عدد الطلبات المكتملة: {completed}",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    elif data == "start_fund":
        await query.edit_message_text(
            "🚀 **بدء تمويل قناتك**\n\n"
            "📌 لإضافة قناتك للتمويل:\n"
            "1️⃣ تأكد من أن البوت أدمن في قناتك\n"
            "2️⃣ أرسل رابط قناتك\n"
            "3️⃣ حدد عدد الأعضاء المطلوب\n\n"
            "✏️ أرسل رابط قناتك الآن:",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    elif data == "my_campaigns":
        await query.edit_message_text(
            "📊 **حملاتي**\n\n"
            "🔹 ليس لديك أي حملات حالياً\n\n"
            "📌 يمكنك بدء حملة جديدة من خلال:\n"
            "🚀 ابدأ تمويل قناتي",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    # ===================== لوحة التحكم =====================
    elif data == "admin_panel":
        if user_id != ADMIN_ID:
            await query.edit_message_text(
                "⛔ عذراً، هذه اللوحة مخصصة للمشرفين فقط.",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
            return
        
        await query.edit_message_text(
            "⚙️ **لوحة التحكم**\n\nمرحباً بك في لوحة تحكم المشرف",
            reply_markup=admin_main_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    elif data == "admin_store_services":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        services = get_store_services()
        text = "🛒 **إدارة المتجر والخدمات**\n\n"
        
        if services:
            for svc in services:
                text += f"📌 {svc[2]} {svc[1]} - {svc[3]} نقطة\n"
                text += f"   📝 {svc[6]}\n"
                text += f"   🆔 SITE_ID: {svc[7] or 'غير محدد'}\n\n"
        else:
            text += "📌 لا توجد خدمات في المتجر حالياً\n"
        
        text += "\n📌 لإضافة خدمة في المتجر، أرسل:\n"
        text += "`الاسم|الايقونة|السعر|الحد_الأدنى|الحد_الأقصى|الوصف|الضمان|وقت_التسليم|SITE_ID`\n"
        text += "مثال: `متابعين انستا|📊|100|1|1000|خدمة متابعة|ضمان 30 يوم|خلال 24 ساعة|1234`"
        
        keyboard = [
            [InlineKeyboardButton("إضافة خدمة متجر", callback_data="admin_add_store_service", style="primary")],
            [InlineKeyboardButton("رجوع", callback_data="back_main", style="primary")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    elif data == "admin_add_store_service":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        await query.edit_message_text(
            "📌 **إضافة خدمة في المتجر**\n\n"
            "أرسل بهذا الشكل:\n"
            "`الاسم|الايقونة|السعر|الحد_الأدنى|الحد_الأقصى|الوصف|الضمان|وقت_التسليم|SITE_ID`\n\n"
            "مثال: `متابعين انستا|📊|100|1|1000|خدمة متابعة|ضمان 30 يوم|خلال 24 ساعة|1234`\n\n"
            "✏️ أرسل الآن:",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'add_store_service'
        return WAITING_ADD_SERVICE
    
    elif data == "admin_add_service":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        await query.edit_message_text(
            "📌 **اختر القسم لإضافة الخدمة فيه**\n\n"
            "اختر القسم الذي تريد إضافة الخدمة إليه 👇",
            reply_markup=select_section_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    elif data.startswith("select_section_"):
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        section_name = data.replace("select_section_", "")
        context.user_data['section_name'] = section_name
        
        await query.edit_message_text(
            f"📌 **إضافة خدمة في قسم {section_name}**\n\n"
            "أرسل بهذا الشكل:\n"
            "`الاسم|الايقونة|السعر|الحد_الأدنى|الحد_الأقصى|الوصف|الضمان|وقت_التسليم`\n\n"
            "مثال: `مشتركين قناة|📢|20|100|1000|قناة ثابته سريعه|ضمان 30 يوم|خلال 24 ساعة`\n\n"
            "✏️ أرسل الآن:",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'add_service'
        return WAITING_ADD_SERVICE
    
    elif data == "admin_sections":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        sections = get_sections()
        text = "📂 **إدارة الأقسام والخدمات**\n\n"
        
        if sections:
            for sec in sections:
                services = get_services_by_section(sec[1])
                text += f"📌 {sec[2]} {sec[1]}\n"
                if services:
                    for svc in services:
                        is_free = "🎁" if svc[10] == 1 else ""
                        is_store = "🛒" if svc[12] == 1 else ""
                        text += f"   • {svc[2]} {svc[1]} - {svc[3]} نقطة {is_free}{is_store}\n"
                else:
                    text += f"   • لا توجد خدمات في هذا القسم\n"
                text += "\n"
        else:
            text += "📌 لا توجد أقسام حالياً\n"
        
        text += "\n📌 لإضافة قسم جديد، أرسل:\n"
        text += "`تيك توك|📱` أو `انستجرام|📸`"
        
        keyboard = [
            [InlineKeyboardButton("إضافة قسم جديد", callback_data="add_section", style="primary")],
            [InlineKeyboardButton("رجوع", callback_data="back_main", style="primary")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'add_section'
        return
    
    elif data == "add_section":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        await query.edit_message_text(
            "📌 **إضافة قسم جديد**\n\n"
            "أرسل القسم بهذا الشكل:\n"
            "`تيك توك|📱`\n"
            "أو: `انستجرام|📸`\n\n"
            "✏️ أرسل الآن:",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'add_section'
        return WAITING_ADD_SECTION
    
    elif data == "admin_points_channels":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        channels = get_points_channels()
        text = "💰 **قنوات النقاط**\n\n"
        
        if channels:
            for ch in channels:
                text += f"• {ch[1]} | {ch[2]} | {ch[4]} نقطة\n"
                text += f"  {ch[3]}\n\n"
        else:
            text += "📌 لا توجد قنوات نقاط حالياً\n"
        
        text += "\n📌 لإضافة قناة، أرسل بهذا الشكل:\n"
        text += "`channel_id|الاسم|https://t.me/channel|النقاط`"
        
        keyboard = [
            [InlineKeyboardButton("إضافة قناة نقاط", callback_data="add_points_channel", style="primary")],
            [InlineKeyboardButton("رجوع", callback_data="back_main", style="primary")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    elif data == "add_points_channel":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        await query.edit_message_text(
            "📌 **إضافة قناة نقاط**\n\n"
            "أرسل بهذا الشكل:\n"
            "`channel_id|الاسم|https://t.me/channel|النقاط`\n\n"
            "مثال: `-1001234567890|قناة النقاط|https://t.me/mychannel|50`\n"
            "أو: `@mychannel|قناتي|https://t.me/mychannel|50`\n\n"
            "✏️ أرسل الآن:",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'add_points_channel'
        return WAITING_ADD_CHANNEL_POINTS
    
    elif data == "admin_forced_channels":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        channels = get_forced_channels()
        text = "🔒 **قنوات إجباري**\n\n"
        
        if channels:
            for ch in channels:
                text += f"• {ch[1]} | {ch[2]}\n"
                text += f"  {ch[3]}\n\n"
        else:
            text += "📌 لا توجد قنوات إجبارية حالياً\n"
        
        keyboard = [
            [InlineKeyboardButton("إضافة قناة إجباري", callback_data="add_forced_channel", style="primary")],
            [InlineKeyboardButton("رجوع", callback_data="back_main", style="primary")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    elif data == "add_forced_channel":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        await query.edit_message_text(
            "📌 **إضافة قناة إجباري**\n\n"
            "أرسل بهذا الشكل:\n"
            "`channel_id|الاسم|الرابط`\n\n"
            "مثال: `-1001234567890|قناة إجباري|https://t.me/mychannel`\n\n"
            "✏️ أرسل الآن:",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'add_forced_channel'
        return WAITING_ADD_FORCED_CHANNEL
    
    elif data == "admin_smm_sites":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        sites = get_smm_sites()
        text = "🌐 **مواقع SMM**\n\n"
        
        if sites:
            for site in sites:
                active = "✅ (نشط)" if site[4] == 1 else ""
                text += f"• {site[1]} {active}\n"
                text += f"  URL: {site[2]}\n"
                text += f"  KEY: {site[3][:10]}...\n"
                text += f"  💰 الرصيد: {site[5]:.2f}$\n\n"
        else:
            text += "📌 لا توجد مواقع SMM حالياً\n"
        
        text += "\n📌 لإضافة موقع، أرسل بهذا الشكل:\n"
        text += "`الاسم|API_URL|API_KEY`"
        
        keyboard = [
            [InlineKeyboardButton("إضافة موقع SMM", callback_data="add_smm_site", style="danger")],
            [InlineKeyboardButton("رجوع", callback_data="back_main", style="primary")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    elif data == "add_smm_site":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        await query.edit_message_text(
            "📌 **إضافة موقع SMM**\n\n"
            "أرسل بهذا الشكل:\n"
            "`الاسم|API_URL|API_KEY`\n\n"
            "✏️ أرسل الآن:",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'add_smm_site'
        return WAITING_ADD_SMM
    
    elif data == "admin_orders_channels":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        channels = get_orders_channels()
        text = "📦 **قنوات الطلبات**\n\n"
        
        if channels:
            for ch in channels:
                text += f"• {ch[1]} | {ch[2]}\n"
        else:
            text += "📌 لا توجد قنوات طلبات حالياً\n"
        
        text += "\n📌 لإضافة قناة طلبات، أرسل:\n"
        text += "`channel_id|الاسم`"
        
        keyboard = [
            [InlineKeyboardButton("إضافة قناة طلبات", callback_data="add_orders_channel", style="success")],
            [InlineKeyboardButton("رجوع", callback_data="back_main", style="primary")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    elif data == "add_orders_channel":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        await query.edit_message_text(
            "📌 **إضافة قناة طلبات**\n\n"
            "أرسل بهذا الشكل:\n"
            "`channel_id|الاسم`\n\n"
            "مثال: `-1001234567890|طلبات البوت`\n\n"
            "✏️ أرسل الآن:",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'add_orders_channel'
        return WAITING_ADD_ORDERS_CHANNEL
    
    elif data == "admin_log_channels":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        channels = get_log_channels()
        text = "📝 **قناة سجل المستخدمين**\n\n"
        
        if channels:
            for ch in channels:
                text += f"• {ch[1]} | {ch[2]}\n"
        else:
            text += "📌 لا توجد قنوات سجل حالياً\n"
        
        text += "\n📌 لإضافة قناة سجل، أرسل:\n"
        text += "`channel_id|الاسم`"
        
        keyboard = [
            [InlineKeyboardButton("إضافة قناة سجل", callback_data="add_log_channel", style="primary")],
            [InlineKeyboardButton("رجوع", callback_data="back_main", style="primary")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    elif data == "add_log_channel":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        await query.edit_message_text(
            "📌 **إضافة قناة سجل مستخدمين**\n\n"
            "أرسل بهذا الشكل:\n"
            "`channel_id|الاسم`\n\n"
            "مثال: `-1001234567890|قناة السجل`\n"
            "أو: `@mychannel|سجل المستخدمين`\n\n"
            "⚠️ يجب أن يكون البوت أدمن في القناة وله صلاحية نشر الرسائل\n\n"
            "✏️ أرسل الآن:",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'add_log_channel'
        return WAITING_ADD_LOG_CHANNEL
    
    elif data == "admin_users":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        await query.edit_message_text(
            "👥 **إدارة المستخدمين**\n\n"
            "📌 للبحث عن مستخدم، أرسل ID المستخدم:\n\n"
            "✏️ أرسل ID المستخدم:",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'search_user'
        return WAITING_SEARCH_USER
    
    elif data == "admin_stats":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        users_count = get_all_users_count()
        orders_count = get_all_orders_count()
        pending_count = get_pending_orders_count()
        completed_count = orders_count - pending_count
        today_orders = get_today_orders_count()
        total_points_used = get_total_points_used()
        today_points_used = get_today_points_used()
        total_referrals = get_total_referrals()
        
        total_profit = total_points_used * 0.01
        today_profit = today_points_used * 0.01
        
        sites = get_smm_sites()
        sites_balance = ""
        for site in sites:
            sites_balance += f"  {site[1]}: {site[5]:.2f}$\n"
        
        text = "📊 **الإحصائيات**\n\n"
        text += "━━━━━━━━━━━━━━━\n"
        text += f"👥 **المستخدمون:** {users_count}\n"
        text += f"📦 **الطلبات:** {orders_count} (اليوم: {today_orders})\n"
        text += f"💰 **نقاط مستخدمة:** {total_points_used:,}\n"
        text += f"💵 **الأرباح:** {total_profit:.2f}$ (اليوم: {today_profit:.2f}$)\n"
        text += f"🔗 **الإحالات:** {total_referrals}\n"
        text += "━━━━━━━━━━━━━━━\n"
        text += "**أرصدة المواقع:**\n"
        text += sites_balance if sites_balance else "  لا توجد مواقع\n"
        text += "━━━━━━━━━━━━━━━"
        
        await query.edit_message_text(
            text,
            reply_markup=admin_stats_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    elif data == "admin_broadcast":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        await query.edit_message_text(
            "📢 **إذاعة جماعية**\n\n"
            "اختر الفئة المستهدفة 👇",
            reply_markup=broadcast_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    elif data.startswith("broadcast_"):
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        broadcast_type = data.replace("broadcast_", "")
        context.user_data['broadcast_type'] = broadcast_type
        
        await query.edit_message_text(
            "📢 **أرسل الرسالة التي تريد إذاعتها:**\n\n"
            "يمكنك استخدام Markdown للتنسيق.\n\n"
            "✏️ أرسل الرسالة الآن:",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'waiting_broadcast'
        return WAITING_BROADCAST_MESSAGE
    
    elif data == "admin_free_services":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        sites = get_smm_sites()
        text = "🎁 **خدمات مجانية**\n\n"
        text += "المواقع:\n"
        for site in sites:
            text += f"  • ID={site[0]}: {site[1]}\n"
        text += "\n📌 لإضافة خدمة مجانية، أرسل:\n"
        text += "`الاسم|SERVICE_ID|حد_يومي|حد_أدنى|حد_أقصى|SITE_ID|الوصف|الضمان|وقت_التسليم`\n\n"
        text += "مثال: `متابعين مجانية|1234|3|100|500|1|خدمة مجانية|ضمان 30 يوم|خلال 24 ساعة`"
        
        await query.edit_message_text(
            text,
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'add_free_service'
        return WAITING_FREE_SERVICE
    
    elif data == "admin_wheel":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        await query.edit_message_text(
            "🎡 **عجلة الحظ - إدارة الجوائز**",
            reply_markup=wheel_admin_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    elif data == "wheel_add":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        await query.edit_message_text(
            "🎡 **إضافة جائزة جديدة**\n\n"
            "أرسل بهذا الشكل:\n"
            "`الاسم|النقاط|الوزن`\n\n"
            "مثال: `جائزة كبرى|1000|1`\n\n"
            "✏️ أرسل الآن:",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'add_wheel_prize'
        return WAITING_WHEEL_PRIZE
    
    elif data.startswith("wheel_delete_"):
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        prize_id = int(data.replace("wheel_delete_", ""))
        delete_wheel_prize(prize_id)
        
        await query.edit_message_text(
            "✅ تم حذف الجائزة بنجاح!",
            reply_markup=wheel_admin_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    elif data == "admin_quick_link":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        await query.edit_message_text(
            "🚀 **رابط نقاط سريع**\n\n"
            "أرسل عدد النقاط والحد الأقصى للاستخدام:\n\n"
            "`النقاط|الحد_الأقصى`\n\n"
            "مثال: `100|50`\n"
            "أو: `200|0` (بلا حد)\n\n"
            "سيتم توليد كود عشوائي تلقائياً",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'add_quick_link'
        return WAITING_QUICK_LINK
    
    elif data == "admin_invite_codes":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        await query.edit_message_text(
            "📋 **أكواد الدعوة**\n\n"
            "📌 أنشئ كود دعوة جديد\n\n"
            "أرسل عدد المستخدمين المسموح لهم بالاستخدام:",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'invite_limit'
        return WAITING_INVITE_LIMIT
    
    elif data == "admin_settings":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        support_channel = get_bot_setting("support_channel") or "غير محدد"
        updates_channel = get_bot_setting("updates_channel") or "غير محدد"
        
        text = "📢 **إعدادات البوت**\n\n"
        text += f"📌 قناة التحديثات: {updates_channel}\n"
        text += f"📌 قناة الدعم: {support_channel}\n\n"
        text += "لتغيير القنوات، أرسل:\n"
        text += "`قناة_التحديثات|قناة_الدعم`\n\n"
        text += "مثال: `@updates|@support`"
        
        await query.edit_message_text(
            text,
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'settings_channels'
        return WAITING_CHANNEL_SETTINGS
    
    elif data == "admin_add_balance":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        await query.edit_message_text(
            "➕ **إضافة رصيد**\n\n"
            "📌 أرسل ID المستخدم الذي تريد إضافة رصيد له:",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'add_balance_id'
        return WAITING_ADD_BALANCE_ID
    
    elif data == "admin_remove_balance":
        if user_id != ADMIN_ID:
            await query.edit_message_text("⛔ غير مصرح", reply_markup=back_to_main_keyboard())
            return
        
        await query.edit_message_text(
            "➖ **خصم رصيد**\n\n"
            "📌 أرسل ID المستخدم الذي تريد خصم رصيد منه:",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'remove_balance_id'
        return WAITING_REMOVE_BALANCE_ID
    
    else:
        await query.edit_message_text(
            f"✅ تم الضغط على: {data}\n\n📌 جاري التطوير...",
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )

# ===================== معالجات النصوص =====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user:
    user_id = update.effective_user.id
else:
    return
    text = update.message.text.strip()
    action = context.user_data.get('action', '')
    
    if action == 'waiting_service_link':
        service_id = context.user_data.get('service_id')
        if not service_id:
            await update.message.reply_text("❌ حدث خطأ، حاول مرة أخرى", reply_markup=back_to_main_keyboard())
            return
        
        service = get_service_by_id(service_id)
        if not service:
            await update.message.reply_text("❌ الخدمة غير موجودة", reply_markup=services_keyboard())
            return
        
        context.user_data['service_link'] = text
        min_order = service[5]
        max_order = service[6]
        
        await update.message.reply_text(
            f"✅ **تم استلام الرابط!**\n\n"
            f"🔗 الرابط: {text}\n\n"
            f"📌 **الخطوة 2:** أرسل الكمية المطلوبة\n"
            f"📊 من {min_order} إلى {max_order:,}:",
            reply_markup=service_detail_keyboard(service_id),
            parse_mode="Markdown"
        )
        context.user_data['action'] = 'waiting_service_quantity'
        return WAITING_SERVICE_QUANTITY
    
    elif action == 'waiting_service_quantity':
        try:
            quantity = int(text)
            service_id = context.user_data.get('service_id')
            service_link = context.user_data.get('service_link')
            
            if not service_id or not service_link:
                await update.message.reply_text("❌ حدث خطأ، حاول مرة أخرى", reply_markup=back_to_main_keyboard())
                return
            
            service = get_service_by_id(service_id)
            if not service:
                await update.message.reply_text("❌ الخدمة غير موجودة", reply_markup=services_keyboard())
                return
            
            min_order = service[5]
            max_order = service[6]
            
            if quantity < min_order or quantity > max_order:
                await update.message.reply_text(
                    f"❌ الكمية غير صحيحة!\n"
                    f"📊 الحد الأدنى: {min_order}\n"
                    f"📊 الحد الأقصى: {max_order:,}\n\n"
                    f"✏️ أرسل كمية صحيحة:",
                    reply_markup=service_detail_keyboard(service_id),
                    parse_mode="Markdown"
                )
                return
            
            price = service[4]
            total_price = price * quantity
            balance = get_balance(user_id)
            
            if balance < total_price:
                await update.message.reply_text(
                    f"❌ رصيدك غير كافٍ!\n"
                    f"💰 رصيدك: {balance:,} نقطة\n"
                    f"💰 المطلوب: {total_price:,} نقطة\n\n"
                    f"📌 قم بشحن رصيدك أولاً",
                    reply_markup=service_detail_keyboard(service_id),
                    parse_mode="Markdown"
                )
                return
            
            update_balance(user_id, -total_price)
            add_order(user_id, service_id, service[2], service_link, quantity, total_price)
            
            await update.message.reply_text(
                f"✅ **تم طلب الخدمة بنجاح!**\n\n"
                f"📌 الخدمة: {service[2]}\n"
                f"🔗 الرابط: {service_link}\n"
                f"📊 الكمية: {quantity}\n"
                f"💰 المبلغ المدفوع: {total_price:,} نقطة\n"
                f"💳 رصيدك المتبقي: {get_balance(user_id):,} نقطة\n\n"
                f"⏳ جاري معالجة طلبك...",
                reply_markup=services_keyboard(),
                parse_mode="Markdown"
            )
            
            context.user_data['action'] = ''
            context.user_data['service_id'] = None
            context.user_data['service_link'] = None
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text(
                "❌ يجب إرسال عدد صحيح!\n"
                "✏️ أرسل الكمية المطلوبة:",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
            return
    
    elif action == 'waiting_store_link':
        service_id = context.user_data.get('service_id')
        if not service_id:
            await update.message.reply_text("❌ حدث خطأ، حاول مرة أخرى", reply_markup=back_to_main_keyboard())
            return
        
        service = get_service_by_id(service_id)
        if not service:
            await update.message.reply_text("❌ الخدمة غير موجودة", reply_markup=store_services_keyboard())
            return
        
        price = service[4]
        smm_site_id = service[8]
        smm_service_id = service[9]
        
        if not smm_site_id or not smm_service_id:
            await update.message.reply_text(
                "❌ هذه الخدمة غير متصلة بـ SMM\n"
                "📌 يرجى التواصل مع الدعم",
                reply_markup=store_services_keyboard()
            )
            return
        
        balance = get_balance(user_id)
        if balance < price:
            await update.message.reply_text(
                f"❌ رصيدك غير كافٍ!\n"
                f"💰 رصيدك: {balance:,} نقطة\n"
                f"💰 سعر الخدمة: {price} نقطة",
                reply_markup=store_services_keyboard()
            )
            return
        
        result = await smm_order(int(smm_site_id), smm_service_id, text, 1)
        
        if result and 'order' in result:
            smm_order_id = result['order']
            add_order(user_id, service_id, service[2], text, 1, price, smm_order_id)
            update_balance(user_id, -price)
            
            await update.message.reply_text(
                f"✅ **تم طلب الخدمة بنجاح!**\n\n"
                f"📌 الخدمة: {service[2]}\n"
                f"🔗 الرابط: {text}\n"
                f"🆔 رقم الطلب: {smm_order_id}\n"
                f"💰 تم خصم: {price} نقطة\n\n"
                f"⏳ جاري تنفيذ الطلب...",
                reply_markup=store_services_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"❌ حدث خطأ في تنفيذ الطلب\n"
                f"📌 يرجى المحاولة مرة أخرى أو التواصل مع الدعم",
                reply_markup=store_services_keyboard()
            )
        
        context.user_data['action'] = ''
        context.user_data['service_id'] = None
        return ConversationHandler.END
    
    elif action == 'charge_stars':
        try:
            stars = int(text)
            if stars <= 0:
                await update.message.reply_text("❌ يجب أن يكون عدد النجوم أكبر من 0")
                return
            
            if stars == 1:
                points = 100
            elif stars == 5:
                points = 550
            elif stars == 10:
                points = 1200
            else:
                points = stars * 100
            
            update_balance(user_id, points)
            await update.message.reply_text(
                f"⭐ **تم الشحن بنجاح!**\n\n"
                f"💰 تم إضافة {points} نقطة\n"
                f"💳 رصيدك الحالي: {get_balance(user_id):,} نقطة",
                reply_markup=main_menu_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = ''
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("❌ أرسل عدد صحيح!")
            return
    
    elif action == 'charge_cash':
        try:
            amount = int(text)
            if amount <= 0:
                await update.message.reply_text("❌ يجب أن يكون المبلغ أكبر من 0")
                return
            
            if amount == 10:
                points = 1000
            elif amount == 50:
                points = 5500
            elif amount == 100:
                points = 12000
            else:
                points = amount * 100
            
            update_balance(user_id, points)
            await update.message.reply_text(
                f"💳 **تم الشحن بنجاح!**\n\n"
                f"💰 تم إضافة {points} نقطة\n"
                f"💳 رصيدك الحالي: {get_balance(user_id):,} نقطة\n\n"
                f"📌 للمتابعة تواصل مع الدعم: @TeleRaiseSupport",
                reply_markup=main_menu_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = ''
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("❌ أرسل مبلغ صحيح!")
            return
    
    elif action == 'sell_number':
        await update.message.reply_text(
            "💰 **بيع رقم**\n\n"
            f"📌 تم استلام رقمك: {text}\n"
            "⏳ جاري التحقق من الرقم...\n\n"
            "📌 هذه الخدمة قيد التطوير",
            reply_markup=collect_points_keyboard(),
            parse_mode="Markdown"
        )
        context.user_data['action'] = ''
        return ConversationHandler.END
    
    elif action == 'transfer_id':
        try:
            target_id = int(text)
            context.user_data['transfer_target'] = target_id
            await update.message.reply_text(
                "🔄 **تحويل نقاط**\n\n"
                f"📌 تم تحديد المستخدم: {target_id}\n"
                f"💰 رصيدك: {get_balance(user_id):,} نقطة\n\n"
                "✏️ أرسل عدد النقاط للتحويل:",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = 'transfer_amount'
            return WAITING_TRANSFER_AMOUNT
        except ValueError:
            await update.message.reply_text("❌ أرسل ID صحيح!")
            return
    
    elif action == 'transfer_amount':
        try:
            amount = int(text)
            target_id = context.user_data.get('transfer_target')
            if not target_id:
                await update.message.reply_text("❌ حدث خطأ، حاول مرة أخرى")
                return
            
            balance = get_balance(user_id)
            if amount > balance:
                await update.message.reply_text(f"❌ رصيدك غير كافٍ! رصيدك: {balance:,} نقطة")
                return
            
            update_balance(user_id, -amount)
            update_balance(target_id, amount)
            
            await update.message.reply_text(
                f"✅ **تم التحويل بنجاح!**\n\n"
                f"💰 تم تحويل {amount:,} نقطة للمستخدم {target_id}\n"
                f"💳 رصيدك الحالي: {get_balance(user_id):,} نقطة",
                reply_markup=main_menu_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = ''
            context.user_data['transfer_target'] = None
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text("❌ أرسل عدد صحيح!")
            return
    
    elif action == 'use_code':
        code = text.strip().upper()
        if code == "TEST100":
            update_balance(user_id, 100)
            await update.message.reply_text(
                f"🎫 **تم استخدام الكود بنجاح!**\n\n"
                f"💰 تم إضافة 100 نقطة\n"
                f"💳 رصيدك الحالي: {get_balance(user_id):,} نقطة",
                reply_markup=main_menu_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "❌ الكود غير صحيح!\n"
                "📌 تأكد من الكود وحاول مرة أخرى",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
        context.user_data['action'] = ''
        return ConversationHandler.END
    
    elif action == 'waiting_broadcast':
        if user_id != ADMIN_ID:
            await update.message.reply_text("⛔ غير مصرح")
            return
        
        broadcast_type = context.user_data.get('broadcast_type', 'all')
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        if broadcast_type == 'all':
            c.execute("SELECT user_id FROM users")
        elif broadcast_type == 'inactive':
            seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
            c.execute("SELECT user_id FROM users WHERE user_id NOT IN (SELECT DISTINCT user_id FROM orders WHERE created_at > ?)", (seven_days_ago,))
        elif broadcast_type == 'low_balance':
            c.execute("SELECT user_id FROM users WHERE balance < 50")
        else:
            c.execute("SELECT user_id FROM users")
        
        users = c.fetchall()
        conn.close()
        
        sent_count = 0
        for user in users:
            try:
                await update.message.bot.send_message(
                    chat_id=user[0],
                    text=text,
                    parse_mode="Markdown"
                )
                sent_count += 1
            except:
                pass
        
        await update.message.reply_text(
            f"✅ **تم إرسال الإذاعة!**\n\n"
            f"📊 تم الإرسال إلى: {sent_count} مستخدم\n"
            f"📝 الرسالة: {text[:100]}...",
            reply_markup=back_to_main_keyboard(),
            parse_mode="Markdown"
        )
        
        context.user_data['action'] = ''
        return ConversationHandler.END
    
    elif action == 'add_service':
        if user_id != ADMIN_ID:
            await update.message.reply_text("⛔ غير مصرح")
            return
        
        try:
            parts = text.split('|')
            if len(parts) != 8:
                await update.message.reply_text(
                    "❌ صيغة غير صحيحة!\n"
                    "أرسل: `الاسم|الايقونة|السعر|الحد_الأدنى|الحد_الأقصى|الوصف|الضمان|وقت_التسليم`",
                    reply_markup=back_to_main_keyboard(),
                    parse_mode="Markdown"
                )
                return
            
            name = parts[0].strip()
            icon = parts[1].strip()
            price = int(parts[2].strip())
            min_order = int(parts[3].strip())
            max_order = int(parts[4].strip())
            description = parts[5].strip()
            guarantee = parts[6].strip() if parts[6].strip() else "ضمان البوت"
            delivery_time = parts[7].strip() if parts[7].strip() else "خلال 24 ساعة"
            
            section_name = context.user_data.get('section_name')
            if not section_name:
                await update.message.reply_text(
                    "❌ حدث خطأ! الرجاء المحاولة مرة أخرى.",
                    reply_markup=back_to_main_keyboard()
                )
                return
            
            add_service(section_name, name, icon, price, min_order, max_order, description, None, None, 0, 0, 0, guarantee, delivery_time)
            
            await update.message.reply_text(
                f"✅ **تم إضافة الخدمة بنجاح!**\n\n"
                f"📂 القسم: {section_name}\n"
                f"📌 الاسم: {name}\n"
                f"🖼️ الايقونة: {icon}\n"
                f"💰 السعر: {price} نقطة\n"
                f"📉 الحد الأدنى: {min_order}\n"
                f"📈 الحد الأقصى: {max_order}\n"
                f"📝 الوصف: {description}\n"
                f"🛡️ الضمان: {guarantee}\n"
                f"⏱️ وقت التسليم: {delivery_time}",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = ''
            context.user_data['section_name'] = None
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text(
                "❌ السعر والحدود يجب أن تكون أرقاماً!",
                reply_markup=back_to_main_keyboard()
            )
            return
        except Exception as e:
            await update.message.reply_text(
                f"❌ حدث خطأ: {str(e)}",
                reply_markup=back_to_main_keyboard()
            )
            return
    
    elif action == 'add_store_service':
        if user_id != ADMIN_ID:
            await update.message.reply_text("⛔ غير مصرح")
            return
        
        try:
            parts = text.split('|')
            if len(parts) != 9:
                await update.message.reply_text(
                    "❌ صيغة غير صحيحة!\n"
                    "أرسل: `الاسم|الايقونة|السعر|الحد_الأدنى|الحد_الأقصى|الوصف|الضمان|وقت_التسليم|SITE_ID`",
                    reply_markup=back_to_main_keyboard(),
                    parse_mode="Markdown"
                )
                return
            
            name = parts[0].strip()
            icon = parts[1].strip()
            price = int(parts[2].strip())
            min_order = int(parts[3].strip())
            max_order = int(parts[4].strip())
            description = parts[5].strip()
            guarantee = parts[6].strip() if parts[6].strip() else "ضمان البوت"
            delivery_time = parts[7].strip() if parts[7].strip() else "خلال 24 ساعة"
            service_id = parts[8].strip()
            
            active_site = get_active_smm_site()
            site_name = active_site[1] if active_site else None
            
            add_service("المتجر", name, icon, price, min_order, max_order, description, service_id, site_name, 0, 0, 1, guarantee, delivery_time)
            
            await update.message.reply_text(
                f"✅ **تم إضافة الخدمة في المتجر بنجاح!**\n\n"
                f"📌 الاسم: {name}\n"
                f"🖼️ الايقونة: {icon}\n"
                f"💰 السعر: {price} نقطة\n"
                f"📉 الحد الأدنى: {min_order}\n"
                f"📈 الحد الأقصى: {max_order}\n"
                f"📝 الوصف: {description}\n"
                f"🛡️ الضمان: {guarantee}\n"
                f"⏱️ وقت التسليم: {delivery_time}\n"
                f"🆔 SITE_ID: {service_id}",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = ''
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text(
                "❌ السعر والحدود يجب أن تكون أرقاماً!",
                reply_markup=back_to_main_keyboard()
            )
            return
        except Exception as e:
            await update.message.reply_text(
                f"❌ حدث خطأ: {str(e)}",
                reply_markup=back_to_main_keyboard()
            )
            return
    
    elif action == 'add_free_service':
        if user_id != ADMIN_ID:
            await update.message.reply_text("⛔ غير مصرح")
            return
        
        try:
            parts = text.split('|')
            if len(parts) != 9:
                await update.message.reply_text(
                    "❌ صيغة غير صحيحة!\n"
                    "أرسل: `الاسم|SERVICE_ID|حد_يومي|حد_أدنى|حد_أقصى|SITE_ID|الوصف|الضمان|وقت_التسليم`",
                    reply_markup=back_to_main_keyboard(),
                    parse_mode="Markdown"
                )
                return
            
            name = parts[0].strip()
            service_id = parts[1].strip()
            daily_limit = int(parts[2].strip())
            min_order = int(parts[3].strip())
            max_order = int(parts[4].strip())
            site_id = int(parts[5].strip())
            description = parts[6].strip()
            guarantee = parts[7].strip() if parts[7].strip() else "ضمان البوت"
            delivery_time = parts[8].strip() if parts[8].strip() else "خلال 24 ساعة"
            
            sites = get_smm_sites()
            site_name = "SMMSite"
            for site in sites:
                if site[0] == site_id:
                    site_name = site[1]
                    break
            
            add_service("خدمات مجانية", name, "🎁", 0, min_order, max_order, description, service_id, site_name, 1, daily_limit, 0, guarantee, delivery_time)
            
            await update.message.reply_text(
                f"✅ **تم إضافة الخدمة المجانية بنجاح!**\n\n"
                f"📌 الاسم: {name}\n"
                f"🆔 SERVICE_ID: {service_id}\n"
                f"📉 الحد الأدنى: {min_order}\n"
                f"📈 الحد الأقصى: {max_order}\n"
                f"📅 الحد اليومي: {daily_limit}\n"
                f"🌐 الموقع: {site_name}\n"
                f"📝 الوصف: {description}\n"
                f"🛡️ الضمان: {guarantee}\n"
                f"⏱️ وقت التسليم: {delivery_time}",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = ''
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text(
                "❌ يجب أن تكون الأرقام صحيحة!",
                reply_markup=back_to_main_keyboard()
            )
            return
        except Exception as e:
            await update.message.reply_text(
                f"❌ حدث خطأ: {str(e)}",
                reply_markup=back_to_main_keyboard()
            )
            return
    
    elif action == 'add_wheel_prize':
        if user_id != ADMIN_ID:
            await update.message.reply_text("⛔ غير مصرح")
            return
        
        try:
            parts = text.split('|')
            if len(parts) != 3:
                await update.message.reply_text(
                    "❌ صيغة غير صحيحة!\n"
                    "أرسل: `الاسم|النقاط|الوزن`",
                    reply_markup=back_to_main_keyboard(),
                    parse_mode="Markdown"
                )
                return
            
            name = parts[0].strip()
            points = int(parts[1].strip())
            weight = int(parts[2].strip())
            
            add_wheel_prize(name, points, weight)
            
            await update.message.reply_text(
                f"✅ **تم إضافة الجائزة بنجاح!**\n\n"
                f"📌 الاسم: {name}\n"
                f"💰 النقاط: {points}\n"
                f"⚖️ الوزن: {weight}",
                reply_markup=wheel_admin_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = ''
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text(
                "❌ يجب أن تكون النقاط والوزن أرقاماً صحيحة!",
                reply_markup=back_to_main_keyboard()
            )
            return
        except Exception as e:
            await update.message.reply_text(
                f"❌ حدث خطأ: {str(e)}",
                reply_markup=back_to_main_keyboard()
            )
            return
    
    elif action == 'add_quick_link':
        if user_id != ADMIN_ID:
            await update.message.reply_text("⛔ غير مصرح")
            return
        
        try:
            parts = text.split('|')
            if len(parts) != 2:
                await update.message.reply_text(
                    "❌ صيغة غير صحيحة!\n"
                    "أرسل: `النقاط|الحد_الأقصى`",
                    reply_markup=back_to_main_keyboard(),
                    parse_mode="Markdown"
                )
                return
            
            points = int(parts[0].strip())
            max_uses = int(parts[1].strip())
            
            code = generate_random_code(10)
            add_quick_link(code, points, max_uses)
            
            bot_username = (await update.message.bot.get_me()).username
            
            await update.message.reply_text(
                f"🎁 **تم إنشاء رابط الهدية!**\n\n"
                f"📌 **الكود:** `{code}`\n"
                f"💰 **النقاط:** {points}\n"
                f"📊 **الحد الأقصى:** {max_uses if max_uses > 0 else 'غير محدود'}\n\n"
                f"🔗 **الرابط:**\n"
                f"`https://t.me/{bot_username}?start=gift_{code}`\n\n"
                f"📌 سيصلك إشعار كلما استخدم أحد هذا الرابط",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = ''
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text(
                "❌ يجب أن تكون النقاط والحد الأقصى أرقاماً صحيحة!",
                reply_markup=back_to_main_keyboard()
            )
            return
        except Exception as e:
            await update.message.reply_text(
                f"❌ حدث خطأ: {str(e)}",
                reply_markup=back_to_main_keyboard()
            )
            return
    
    elif action == 'invite_limit':
        if user_id != ADMIN_ID:
            await update.message.reply_text("⛔ غير مصرح")
            return
        
        try:
            max_users = int(text)
            context.user_data['invite_max_users'] = max_users
            
            await update.message.reply_text(
                "📋 **أرسل عدد النقاط لكل مستخدم:**",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = 'invite_points'
            return WAITING_INVITE_POINTS
            
        except ValueError:
            await update.message.reply_text(
                "❌ يجب إرسال رقم صحيح!",
                reply_markup=back_to_main_keyboard()
            )
            return
    
    elif action == 'invite_points':
        if user_id != ADMIN_ID:
            await update.message.reply_text("⛔ غير مصرح")
            return
        
        try:
            points = int(text)
            max_users = context.user_data.get('invite_max_users', 0)
            
            code = generate_random_code(8)
            add_invite_code(code, points, max_users, user_id)
            
            bot_username = (await update.message.bot.get_me()).username
            
            await update.message.reply_text(
                f"🎁 **تم إنشاء كود الدعوة!**\n\n"
                f"📌 **الكود:** `{code}`\n"
                f"💰 **النقاط:** {points}\n"
                f"👥 **عدد المستخدمين:** {max_users}\n\n"
                f"🔗 **الرابط:**\n"
                f"`https://t.me/{bot_username}?start=invite_{code}`",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = ''
            context.user_data['invite_max_users'] = None
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text(
                "❌ يجب إرسال رقم صحيح!",
                reply_markup=back_to_main_keyboard()
            )
            return
        except Exception as e:
            await update.message.reply_text(
                f"❌ حدث خطأ: {str(e)}",
                reply_markup=back_to_main_keyboard()
            )
            return
    
    elif action == 'settings_channels':
        if user_id != ADMIN_ID:
            await update.message.reply_text("⛔ غير مصرح")
            return
        
        try:
            parts = text.split('|')
            if len(parts) != 2:
                await update.message.reply_text(
                    "❌ صيغة غير صحيحة!\n"
                    "أرسل: `قناة_التحديثات|قناة_الدعم`",
                    reply_markup=back_to_main_keyboard(),
                    parse_mode="Markdown"
                )
                return
            
            updates_channel = parts[0].strip()
            support_channel = parts[1].strip()
            
            set_bot_setting("updates_channel", updates_channel)
            set_bot_setting("support_channel", support_channel)
            
            await update.message.reply_text(
                f"✅ **تم تحديث الإعدادات!**\n\n"
                f"📌 قناة التحديثات: {updates_channel}\n"
                f"📌 قناة الدعم: {support_channel}",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = ''
            return ConversationHandler.END
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ حدث خطأ: {str(e)}",
                reply_markup=back_to_main_keyboard()
            )
            return
    
    elif action == 'add_section':
        try:
            parts = text.split('|')
            if len(parts) != 2:
                await update.message.reply_text(
                    "❌ صيغة غير صحيحة!\n"
                    "أرسل بهذا الشكل: `الاسم|الايقونة`\n"
                    "مثال: `تيك توك|📱`",
                    reply_markup=back_to_main_keyboard(),
                    parse_mode="Markdown"
                )
                return
            
            name = parts[0].strip()
            icon = parts[1].strip()
            add_section(name, icon)
            
            await update.message.reply_text(
                f"✅ تم إضافة القسم بنجاح!\n\n"
                f"📌 الاسم: {name}\n"
                f"🖼️ الايقونة: {icon}",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = ''
            return ConversationHandler.END
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ حدث خطأ: {str(e)}",
                reply_markup=back_to_main_keyboard()
            )
            return
    
    elif action == 'add_points_channel':
        try:
            parts = text.split('|')
            if len(parts) != 4:
                await update.message.reply_text(
                    "❌ صيغة غير صحيحة!\n"
                    "أرسل بهذا الشكل: `channel_id|الاسم|الرابط|النقاط`\n"
                    "مثال: `-1001234567890|قناة النقاط|https://t.me/channel|50`",
                    reply_markup=back_to_main_keyboard(),
                    parse_mode="Markdown"
                )
                return
            
            channel_id = parts[0].strip()
            name = parts[1].strip()
            link = parts[2].strip()
            points = int(parts[3].strip())
            
            add_points_channel(channel_id, name, link, points)
            
            await update.message.reply_text(
                f"✅ تم إضافة قناة النقاط بنجاح!\n\n"
                f"🆔 المعرف: {channel_id}\n"
                f"📌 الاسم: {name}\n"
                f"🔗 الرابط: {link}\n"
                f"💰 النقاط: {points}",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = ''
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text(
                "❌ يجب أن تكون النقاط رقماً صحيحاً!",
                reply_markup=back_to_main_keyboard()
            )
            return
        except Exception as e:
            await update.message.reply_text(
                f"❌ حدث خطأ: {str(e)}",
                reply_markup=back_to_main_keyboard()
            )
            return
    
    elif action == 'add_forced_channel':
        try:
            parts = text.split('|')
            if len(parts) != 3:
                await update.message.reply_text(
                    "❌ صيغة غير صحيحة!\n"
                    "أرسل بهذا الشكل: `channel_id|الاسم|الرابط`\n"
                    "مثال: `-1001234567890|قناة إجباري|https://t.me/channel`",
                    reply_markup=back_to_main_keyboard(),
                    parse_mode="Markdown"
                )
                return
            
            channel_id = parts[0].strip()
            name = parts[1].strip()
            link = parts[2].strip()
            
            add_forced_channel(channel_id, name, link)
            
            await update.message.reply_text(
                f"✅ تم إضافة القناة الإجبارية بنجاح!\n\n"
                f"🆔 المعرف: {channel_id}\n"
                f"📌 الاسم: {name}\n"
                f"🔗 الرابط: {link}",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = ''
            return ConversationHandler.END
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ حدث خطأ: {str(e)}",
                reply_markup=back_to_main_keyboard()
            )
            return
    
    elif action == 'add_smm_site':
        try:
            parts = text.split('|')
            if len(parts) != 3:
                await update.message.reply_text(
                    "❌ صيغة غير صحيحة!\n"
                    "أرسل بهذا الشكل: `الاسم|API_URL|API_KEY`\n"
                    "مثال: `SMMParty|https://smmparty.com/api/v2|YOUR_KEY`",
                    reply_markup=back_to_main_keyboard(),
                    parse_mode="Markdown"
                )
                return
            
            name = parts[0].strip()
            api_url = parts[1].strip()
            api_key = parts[2].strip()
            
            add_smm_site(name, api_url, api_key)
            
            sites = get_smm_sites()
            if sites:
                set_active_smm_site(sites[0][0])
            
            await update.message.reply_text(
                f"✅ تم إضافة موقع SMM بنجاح!\n\n"
                f"📌 الاسم: {name}\n"
                f"🔗 API URL: {api_url}\n"
                f"🔑 API KEY: {api_key[:10]}...\n\n"
                f"✅ تم تفعيل الموقع تلقائياً!",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = ''
            return ConversationHandler.END
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ حدث خطأ: {str(e)}",
                reply_markup=back_to_main_keyboard()
            )
            return
    
    elif action == 'add_orders_channel':
        try:
            parts = text.split('|')
            if len(parts) != 2:
                await update.message.reply_text(
                    "❌ صيغة غير صحيحة!\n"
                    "أرسل بهذا الشكل: `channel_id|الاسم`\n"
                    "مثال: `-1001234567890|طلبات البوت`",
                    reply_markup=back_to_main_keyboard(),
                    parse_mode="Markdown"
                )
                return
            
            channel_id = parts[0].strip()
            name = parts[1].strip()
            
            add_orders_channel(channel_id, name)
            
            await update.message.reply_text(
                f"✅ تم إضافة قناة الطلبات بنجاح!\n\n"
                f"🆔 المعرف: {channel_id}\n"
                f"📌 الاسم: {name}",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = ''
            return ConversationHandler.END
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ حدث خطأ: {str(e)}",
                reply_markup=back_to_main_keyboard()
            )
            return
    
    elif action == 'add_log_channel':
        try:
            parts = text.split('|')
            if len(parts) != 2:
                await update.message.reply_text(
                    "❌ صيغة غير صحيحة!\n"
                    "أرسل بهذا الشكل: `channel_id|الاسم`\n"
                    "مثال: `-1001234567890|قناة السجل`",
                    reply_markup=back_to_main_keyboard(),
                    parse_mode="Markdown"
                )
                return
            
            channel_id = parts[0].strip()
            name = parts[1].strip()
            
            add_log_channel(channel_id, name)
            
            await update.message.reply_text(
                f"✅ تم إضافة قناة السجل بنجاح!\n\n"
                f"🆔 المعرف: {channel_id}\n"
                f"📌 الاسم: {name}\n\n"
                f"⚠️ تأكد من أن البوت أدمن في القناة وله صلاحية نشر الرسائل",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = ''
            return ConversationHandler.END
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ حدث خطأ: {str(e)}",
                reply_markup=back_to_main_keyboard()
            )
            return
    
    elif action == 'search_user':
        try:
            search_id = int(text)
            user = get_user_by_id(search_id)
            
            if not user:
                await update.message.reply_text(
                    f"❌ لا يوجد مستخدم بهذا ID: {search_id}",
                    reply_markup=back_to_main_keyboard(),
                    parse_mode="Markdown"
                )
                return
            
            text_msg = f"👤 **معلومات المستخدم**\n\n"
            text_msg += f"🆔 المعرف: {user[0]}\n"
            text_msg += f"📛 الاسم: {user[2]}\n"
            text_msg += f"👤 اليوزر: @{user[1] or 'غير معروف'}\n"
            text_msg += f"💰 الرصيد: {user[3]} نقطة\n"
            text_msg += f"✅ الطلبات المكتملة: {user[5]}\n"
            text_msg += f"📅 تاريخ الانضمام: {user[4][:16]}\n"
            if user[6]:
                text_msg += f"🎁 آخر هدية يومية: {user[6]}\n"
            if user[7]:
                text_msg += f"🔗 تمت الدعوة بواسطة: {user[7]}\n"
            
            await update.message.reply_text(
                text_msg,
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = ''
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text(
                "❌ يجب إرسال ID رقمي صحيح!",
                reply_markup=back_to_main_keyboard()
            )
            return
        except Exception as e:
            await update.message.reply_text(
                f"❌ حدث خطأ: {str(e)}",
                reply_markup=back_to_main_keyboard()
            )
            return
    
    elif action == 'add_balance_id':
        if user_id != ADMIN_ID:
            await update.message.reply_text("⛔ غير مصرح")
            return
        
        try:
            target_id = int(text)
            user = get_user_by_id(target_id)
            if not user:
                await update.message.reply_text(
                    f"❌ لا يوجد مستخدم بهذا ID: {target_id}",
                    reply_markup=back_to_main_keyboard()
                )
                return
            
            context.user_data['add_balance_target'] = target_id
            await update.message.reply_text(
                f"✅ تم تحديد المستخدم: {user[2] or user[1] or target_id}\n\n"
                f"💰 رصيده الحالي: {user[3]} نقطة\n\n"
                f"✏️ أرسل عدد النقاط للإضافة:",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = 'add_balance_amount'
            return WAITING_ADD_BALANCE_AMOUNT
            
        except ValueError:
            await update.message.reply_text("❌ أرسل ID رقمي صحيح!")
            return
    
    elif action == 'add_balance_amount':
        if user_id != ADMIN_ID:
            await update.message.reply_text("⛔ غير مصرح")
            return
        
        try:
            amount = int(text)
            if amount <= 0:
                await update.message.reply_text("❌ يجب أن يكون المبلغ أكبر من 0")
                return
            
            target_id = context.user_data.get('add_balance_target')
            if not target_id:
                await update.message.reply_text("❌ حدث خطأ، حاول مرة أخرى")
                return
            
            update_balance(target_id, amount)
            user = get_user_by_id(target_id)
            
            await update.message.reply_text(
                f"✅ **تم إضافة الرصيد بنجاح!**\n\n"
                f"👤 المستخدم: {user[2] or user[1] or target_id}\n"
                f"💰 تم إضافة: {amount:,} نقطة\n"
                f"💳 الرصيد الجديد: {user[3]} نقطة",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = ''
            context.user_data['add_balance_target'] = None
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text("❌ أرسل عدد صحيح!")
            return
    
    elif action == 'remove_balance_id':
        if user_id != ADMIN_ID:
            await update.message.reply_text("⛔ غير مصرح")
            return
        
        try:
            target_id = int(text)
            user = get_user_by_id(target_id)
            if not user:
                await update.message.reply_text(
                    f"❌ لا يوجد مستخدم بهذا ID: {target_id}",
                    reply_markup=back_to_main_keyboard()
                )
                return
            
            context.user_data['remove_balance_target'] = target_id
            await update.message.reply_text(
                f"✅ تم تحديد المستخدم: {user[2] or user[1] or target_id}\n\n"
                f"💰 رصيده الحالي: {user[3]} نقطة\n\n"
                f"✏️ أرسل عدد النقاط للخصم:",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = 'remove_balance_amount'
            return WAITING_REMOVE_BALANCE_AMOUNT
            
        except ValueError:
            await update.message.reply_text("❌ أرسل ID رقمي صحيح!")
            return
    
    elif action == 'remove_balance_amount':
        if user_id != ADMIN_ID:
            await update.message.reply_text("⛔ غير مصرح")
            return
        
        try:
            amount = int(text)
            if amount <= 0:
                await update.message.reply_text("❌ يجب أن يكون المبلغ أكبر من 0")
                return
            
            target_id = context.user_data.get('remove_balance_target')
            if not target_id:
                await update.message.reply_text("❌ حدث خطأ، حاول مرة أخرى")
                return
            
            current_balance = get_balance(target_id)
            if amount > current_balance:
                await update.message.reply_text(
                    f"❌ الرصيد غير كافٍ!\n"
                    f"💰 رصيد المستخدم: {current_balance} نقطة\n"
                    f"📌 المبلغ المطلوب خصمه: {amount} نقطة",
                    reply_markup=back_to_main_keyboard()
                )
                return
            
            update_balance(target_id, -amount)
            user = get_user_by_id(target_id)
            
            await update.message.reply_text(
                f"✅ **تم خصم الرصيد بنجاح!**\n\n"
                f"👤 المستخدم: {user[2] or user[1] or target_id}\n"
                f"💰 تم خصم: {amount:,} نقطة\n"
                f"💳 الرصيد الجديد: {user[3]} نقطة",
                reply_markup=back_to_main_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['action'] = ''
            context.user_data['remove_balance_target'] = None
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text("❌ أرسل عدد صحيح!")
            return

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 البوت شغال...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()