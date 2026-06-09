import os
import json
import random
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from functools import wraps

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, UserNotParticipant
import pyromod
from pyromod.listen import Client as ListenClient
from peewee import *

# ----------------------------- قاعدة البيانات -----------------------------
db = SqliteDatabase('smm_bot.db')

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    user_id = BigIntegerField(unique=True)
    username = CharField(null=True)
    first_name = CharField()
    last_name = CharField(null=True)
    balance = FloatField(default=0.0)
    referred_by = BigIntegerField(null=True)
    referral_code = CharField(unique=True)
    is_banned = BooleanField(default=False)
    is_admin = BooleanField(default=False)
    joined_date = DateTimeField(default=datetime.now)
    
class Transaction(BaseModel):
    user_id = BigIntegerField()
    amount = FloatField()
    type = CharField()  # 'deposit', 'withdraw', 'referral', 'daily', 'order'
    description = CharField()
    date = DateTimeField(default=datetime.now)
    
class Order(BaseModel):
    order_id = CharField(unique=True)
    user_id = BigIntegerField()
    service = CharField()
    quantity = IntegerField()
    cost = FloatField()
    status = CharField(default='pending')  # pending, processing, completed, cancelled
    target = CharField(null=True)
    provider_order_id = CharField(null=True)  # معرف الطلب في موقع الرشق
    provider_response = TextField(null=True)  # استجابة API كاملة
    provider_id = IntegerField(null=True)  # الموقع المستخدم
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
class Service(BaseModel):
    name = CharField(unique=True)
    description = CharField()
    price_per_unit = FloatField()
    min_quantity = IntegerField(default=1)
    max_quantity = IntegerField(default=10000)
    is_active = BooleanField(default=True)
    api_service_id = CharField(null=True)  # معرف الخدمة في موقع الرشق
    provider_id = IntegerField(null=True)  # الموقع التابع له
    
class Broadcast(BaseModel):
    broadcast_id = CharField(unique=True)
    message = TextField()
    total_sent = IntegerField(default=0)
    total_failed = IntegerField(default=0)
    status = CharField(default='pending')
    created_at = DateTimeField(default=datetime.now)
    completed_at = DateTimeField(null=True)
    
class Provider(BaseModel):
    name = CharField(unique=True)  # اسم الموقع (مثل: رشق1، رشق2)
    api_url = CharField()  # رابط API الثابت
    api_key = CharField()  # مفتاح API الخاص
    is_active = BooleanField(default=True)  # هل الموقع مفعل
    created_at = DateTimeField(default=datetime.now)
    
class BotSettings(BaseModel):
    key = CharField(unique=True)
    value = TextField()
    
    @classmethod
    def get_setting(cls, key, default=None):
        try:
            return cls.get(cls.key == key).value
        except cls.DoesNotExist:
            return default
            
    @classmethod
    def set_setting(cls, key, value):
        setting, created = cls.get_or_create(key=key, defaults={'value': value})
        if not created:
            setting.value = value
            setting.save()
        return setting

# إنشاء الجداول
db.connect()
db.create_tables([User, Transaction, Order, Service, Broadcast, Provider, BotSettings], safe=True)

# ----------------------------- الإعدادات -----------------------------
BOT_TOKEN = "8555009710:AAGa3vvjR-Xq7o6mlZWzHrFwGKpznu0CQ6k"
ADMIN_IDS = [6640098641]

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ----------------------------- دوال API للمواقع المتعددة -----------------------------
async def provider_api_request(provider: Provider, endpoint: str, method: str = 'POST', data: dict = None) -> dict:
    """إرسال طلب إلى API موقع محدد"""
    if not provider.is_active:
        return {'error': f'الموقع {provider.name} غير نشط', 'success': False}
    
    headers = {
        'Authorization': f'Bearer {provider.api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    full_url = provider.api_url.rstrip('/') + '/' + endpoint.lstrip('/')
    
    async with aiohttp.ClientSession() as session:
        try:
            if method.upper() == 'GET':
                async with session.get(full_url, headers=headers, params=data) as resp:
                    return await resp.json()
            else:
                async with session.post(full_url, headers=headers, json=data) as resp:
                    return await resp.json()
        except Exception as e:
            logger.error(f"API Request Error for {provider.name}: {e}")
            return {'error': str(e), 'success': False}

async def create_order_on_provider(provider: Provider, service_id: str, quantity: int, link: str, user_id: int) -> dict:
    """إنشاء طلب في موقع معين"""
    data = {
        'service': service_id,
        'quantity': quantity,
        'link': link,
        'user_id': str(user_id)
    }
    return await provider_api_request(provider, 'api/order', 'POST', data)

async def check_order_status_on_provider(provider: Provider, order_id: str) -> dict:
    """الاستعلام عن حالة طلب من موقع معين"""
    return await provider_api_request(provider, f'api/order/{order_id}', 'GET')

async def get_services_from_provider(provider: Provider) -> dict:
    """جلب قائمة الخدمات من موقع معين"""
    return await provider_api_request(provider, 'api/services', 'GET')

async def update_order_status_from_provider(order: Order):
    """تحديث حالة طلب محلي بناءً على API الموقع المستخدم"""
    if not order.provider_id or not order.provider_order_id:
        return
    
    provider = Provider.get_or_none(Provider.id == order.provider_id)
    if not provider or not provider.is_active:
        return
    
    result = await check_order_status_on_provider(provider, order.provider_order_id)
    if result and result.get('success', False):
        api_status = result.get('status', '')
        status_map = {
            'pending': 'pending',
            'processing': 'processing',
            'completed': 'completed',
            'cancelled': 'cancelled',
            'partial': 'processing',
            'error': 'cancelled'
        }
        new_status = status_map.get(api_status, order.status)
        if new_status != order.status:
            order.status = new_status
            order.updated_at = datetime.now()
            order.save()
            # إخطار المستخدم
            try:
                await app.send_message(
                    order.user_id,
                    f"🔄 تحديث حالة الطلب `{order.order_id}`\n"
                    f"الحالة الجديدة: {new_status}\n"
                    f"الخدمة: {order.service}\n"
                    f"الكمية: {order.quantity}"
                )
            except:
                pass

# ----------------------------- الديكورات المساعدة -----------------------------
def admin_only(func):
    @wraps(func)
    async def wrapper(client: Client, message: Message):
        user_id = message.from_user.id
        user = User.get_or_none(User.user_id == user_id)
        if user_id in ADMIN_IDS or (user and user.is_admin):
            return await func(client, message)
        else:
            await message.reply_text("⛔ عذراً، هذا الأمر متاح للمشرفين فقط.")
    return wrapper

def require_user(func):
    @wraps(func)
    async def wrapper(client: Client, message: Message):
        user = message.from_user
        if User.get_or_none(User.user_id == user.id) is None:
            ref_code = None
            if message.command and len(message.command) > 1:
                ref_arg = message.command[1]
                if ref_arg and ref_arg.startswith('ref_'):
                    referrer = User.get_or_none(User.referral_code == ref_arg)
                    if referrer and referrer.user_id != user.id:
                        ref_code = referrer.user_id
            unique_code = f"ref_{user.id}_{random.randint(1000, 9999)}"
            User.create(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                referred_by=ref_code,
                referral_code=unique_code
            )
            if ref_code:
                referrer = User.get(User.user_id == ref_code)
                referrer.balance += 5
                referrer.save()
                Transaction.create(
                    user_id=ref_code,
                    amount=5,
                    type='referral',
                    description=f'إحالة مستخدم جديد (ID: {user.id})'
                )
        return await func(client, message)
    return wrapper

# ----------------------------- دوال مساعدة -----------------------------
def generate_unique_id():
    return f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"

def get_user_balance(user_id: int) -> float:
    user = User.get_or_none(User.user_id == user_id)
    return user.balance if user else 0.0

def add_to_balance(user_id: int, amount: float, description: str = ""):
    user = User.get_or_none(User.user_id == user_id)
    if user:
        user.balance += amount
        user.save()
        Transaction.create(
            user_id=user_id,
            amount=amount,
            type='deposit' if amount > 0 else 'withdraw',
            description=description
        )
        return True
    return False

def deduct_balance(user_id: int, amount: float, description: str = ""):
    return add_to_balance(user_id, -amount, description)

def format_number(num: float) -> str:
    return f"{num:,.2f}"

# ----------------------------- لوحات المفاتيح -----------------------------
def get_main_keyboard():
    buttons = [
        [InlineKeyboardButton("🌐 الخدمات المتوفرة", callback_data="services_list"),
         InlineKeyboardButton("📦 تمويل القنوات", callback_data="channels_funding")],
        [InlineKeyboardButton("🫆 معلومات الحساب", callback_data="my_profile"),
         InlineKeyboardButton("🎁 الهدية اليومية", callback_data="daily_bonus")],
        [InlineKeyboardButton("💵 تحويل الرصيد", callback_data="transfer_balance"),
         InlineKeyboardButton("🔀 استرداد كود", callback_data="refund_code")],
        [InlineKeyboardButton("🧐 معلومات الطلب", callback_data="order_info"),
         InlineKeyboardButton("📚 جميع طلباتي", callback_data="my_orders")],
        [InlineKeyboardButton("💈 الشروط", callback_data="terms"),
         InlineKeyboardButton("💎 شحن رصيدك", callback_data="charge_balance")],
        [InlineKeyboardButton("📦 المتجر", callback_data="shop"),
         InlineKeyboardButton("✅ عدد طلبات البوت", callback_data="bot_stats")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_admin_panel():
    buttons = [
        [InlineKeyboardButton("⚙️ الإعدادات", callback_data="admin_settings"),
         InlineKeyboardButton("📢 الإذاعة", callback_data="admin_broadcast")],
        [InlineKeyboardButton("👮 إدارة الأدمنية", callback_data="admin_admins"),
         InlineKeyboardButton("🚫 الحظر", callback_data="admin_ban")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"),
         InlineKeyboardButton("🔔 تنبيه الأعضاء الجدد", callback_data="admin_welcome")],
        [InlineKeyboardButton("🔄 التوجيه", callback_data="admin_forward"),
         InlineKeyboardButton("🛠 الصيانة", callback_data="admin_maintenance")],
        [InlineKeyboardButton("🎨 تعديل الأزرار", callback_data="admin_edit_buttons"),
         InlineKeyboardButton("✍️ تعديل رسالة الترحيب", callback_data="admin_edit_welcome")],
        [InlineKeyboardButton("🌐 إدارة مواقع الرشق", callback_data="admin_manage_providers"),
         InlineKeyboardButton("🔄 مزامنة الخدمات", callback_data="admin_sync_services")],
        [InlineKeyboardButton("📢 الاشتراك الإجباري", callback_data="admin_force_sub"),
         InlineKeyboardButton("🧩 الاختصارات والردود", callback_data="admin_shortcuts")],
        [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_providers_list_keyboard(page: int = 0):
    """عرض قائمة المواقع مع أزرار التحكم"""
    per_page = 5
    providers = Provider.select().order_by(Provider.created_at.desc())
    total_pages = (providers.count() + per_page - 1) // per_page
    providers_page = providers.limit(per_page).offset(page * per_page)
    
    buttons = []
    for provider in providers_page:
        status_icon = "✅" if provider.is_active else "❌"
        buttons.append([InlineKeyboardButton(
            f"{status_icon} {provider.name}",
            callback_data=f"provider_{provider.id}"
        )])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⏮ السابق", callback_data=f"providers_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("التالي ⏭", callback_data=f"providers_page_{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton("➕ إضافة موقع جديد", callback_data="admin_add_provider")])
    buttons.append([InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="admin_back")])
    return InlineKeyboardMarkup(buttons)

def get_provider_control_keyboard(provider_id: int):
    """لوحة تحكم موقع معين"""
    provider = Provider.get_by_id(provider_id)
    toggle_text = "❌ تعطيل" if provider.is_active else "✅ تفعيل"
    buttons = [
        [InlineKeyboardButton(toggle_text, callback_data=f"provider_toggle_{provider_id}")],
        [InlineKeyboardButton("🗑 حذف الموقع", callback_data=f"provider_delete_{provider_id}")],
        [InlineKeyboardButton("🔄 مزامنة خدمات هذا الموقع", callback_data=f"provider_sync_{provider_id}")],
        [InlineKeyboardButton("🔙 العودة لقائمة المواقع", callback_data="admin_manage_providers")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_services_keyboard(page: int = 0):
    per_page = 5
    services = Service.select().where(Service.is_active == True)
    total_pages = (services.count() + per_page - 1) // per_page
    services_page = services.limit(per_page).offset(page * per_page)
    
    buttons = []
    for service in services_page:
        # إظهار اسم الموقع التابع للخدمة
        provider = Provider.get_or_none(Provider.id == service.provider_id)
        provider_name = f" [{provider.name}]" if provider else ""
        buttons.append([InlineKeyboardButton(
            f"📌 {service.name}{provider_name} - {format_number(service.price_per_unit)} 💎",
            callback_data=f"service_{service.id}"
        )])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⏮ السابق", callback_data=f"services_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("التالي ⏭", callback_data=f"services_page_{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")])
    return InlineKeyboardMarkup(buttons)

# ----------------------------- معالجات الأوامر -----------------------------
@Client.on_message(filters.command("start") & filters.private)
@require_user
async def start_command(client: Client, message: Message):
    user = message.from_user
    db_user = User.get(User.user_id == user.id)
    welcome_text = f"""
• مرحبا بك عزيزي المستخدم في بوت رشق 𝐁𝐄𝐀𝐔𝐓𝐈𝐅𝐔𝐋 👋🏻

💰- رصيدك: {format_number(db_user.balance)} 💎
📦- ايديك: `{user.id}`

🌐 اختر الخدمة التي ترغب بها من القائمة أدناه:
    """
    await message.reply_text(welcome_text, reply_markup=get_main_keyboard(), parse_mode=ParseMode.MARKDOWN)

@Client.on_message(filters.command("admin") & filters.private)
@admin_only
async def admin_panel_command(client: Client, message: Message):
    await message.reply_text("**🔐 لوحة تحكم المشرفين**\n\nاختر الإجراء المناسب:", reply_markup=get_admin_panel(), parse_mode=ParseMode.MARKDOWN)

# --------------------- إدارة مواقع الرشق ---------------------
@Client.on_message(filters.command("add_provider") & filters.private)
@admin_only
async def add_provider_command(client: Client, message: Message):
    """إضافة موقع رشق جديد"""
    args = message.text.split(maxsplit=3)
    if len(args) < 4:
        await message.reply_text(
            "➕ **إضافة موقع رشق جديد**\n\n"
            "الاستخدام:\n"
            "`/add_provider <الاسم> <API_URL> <API_KEY>`\n\n"
            "مثال:\n"
            "`/add_provider رشق1 https://rashq1.com/api key123`\n\n"
            "⚠️ الاسم يجب أن يكون فريداً.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    name = args[1]
    api_url = args[2]
    api_key = args[3]
    
    # التحقق من عدم وجود اسم مكرر
    if Provider.get_or_none(Provider.name == name):
        await message.reply_text(f"⚠️ يوجد موقع بالفعل باسم `{name}`. يرجى اختيار اسم آخر.", parse_mode=ParseMode.MARKDOWN)
        return
    
    provider = Provider.create(
        name=name,
        api_url=api_url,
        api_key=api_key,
        is_active=True
    )
    await message.reply_text(
        f"✅ تم إضافة موقع `{provider.name}` بنجاح!\n"
        f"🆔 المعرف: {provider.id}\n"
        f"🔗 الرابط: {provider.api_url}\n"
        f"📌 يمكنك الآن مزامنة خدماته باستخدام الأمر:\n"
        f"`/sync_provider {provider.id}`",
        parse_mode=ParseMode.MARKDOWN
    )

@Client.on_message(filters.command("sync_provider") & filters.private)
@admin_only
async def sync_provider_command(client: Client, message: Message):
    """مزامنة خدمات موقع معين"""
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text(
            "🔄 **مزامنة خدمات موقع**\n\n"
            "الاستخدام:\n"
            "`/sync_provider <provider_id>`\n\n"
            "لعرض قائمة المواقع وأرقامها استخدم `/providers`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        provider_id = int(args[1])
    except ValueError:
        await message.reply_text("⚠️ يرجى إدخال معرف الموقع الصحيح.")
        return
    
    provider = Provider.get_or_none(Provider.id == provider_id)
    if not provider:
        await message.reply_text(f"⚠️ لا يوجد موقع بهذا المعرف: {provider_id}")
        return
    
    status_msg = await message.reply_text(f"🔄 جاري مزامنة خدمات موقع `{provider.name}`...", parse_mode=ParseMode.MARKDOWN)
    
    result = await get_services_from_provider(provider)
    if result.get('error'):
        await status_msg.edit_text(
            f"❌ فشل الاتصال بـ {provider.name}: {result.get('error')}\n"
            f"تأكد من صحة الرابط والمفتاح.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    services_data = result.get('services', [])
    if not services_data:
        await status_msg.edit_text(f"⚠️ لم يتم العثور على خدمات في موقع `{provider.name}`.", parse_mode=ParseMode.MARKDOWN)
        return
    
    count = 0
    for svc in services_data:
        # تحديث أو إنشاء خدمة محلية مع ربطها بهذا الموقع
        service, created = Service.get_or_create(
            name=f"{provider.name}:{svc.get('name')}",  # إضافة اسم الموقع لتجنب تكرار الأسماء
            defaults={
                'description': svc.get('description', ''),
                'price_per_unit': float(svc.get('price', 0)),
                'min_quantity': int(svc.get('min', 1)),
                'max_quantity': int(svc.get('max', 10000)),
                'is_active': svc.get('active', True),
                'api_service_id': str(svc.get('id')),
                'provider_id': provider.id
            }
        )
        if not created:
            service.description = svc.get('description', '')
            service.price_per_unit = float(svc.get('price', 0))
            service.min_quantity = int(svc.get('min', 1))
            service.max_quantity = int(svc.get('max', 10000))
            service.is_active = svc.get('active', True)
            service.api_service_id = str(svc.get('id'))
            service.provider_id = provider.id
            service.save()
        count += 1
    
    await status_msg.edit_text(f"✅ تمت مزامنة {count} خدمة بنجاح من موقع `{provider.name}`.", parse_mode=ParseMode.MARKDOWN)

@Client.on_message(filters.command("providers") & filters.private)
@admin_only
async def list_providers_command(client: Client, message: Message):
    """عرض قائمة مواقع الرشق"""
    providers = Provider.select()
    if not providers:
        await message.reply_text("⚠️ لا توجد مواقع رشق مضافة حالياً.\nلإضافة موقع استخدم `/add_provider`")
        return
    
    text = "🌐 **قائمة مواقع الرشق:**\n\n"
    for p in providers:
        status = "✅ مفعل" if p.is_active else "❌ معطل"
        text += f"🆔 `{p.id}` - **{p.name}** ({status})\n"
        text += f"   🔗 {p.api_url}\n\n"
    
    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

@Client.on_message(filters.command("delete_provider") & filters.private)
@admin_only
async def delete_provider_command(client: Client, message: Message):
    """حذف موقع رشق"""
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text(
            "🗑 **حذف موقع**\n\n"
            "الاستخدام:\n"
            "`/delete_provider <provider_id>`\n\n"
            "⚠️ سيتم حذف جميع الخدمات المرتبطة بهذا الموقع أيضاً.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        provider_id = int(args[1])
    except ValueError:
        await message.reply_text("⚠️ يرجى إدخال معرف الموقع الصحيح.")
        return
    
    provider = Provider.get_or_none(Provider.id == provider_id)
    if not provider:
        await message.reply_text(f"⚠️ لا يوجد موقع بهذا المعرف: {provider_id}")
        return
    
    # حذف الخدمات المرتبطة
    services_deleted = Service.delete().where(Service.provider_id == provider_id).execute()
    
    provider.delete_instance()
    await message.reply_text(
        f"✅ تم حذف موقع `{provider.name}` بنجاح.\n"
        f"🗑 تم حذف {services_deleted} خدمة مرتبطة به.",
        parse_mode=ParseMode.MARKDOWN
    )

@Client.on_message(filters.command("toggle_provider") & filters.private)
@admin_only
async def toggle_provider_command(client: Client, message: Message):
    """تفعيل/تعطيل موقع"""
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text(
            "🔄 **تفعيل/تعطيل موقع**\n\n"
            "الاستخدام:\n"
            "`/toggle_provider <provider_id>`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        provider_id = int(args[1])
    except ValueError:
        await message.reply_text("⚠️ يرجى إدخال معرف الموقع الصحيح.")
        return
    
    provider = Provider.get_or_none(Provider.id == provider_id)
    if not provider:
        await message.reply_text(f"⚠️ لا يوجد موقع بهذا المعرف: {provider_id}")
        return
    
    provider.is_active = not provider.is_active
    provider.save()
    status = "مفعل" if provider.is_active else "معطل"
    await message.reply_text(f"✅ تم {status} موقع `{provider.name}` بنجاح.", parse_mode=ParseMode.MARKDOWN)

# ----------------------------- معالجات الأزرار -----------------------------
@Client.on_callback_query()
async def handle_callbacks(client: Client, callback: CallbackQuery):
    data = callback.data
    user_id = callback.from_user.id
    user = callback.from_user
    
    db_user = User.get_or_none(User.user_id == user_id)
    if db_user and db_user.is_banned:
        await callback.answer("🚫 عذراً، تم حظرك من استخدام البوت.", show_alert=True)
        return
    
    # القائمة الرئيسية
    if data == "back_to_main":
        db_user = User.get_or_none(User.user_id == user_id)
        welcome_text = f"""
• مرحبا بك عزيزي المستخدم في بوت رشق 𝐁𝐄𝐀𝐔𝐓𝐈𝐅𝐔𝐋 👋🏻

💰- رصيدك: {format_number(db_user.balance)} 💎
📦- ايديك: `{user_id}`

🌐 اختر الخدمة التي ترغب بها من القائمة أدناه:
        """
        await callback.message.edit_text(welcome_text, reply_markup=get_main_keyboard(), parse_mode=ParseMode.MARKDOWN)
    
    elif data == "admin_back":
        await callback.message.edit_text("**🔐 لوحة تحكم المشرفين**\n\nاختر الإجراء المناسب:", reply_markup=get_admin_panel(), parse_mode=ParseMode.MARKDOWN)
    
    # إدارة مواقع الرشق
    elif data == "admin_manage_providers":
        await callback.message.edit_text(
            "🌐 **إدارة مواقع الرشق**\n\nاختر موقعاً للتحكم فيه:",
            reply_markup=get_providers_list_keyboard(0),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data.startswith("providers_page_"):
        page = int(data.split("_")[2])
        await callback.message.edit_reply_markup(reply_markup=get_providers_list_keyboard(page))
    
    elif data.startswith("provider_"):
        provider_id = int(data.split("_")[1])
        provider = Provider.get_or_none(Provider.id == provider_id)
        if provider:
            await callback.message.edit_text(
                f"**🌐 {provider.name}**\n\n"
                f"🆔 المعرف: `{provider.id}`\n"
                f"🔗 الرابط: `{provider.api_url}`\n"
                f"🔑 المفتاح: `{provider.api_key[:8]}...`\n"
                f"📌 الحالة: {'✅ مفعل' if provider.is_active else '❌ معطل'}\n"
                f"📅 تاريخ الإضافة: {provider.created_at.strftime('%Y-%m-%d %H:%M')}",
                reply_markup=get_provider_control_keyboard(provider_id),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await callback.answer("الموقع غير موجود", show_alert=True)
    
    elif data.startswith("provider_toggle_"):
        provider_id = int(data.split("_")[2])
        provider = Provider.get_or_none(Provider.id == provider_id)
        if provider:
            provider.is_active = not provider.is_active
            provider.save()
            status = "مفعل" if provider.is_active else "معطل"
            await callback.answer(f"✅ تم {status} الموقع", show_alert=True)
            # تحديث العرض
            await callback.message.edit_text(
                f"**🌐 {provider.name}**\n\n"
                f"🆔 المعرف: `{provider.id}`\n"
                f"🔗 الرابط: `{provider.api_url}`\n"
                f"🔑 المفتاح: `{provider.api_key[:8]}...`\n"
                f"📌 الحالة: {'✅ مفعل' if provider.is_active else '❌ معطل'}",
                reply_markup=get_provider_control_keyboard(provider_id),
                parse_mode=ParseMode.MARKDOWN
            )
    
    elif data.startswith("provider_delete_"):
        provider_id = int(data.split("_")[2])
        provider = Provider.get_or_none(Provider.id == provider_id)
        if provider:
            # حذف الخدمات المرتبطة
            services_count = Service.delete().where(Service.provider_id == provider_id).execute()
            provider.delete_instance()
            await callback.answer(f"✅ تم حذف الموقع {provider.name} و {services_count} خدمة", show_alert=True)
            await callback.message.edit_text(
                "🌐 **إدارة مواقع الرشق**\n\nتم حذف الموقع بنجاح.",
                reply_markup=get_providers_list_keyboard(0),
                parse_mode=ParseMode.MARKDOWN
            )
    
    elif data.startswith("provider_sync_"):
        provider_id = int(data.split("_")[2])
        provider = Provider.get_or_none(Provider.id == provider_id)
        if not provider:
            await callback.answer("الموقع غير موجود", show_alert=True)
            return
        
        await callback.answer(f"🔄 جاري مزامنة خدمات {provider.name}...", show_alert=True)
        result = await get_services_from_provider(provider)
        if result.get('error'):
            await callback.message.edit_text(
                f"❌ فشل المزامنة لموقع {provider.name}: {result.get('error')}",
                reply_markup=get_provider_control_keyboard(provider_id),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        services_data = result.get('services', [])
        count = 0
        for svc in services_data:
            service, created = Service.get_or_create(
                name=f"{provider.name}:{svc.get('name')}",
                defaults={
                    'description': svc.get('description', ''),
                    'price_per_unit': float(svc.get('price', 0)),
                    'min_quantity': int(svc.get('min', 1)),
                    'max_quantity': int(svc.get('max', 10000)),
                    'is_active': svc.get('active', True),
                    'api_service_id': str(svc.get('id')),
                    'provider_id': provider.id
                }
            )
            if not created:
                service.description = svc.get('description', '')
                service.price_per_unit = float(svc.get('price', 0))
                service.min_quantity = int(svc.get('min', 1))
                service.max_quantity = int(svc.get('max', 10000))
                service.is_active = svc.get('active', True)
                service.api_service_id = str(svc.get('id'))
                service.save()
            count += 1
        
        await callback.message.edit_text(
            f"✅ تمت مزامنة {count} خدمة من موقع {provider.name} بنجاح.",
            reply_markup=get_provider_control_keyboard(provider_id),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == "admin_add_provider":
        await callback.message.edit_text(
            "➕ **إضافة موقع رشق جديد**\n\n"
            "استخدم الأمر:\n"
            "`/add_provider <الاسم> <API_URL> <API_KEY>`\n\n"
            "مثال:\n"
            "`/add_provider رشق2 https://rashq2.com/api key456`\n\n"
            "⚠️ بعد الإضافة، قم بمزامنة الخدمات باستخدام الأمر `/sync_provider <id>`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="admin_manage_providers")]])
        )
    
    elif data == "admin_sync_services":
        # مزامنة جميع المواقع النشطة
        providers = Provider.select().where(Provider.is_active == True)
        if not providers:
            await callback.answer("⚠️ لا توجد مواقع نشطة للمزامنة.", show_alert=True)
            return
        
        await callback.answer("🔄 جاري مزامنة جميع المواقع...", show_alert=True)
        total_services = 0
        for provider in providers:
            result = await get_services_from_provider(provider)
            if not result.get('error'):
                services_data = result.get('services', [])
                for svc in services_data:
                    service, created = Service.get_or_create(
                        name=f"{provider.name}:{svc.get('name')}",
                        defaults={
                            'description': svc.get('description', ''),
                            'price_per_unit': float(svc.get('price', 0)),
                            'min_quantity': int(svc.get('min', 1)),
                            'max_quantity': int(svc.get('max', 10000)),
                            'is_active': svc.get('active', True),
                            'api_service_id': str(svc.get('id')),
                            'provider_id': provider.id
                        }
                    )
                    if not created:
                        service.description = svc.get('description', '')
                        service.price_per_unit = float(svc.get('price', 0))
                        service.min_quantity = int(svc.get('min', 1))
                        service.max_quantity = int(svc.get('max', 10000))
                        service.is_active = svc.get('active', True)
                        service.api_service_id = str(svc.get('id'))
                        service.save()
                    total_services += 1
        await callback.message.edit_text(
            f"✅ تمت مزامنة {total_services} خدمة من {providers.count()} موقع.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="admin_back")]])
        )
    
    # قائمة الخدمات للمستخدمين
    elif data == "services_list":
        await callback.message.edit_text("**🌐 الخدمات المتوفرة**\n\nاختر الخدمة التي تريدها:", reply_markup=get_services_keyboard(0), parse_mode=ParseMode.MARKDOWN)
    
    elif data.startswith("services_page_"):
        page = int(data.split("_")[2])
        await callback.message.edit_reply_markup(reply_markup=get_services_keyboard(page))
    
    elif data.startswith("service_"):
        service_id = int(data.split("_")[1])
        service = Service.get_or_none(Service.id == service_id)
        if service and service.is_active:
            # الحصول على الموقع المرتبط
            provider = Provider.get_or_none(Provider.id == service.provider_id)
            if not provider or not provider.is_active:
                await callback.answer("⚠️ الموقع المرتبط بهذه الخدمة غير نشط حالياً.", show_alert=True)
                return
            
            # طلب الرابط
            await client.send_message(
                chat_id=user_id,
                text=f"📌 **{service.name}**\n\n"
                     f"📝 {service.description}\n"
                     f"💎 السعر: {format_number(service.price_per_unit)} 💎\n"
                     f"📊 الكمية المتاحة: {service.min_quantity} - {service.max_quantity}\n"
                     f"🌐 الموقع: {provider.name}\n\n"
                     f"⚠️ يرجى إرسال الرابط (مثال: رابط حساب Instagram أو فيديو YouTube):",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 إلغاء", callback_data="back_to_main")]]),
                parse_mode=ParseMode.MARKDOWN
            )
            try:
                link_response = await client.listen(user_id, timeout=60)
                target_link = link_response.text.strip()
                
                await link_response.reply_text("🔢 أدخل الكمية المطلوبة:")
                quantity_response = await client.listen(user_id, timeout=60)
                quantity = int(quantity_response.text)
                
                if service.min_quantity <= quantity <= service.max_quantity:
                    total_cost = quantity * service.price_per_unit
                    if get_user_balance(user_id) >= total_cost:
                        # إرسال الطلب إلى موقع الرشق المرتبط
                        api_result = await create_order_on_provider(
                            provider=provider,
                            service_id=service.api_service_id,
                            quantity=quantity,
                            link=target_link,
                            user_id=user_id
                        )
                        
                        if api_result.get('error'):
                            await quantity_response.reply_text(
                                f"❌ فشل إنشاء الطلب في موقع {provider.name}: {api_result.get('error')}\n"
                                f"يرجى المحاولة لاحقاً أو إبلاغ المشرف.",
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]])
                            )
                            return
                        
                        order_id = generate_unique_id()
                        provider_order_id = api_result.get('order_id') or api_result.get('id')
                        Order.create(
                            order_id=order_id,
                            user_id=user_id,
                            service=service.name,
                            quantity=quantity,
                            cost=total_cost,
                            status='processing' if api_result.get('status') == 'pending' else 'pending',
                            target=target_link,
                            provider_order_id=str(provider_order_id) if provider_order_id else None,
                            provider_response=json.dumps(api_result),
                            provider_id=provider.id
                        )
                        deduct_balance(user_id, total_cost, f"طلب خدمة: {service.name} - الكمية: {quantity} (موقع: {provider.name})")
                        
                        # إخطار المشرفين
                        for admin_id in ADMIN_IDS:
                            await client.send_message(
                                admin_id,
                                f"📢 طلب جديد عبر {provider.name}!\n\n"
                                f"🆔 ID الطلب: {order_id}\n"
                                f"🔗 Provider Order ID: {provider_order_id}\n"
                                f"👤 المستخدم: {user.first_name} (ID: {user_id})\n"
                                f"📌 الخدمة: {service.name}\n"
                                f"🔢 الكمية: {quantity}\n"
                                f"💰 التكلفة: {format_number(total_cost)} 💎\n"
                                f"🔗 الرابط: {target_link}"
                            )
                        
                        await quantity_response.reply_text(
                            f"✅ تم إنشاء طلبك بنجاح عبر موقع {provider.name}!\n\n"
                            f"🆔 رقم الطلب: `{order_id}`\n"
                            f"📌 الخدمة: {service.name}\n"
                            f"🔢 الكمية: {quantity}\n"
                            f"💰 التكلفة: {format_number(total_cost)} 💎\n\n"
                            f"سيتم معالجة طلبك في أقرب وقت.",
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]])
                        )
                    else:
                        await quantity_response.reply_text(
                            f"⚠️ رصيدك غير كافٍ!\n"
                            f"رصيدك الحالي: {format_number(get_user_balance(user_id))} 💎\n"
                            f"المطلوب: {format_number(total_cost)} 💎",
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]])
                        )
                else:
                    await quantity_response.reply_text(
                        f"⚠️ الكمية غير صالحة!\n"
                        f"الحد الأدنى: {service.min_quantity}\n"
                        f"الحد الأقصى: {service.max_quantity}",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 المحاولة مرة أخرى", callback_data="services_list")]])
                    )
            except (ValueError, asyncio.TimeoutError):
                await client.send_message(user_id, "⏰ انتهى الوقت أو إدخال غير صحيح. يرجى المحاولة مرة أخرى.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]]))
        else:
            await callback.answer("⚠️ الخدمة غير متوفرة حالياً.", show_alert=True)
    
    # باقي الأقسام (my_profile, daily_bonus, transfer_balance, order_info, my_orders, terms, charge_balance, bot_stats, etc.)
    # يمكن إضافتها بنفس الطريقة السابقة، للاختصار سأضيف الأساسيات فقط.
    elif data == "my_profile":
        db_user = User.get_or_none(User.user_id == user_id)
        referrals_count = User.select().where(User.referred_by == user_id).count()
        profile_text = f"""
🫆 **معلومات الحساب**

👤 الاسم: {user.first_name}
🆔 المعرف: `{user_id}`
💰 الرصيد: {format_number(db_user.balance)} 💎
🔗 كود الإحالة: `{db_user.referral_code}`
👥 عدد الإحالات: {referrals_count}
📅 تاريخ الانضمام: {db_user.joined_date.strftime('%Y-%m-%d')}

💡 قم بمشاركة كود الإحالة الخاص بك مع أصدقائك لتربح 5 💎 عن كل مستخدم جديد!
        """
        await callback.message.edit_text(profile_text, reply_markup=get_main_keyboard(), parse_mode=ParseMode.MARKDOWN)
    
    elif data == "daily_bonus":
        last_bonus_key = f"last_bonus_{user_id}"
        last_bonus = BotSettings.get_setting(last_bonus_key)
        if last_bonus:
            last_bonus_date = datetime.fromisoformat(last_bonus)
            if datetime.now() - last_bonus_date < timedelta(days=1):
                hours_left = 24 - (datetime.now() - last_bonus_date).seconds // 3600
                await callback.answer(f"🎁 يمكنك الحصول على الهدية اليومية بعد {hours_left} ساعة!", show_alert=True)
                return
        bonus_amount = random.randint(1, 20)
        add_to_balance(user_id, bonus_amount, f"مكافأة يومية: {bonus_amount}")
        BotSettings.set_setting(last_bonus_key, datetime.now().isoformat())
        await callback.answer(f"🎁 تم إضافة {bonus_amount} 💎 إلى رصيدك!", show_alert=True)
        await callback.message.edit_text(
            f"🎁 **الهدية اليومية** 🎁\n\n"
            f"تهانينا! لقد حصلت على {bonus_amount} 💎\n"
            f"رصيدك الحالي: {format_number(get_user_balance(user_id))} 💎",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]]),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == "order_info":
        await callback.message.edit_text("🧐 **معلومات الطلب**\n\nأدخل رقم الطلب الخاص بك:", parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]]))
        try:
            response = await client.listen(user_id, timeout=60)
            if response.text:
                order_id = response.text.strip()
                order = Order.get_or_none(Order.order_id == order_id)
                if order:
                    # تحديث الحالة من الموقع إذا كان هناك provider
                    if order.provider_id and order.provider_order_id:
                        provider = Provider.get_or_none(Provider.id == order.provider_id)
                        if provider:
                            await update_order_status_from_provider(order)
                            order = Order.get(Order.order_id == order_id)
                    
                    status_map = {'pending': '⏳ قيد الانتظار', 'processing': '🔄 قيد المعالجة', 'completed': '✅ مكتمل', 'cancelled': '❌ ملغي'}
                    await response.reply_text(
                        f"📋 **تفاصيل الطلب**\n\n"
                        f"🆔 رقم الطلب: `{order.order_id}`\n"
                        f"📌 الخدمة: {order.service}\n"
                        f"🔢 الكمية: {order.quantity}\n"
                        f"💰 التكلفة: {format_number(order.cost)} 💎\n"
                        f"📊 الحالة: {status_map.get(order.status, order.status)}\n"
                        f"🔗 الرابط: {order.target or 'غير محدد'}\n"
                        f"📅 تاريخ الإنشاء: {order.created_at.strftime('%Y-%m-%d %H:%M')}",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]])
                    )
                else:
                    await response.reply_text("⚠️ لا يوجد طلب بهذا الرقم.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]]))
        except asyncio.TimeoutError:
            await client.send_message(user_id, "⏰ انتهى الوقت.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]]))
    
    elif data == "my_orders":
        orders = Order.select().where(Order.user_id == user_id).order_by(Order.created_at.desc()).limit(10)
        if not orders:
            await callback.message.edit_text("📚 **جميع طلباتي**\n\nلا توجد طلبات سابقة.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]]), parse_mode=ParseMode.MARKDOWN)
            return
        text = "📚 **أحدث طلباتي:**\n\n"
        for order in orders:
            status_emoji = {'pending': '⏳', 'processing': '🔄', 'completed': '✅', 'cancelled': '❌'}.get(order.status, '❓')
            text += f"{status_emoji} **{order.service}**\n"
            text += f"   🆔: `{order.order_id}`\n"
            text += f"   🔢 الكمية: {order.quantity}\n"
            text += f"   💰 التكلفة: {format_number(order.cost)} 💎\n"
            text += f"   📅 التاريخ: {order.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]]), parse_mode=ParseMode.MARKDOWN)
    
    elif data == "terms":
        await callback.message.edit_text(
            "💈 **الشروط والأحكام**\n\n"
            "1. يرجى قراءة تفاصيل الخدمة قبل الشراء.\n"
            "2. البوت ليس مسؤولاً عن سوء استخدام الخدمات.\n"
            "3. عند حصول مشكلة بالخدمة يمكنك التحدث مع الدعم.\n"
            "4. جميع المبالغ المدفوعة غير قابلة للاسترداد.\n"
            "5. يرجى مراجعة حالة الطلب باستخدام معرف الطلب.\n\n"
            "للمساعدة والدعم تواصل مع @BeautySupport",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]]),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == "charge_balance":
        await callback.message.edit_text(
            "💎 **شحن رصيدك**\n\n"
            "الطرق المتاحة للشحن:\n"
            "🔹 تحويل عبر العملات الرقمية\n"
            "🔹 فودافون كاش\n\n"
            "للمساعدة في الشحن تواصل مع:\n"
            "@BeautySupport",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]])
        )
    
    elif data == "bot_stats":
        total_users = User.select().count()
        total_orders = Order.select().count()
        providers_count = Provider.select().count()
        await callback.message.edit_text(
            f"✅ **عدد طلبات البوت**\n\n"
            f"إجمالي عدد المستخدمين: {total_users}\n"
            f"إجمالي عدد الطلبات: {total_orders}\n"
            f"عدد مواقع الرشق: {providers_count}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]])
        )
    
    # باقي الأقسام (channels_funding, refund_code, shop, transfer_balance) يمكن إضافتها بنفس الطريقة، وللاختصار نكتفي بما سبق.
    else:
        await callback.answer("هذا القسم قيد التطوير.", show_alert=True)

# ----------------------------- أوامر المشرفين الإضافية -----------------------------
@Client.on_message(filters.command("add_admin") & filters.private)
@admin_only
async def add_admin_command(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("الاستخدام: `/add_admin <user_id>`", parse_mode=ParseMode.MARKDOWN)
        return
    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply_text("⚠️ يرجى إدخال ID صحيح.")
        return
    user = User.get_or_none(User.user_id == target_id)
    if not user:
        await message.reply_text(f"⚠️ لا يوجد مستخدم بهذا ID: {target_id}")
        return
    user.is_admin = True
    user.save()
    await message.reply_text(f"✅ تم إضافة {user.first_name} كمشرف بنجاح.")

@Client.on_message(filters.command("remove_admin") & filters.private)
@admin_only
async def remove_admin_command(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("الاستخدام: `/remove_admin <user_id>`", parse_mode=ParseMode.MARKDOWN)
        return
    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply_text("⚠️ يرجى إدخال ID صحيح.")
        return
    if target_id in ADMIN_IDS:
        await message.reply_text("⚠️ لا يمكن إزالة المشرف الرئيسي.")
        return
    user = User.get_or_none(User.user_id == target_id)
    if not user:
        await message.reply_text(f"⚠️ لا يوجد مستخدم بهذا ID: {target_id}")
        return
    user.is_admin = False
    user.save()
    await message.reply_text(f"✅ تم إزالة {user.first_name} من قائمة المشرفين.")

# ----------------------------- إنشاء خدمات افتراضية -----------------------------
def initialize_default_providers_and_services():
    """إنشاء مواقع افتراضية وخدمات إذا كانت قاعدة البيانات فارغة"""
    if Provider.select().count() == 0:
        # إنشاء موقع افتراضي
        default_provider = Provider.create(
            name="الموقع الافتراضي",
            api_url="https://example.com/api",
            api_key="default_key_123",
            is_active=False  # معطل افتراضياً حتى يقوم المشرف بتعيين البيانات الصحيحة
        )
        logger.info("تم إنشاء موقع افتراضي (معطل) - يرجى تحديث بياناته")
    
    if Service.select().count() == 0:
        default_services = [
            {"name": "متابعين Instagram", "description": "متابعين حقيقيين لإنستغرام", "price": 0.5, "min": 100, "max": 10000},
            {"name": "مشاهدات YouTube", "description": "مشاهدات فيديو يوتيوب", "price": 0.3, "min": 100, "max": 50000},
            {"name": "أعضاء Telegram", "description": "أعضاء حقيقيين لمجموعات التليجرام", "price": 0.2, "min": 100, "max": 5000},
        ]
        for svc in default_services:
            Service.create(
                name=svc["name"],
                description=svc["description"],
                price_per_unit=svc["price"],
                min_quantity=svc["min"],
                max_quantity=svc["max"],
                is_active=True,
                provider_id=None  # غير مرتبط بأي موقع حتى تتم المزامنة
            )
        logger.info("تم إضافة خدمات افتراضية (غير مرتبطة بموقع)")

# ----------------------------- تشغيل البوت -----------------------------
app = None

def ma