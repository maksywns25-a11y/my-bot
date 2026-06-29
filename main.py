import os
import json
import requests
import re
import random
import base64
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# ========== التوكن والمتغيرات الرئيسية ==========
API_KEY = "8818721617:AAF266kqrgrYLL19e6F45AlvaU-74XewJRI"
ADMIN = 6640098641  # ايديك
NMBR = "07778443464"  # رقم اسيا
CHNL = "@zaidmfj"  # يوزر قناتك
SUDO = [6640098641]  # قائمة الادمن (ايديك فقط)
API_TOK = "fcec77c6da41e28fb1744b2923c77143915d6b81"  # توكن موقع الرشق
BOT_USERNAME = None

# ========== تحويل مسارات الملفات إلى المجلد المؤقت /tmp المتوافق مع Vercel ==========
def get_tmp_path(filename):
    return os.path.join("/tmp", filename)

SAIKO_FILE = get_tmp_path("saiko.json")
ABBAS_FILE = get_tmp_path("abbas.json")
AD_FILE = get_tmp_path("ad.json")
RSHQ_FILE = get_tmp_path("rshq.json")
BOT_TXT_FILE = get_tmp_path("bot.txt")
SKOR_FILE = get_tmp_path("skor.php")
ABBAS09_FILE = get_tmp_path("abbas09.json")
MSG_FILE = get_tmp_path("msg.php")

# ========== دوال مساعدة ==========
def bot(method, datas=None):
    if datas is None:
        datas = {}
    url = f"https://api.telegram.org/bot{API_KEY}/{method}"
    try:
        response = requests.post(url, data=datas)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error in bot: {e}")
        return None

def get_bot_username():
    global BOT_USERNAME
    if BOT_USERNAME is None:
        res = bot('getme')
        if res and res.get('ok'):
            BOT_USERNAME = res['result']['username']
    return BOT_USERNAME or "bot"

def load_json(file):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def read_file(file):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ""

def write_file(file, content):
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)

def append_file(file, content):
    with open(file, 'a', encoding='utf-8') as f:
        f.write(content)

def file_lines(file):
    content = read_file(file)
    if content == "":
        return []
    return content.strip().split('\n')

def is_numeric(s):
    try:
        int(s)
        return True
    except:
        return False

# ========== تهيئة الملفات في الـ /tmp ==========
if not os.path.exists(SAIKO_FILE):
    save_json(SAIKO_FILE, {"gch": "❎"})
if not os.path.exists(ABBAS_FILE):
    write_file(ABBAS_FILE, "")
if not os.path.exists(AD_FILE):
    write_file(AD_FILE, str(ADMIN) + "\n")
if not os.path.exists(RSHQ_FILE):
    save_json(RSHQ_FILE, {"rshaq": "on", "coin": {}, "mode": {}, "id": {}, "shhn": {}, "tp": {}, "3dd": {}, "order": {}})
if not os.path.exists(BOT_TXT_FILE):
    write_file(BOT_TXT_FILE, "مفتوح")
if not os.path.exists(SKOR_FILE):
    write_file(SKOR_FILE, "معطل ⚠️")
if not os.path.exists(ABBAS09_FILE):
    save_json(ABBAS09_FILE, {"addmessage": 0, "messagee": 0})
if not os.path.exists(MSG_FILE):
    write_file(MSG_FILE, "")

# ========== دوال جلب بيانات التحديث ==========
def get_chat_id(update):
    if 'message' in update and update['message']:
        return update['message']['chat']['id']
    elif 'callback_query' in update and update['callback_query']:
        return update['callback_query']['message']['chat']['id']
    return None

def get_from_id(update):
    if 'message' in update and update['message']:
        return update['message']['from']['id']
    elif 'callback_query' in update and update['callback_query']:
        return update['callback_query']['from']['id']
    return None

def get_message_id(update):
    if 'message' in update and update['message']:
        return update['message']['message_id']
    elif 'callback_query' in update and update['callback_query']:
        return update['callback_query']['message']['message_id']
    return None

def get_name(update):
    if 'message' in update and update['message']:
        return update['message']['from'].get('first_name', '')
    elif 'callback_query' in update and update['callback_query']:
        return update['callback_query']['from'].get('first_name', '')
    return ''

def get_username(update):
    if 'message' in update and update['message']:
        return update['message']['from'].get('username', '')
    elif 'callback_query' in update and update['callback_query']:
        return update['callback_query']['from'].get('username', '')
    return ''

def is_member(chat_id, user_id):
    url = f"https://api.telegram.org/bot{API_KEY}/getChatMember"
    params = {"chat_id": chat_id, "user_id": user_id}
    try:
        r = requests.get(url, params=params)
        data = r.json()
        if data.get('ok') and data.get('result'):
            status = data['result'].get('status')
            return status not in ['left', 'kicked']
        return False
    except:
        return False

# ========== معالجة الويب هوك ==========
@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if update:
        process_update(update)
    return 'ok', 200

@app.route('/')
def index():
    return "<h1>Bot is running perfectly!</h1>"

@app.route('/set_webhook')
def set_webhook():
    YOUR_VERCEL_URL = "https://my-bot-two-sepia.vercel.app" 
    s = bot('setWebhook', {'url': f"{YOUR_VERCEL_URL}/webhook"})
    if s:
        return "<h1>Webhook setup ok!</h1>"
    return "<h1>Webhook setup failed!</h1>"

def process_update(update):
    message = update.get('message')
    callback_query = update.get('callback_query')
    chat_id = get_chat_id(update)
    from_id = get_from_id(update)
    message_id = get_message_id(update)
    text = message.get('text') if message else None
    name = get_name(update)
    username = get_username(update)

    if not chat_id or not from_id:
        return

    # التحقق من قفل البوت
    bot_status = read_file(BOT_TXT_FILE).strip()
    if bot_status == "متوقف" and from_id != ADMIN:
        if message:
            bot('sendMessage', {'chat_id': chat_id, 'text': "عذراً، البوت متوقف حالياً في صيانة مؤقتة 🛠"})
        return

    # الاشتراك الإجباري الثابت
    if message and not is_member(CHNL, from_id) and from_id != ADMIN:
        bot('sendMessage', {
            'chat_id': chat_id,
            'text': f"🚸| عذراً عزيزي {name}\n🔰| عليك الاشتراك بقناة البوت لتتمكن من استخدامه\n\n- {CHNL}\n\n‼️| اشترك ثم أرسل /start",
            'disable_web_page_preview': True
        })
        return

    # تسجيل الأعضاء
    users = file_lines(ABBAS_FILE)
    if message and str(from_id) not in users:
        append_file(ABBAS_FILE, f"{from_id}\n")

    # ========== معالجة الأوامر النصية ==========
    if text:
        if text.startswith('/start'):
            e1 = text.replace('/start', '').strip()
            rshq = load_json(RSHQ_FILE)
            if e1 and e1.isdigit() and int(e1) != from_id:
                if str(from_id) not in rshq.get("3thu", []):
                    rshq.setdefault("coin", {})
                    rshq["coin"][str(e1)] = rshq["coin"].get(str(e1), 0) + 5
                    rshq.setdefault("3thu", []).append(str(from_id))
                    save_json(RSHQ_FILE, rshq)
                    bot('sendMessage', {'chat_id': int(e1), 'text': f"🎯 دخل عضو جديد عبر رابط دعوتك وحصلت على +5 نقاط!"})
            
            coin = rshq.get("coin", {}).get(str(from_id), 0)
            bot_tlb = rshq.get("bot_tlb", 0)
            send_start_message(chat_id, from_id, name, coin, bot_tlb)
            return

        if text == '/admin' and from_id == ADMIN:
            send_admin_panel(chat_id, message_id, from_id)
            return

        rshq = load_json(RSHQ_FILE)
        mode = rshq.get("mode", {}).get(str(from_id))

        # تحويل النقاط
        if mode == "transer" and is_numeric(text):
            coin = rshq.get("coin", {}).get(str(from_id), 0)
            amount = int(text)
            if coin >= amount and amount >= 20:
                MakLink = ''.join(random.choices('AbCdEfGhIjKlMnOpQrStU1234567890', k=13))
                rshq["coin"][str(from_id)] = coin - amount
                rshq.setdefault("thoiler", {})[MakLink] = {"coin": amount, "to": from_id}
                rshq["mode"][str(from_id)] = None
                save_json(RSHQ_FILE, rshq)
                link = f"https://t.me/{get_bot_username()}?start=Bero{MakLink}"
                bot('sendMessage', {
                    'chat_id': chat_id,
                    'text': f"💰 تم إنشاء رابط تحويل بقيمة *{amount}* نقطة بنجاح.\n\nالرابط للنسخ والمشاركة:\n`{link}`",
                    'parse_mode': 'Markdown',
                    'reply_markup': json.dumps({'inline_keyboard': [[{'text': 'رجوع', 'callback_data': 'bak'}]]})
                })
            else:
                bot('sendMessage', {'chat_id': chat_id, 'text': "❌ نقاطك غير كافية أو القيمة أقل من 20 نقطة."})
            return

        # إضافة / خصم النقاط من الأدمن
        if mode == "coins" and from_id == ADMIN:
            rshq['mode'][str(from_id)] = "coins2"
            rshq['id'][str(from_id)] = text
            save_json(RSHQ_FILE, rshq)
            bot('sendMessage', {'chat_id': chat_id, 'text': f"أرسل الآن عدد النقاط لإضافتها أو خصمها للحساب {text}:"})
            return

        if mode == "coins2" and from_id == ADMIN:
            target_id = rshq.get('id', {}).get(str(from_id))
            if target_id and is_numeric(text.replace('-', '')):
                rshq.setdefault("coin", {})
                rshq["coin"][target_id] = rshq["coin"].get(target_id, 0) + int(text)
                rshq['mode'][str(from_id)] = None
                save_json(RSHQ_FILE, rshq)
                bot('sendMessage', {'chat_id': chat_id, 'text': f"✅ تم تحديث نقاط الحساب {target_id} بمقدار {text} نقطة."})
            return

        # استقبال كود الهدية
        if mode == "hdia":
            if text in rshq and str(rshq[text]).startswith("on|"):
                points = int(rshq[text].split('|')[1])
                rshq.setdefault("mehdia", {})
                if str(from_id) not in rshq["mehdia"].get(text, []):
                    rshq["mehdia"].setdefault(text, []).append(str(from_id))
                    rshq.setdefault("coin", {})[str(from_id)] = rshq["coin"].get(str(from_id), 0) + points
                    rshq["mode"][str(from_id)] = None
                    save_json(RSHQ_FILE, rshq)
                    bot('sendMessage', {'chat_id': chat_id, 'text': f"🎉 مبروك! حصلت على {points} نقطة من كود الهدية."})
                else:
                    bot('sendMessage', {'chat_id': chat_id, 'text': "❌ أنت استخدمت هذا الكود مسبقاً."})
            else:
                bot('sendMessage', {'chat_id': chat_id, 'text': "❌ كود الهدية منتهي الصلاحية أو خاطئ."})
            return

        # استقبال رابط حساب الرشق
        if mode == "to":
            tp = rshq.get('tp', {}).get(str(from_id))
            quantity = rshq.get('3dd', {}).get(str(from_id))
            if tp and quantity:
                rnd_order = random.randint(100000, 999999)
                rshq.setdefault("order", {})[str(rnd_order)] = rnd_order
                rshq['mode'][str(from_id)] = None
                rshq['bot_tlb'] = rshq.get('bot_tlb', 0) + 1
                save_json(RSHQ_FILE, rshq)
                bot('sendMessage', {
                    'chat_id': chat_id,
                    'text': f"✅ تم إرسال طلبك بنجاح للجدولة والاكتمال!\n\nرقم الطلب: `{rnd_order}`\nالعدد المستهدف: {quantity}\nالرابط المرسل: {text}",
                    'parse_mode': 'Markdown'
                })
                bot('sendMessage', {'chat_id': ADMIN, 'text': f"🔔 طلب رشق جديد من العضو: {from_id}\nالعدد: {quantity}\nالرابط: {text}"})
            return

        # الإذاعة العامة للأعضاء
        if read_file(MSG_FILE).strip() == "on" and from_id == ADMIN:
            all_u = file_lines(ABBAS_FILE)
            for uid in all_u:
                if uid.strip():
                    bot('sendMessage', {'chat_id': int(uid.strip()), 'text': text})
            write_file(MSG_FILE, "")
            bot('sendMessage', {'chat_id': chat_id, 'text': f"📢 تم إرسال الإذاعة بنجاح إلى {len(all_u)} مشترك."})
            return

    # ========== معالجة ضغطات الأزرار (Callback Queries) ==========
    if callback_query:
        data = callback_query.get('data')
        if not data:
            return
        
        if data == 'collect':
            link = f"https://t.me/{get_bot_username()}?start={from_id}"
            bot('sendMessage', {
                'chat_id': chat_id,
                'text': f"🎯 نظام تجميع النقاط:\n\nقم بنسخ الرابط الخاص بك بالأسفل، وكل شخص يدخل للبوت عن طريق الرابط ستحصل على *5 نقاط* مجانية!\n\nرابط الدعوة الخاص بك:\n`{link}`",
                'parse_mode': 'Markdown'
            })
            return

        if data == 'gift_code':
            rshq = load_json(RSHQ_FILE)
            rshq.setdefault("mode", {})[str(from_id)] = "hdia"
            save_json(RSHQ_FILE, rshq)
            bot('sendMessage', {'chat_id': chat_id, 'text': "📥 قم بإرسال كود الهدية لتفعيله الفوري وحصد نقاطك:"})
            return

        if data == 'transfer_coin':
            rshq = load_json(RSHQ_FILE)
            rshq.setdefault("mode", {})[str(from_id)] = "transer"
            save_json(RSHQ_FILE, rshq)
            bot('sendMessage', {'chat_id': chat_id, 'text': "💵 أرسل عدد النقاط التي تريد تحويلها وإنشاء رابط بها (الحد الأدنى 20):"})
            return

        if data == 'order_rshq':
            bot('sendMessage', {
                'chat_id': chat_id,
                'text': "🌐 اختر منصة التواصل الاجتماعي التي تريد رشقها:",
                'reply_markup': json.dumps({
                    'inline_keyboard': [
                        [{'text': 'تيك توك 📱', 'callback_data': 'serv|tiktok'}, {'text': 'إنستغرام 📸', 'callback_data': 'serv|instagram'}],
                        [{'text': 'تليجرام ✈️', 'callback_data': 'serv|telegram'}, {'text': 'يوتيوب 🎥', 'callback_data': 'serv|youtube'}],
                        [{'text': 'رجوع 🔙', 'callback_data': 'bak'}]
                    ]
                })
            })
            return

        if data.startswith('serv|'):
            platform = data.split('|')[1]
            bot('sendMessage', {
                'chat_id': chat_id,
                'text': f"🛒 اختر الخدمة المطلوبة لمنصة {platform.upper()}:",
                'reply_markup': json.dumps({
                    'inline_keyboard': [
                        [{'text': 'متابعين حقيقيين (100 نقطة)', 'callback_data': f'runrshq|{platform}|100'}],
                        [{'text': 'لايكات وإعجابات سريعة (50 نقطة)', 'callback_data': f'runrshq|{platform}|50'}],
                        [{'text': 'مشاهدات فائقة السرعة (10 نقاط)', 'callback_data': f'runrshq|{platform}|10'}]
                    ]
                })
            })
            return

        if data.startswith('runrshq|'):
            _, platform, price = data.split('|')
            rshq = load_json(RSHQ_FILE)
            user_coin = rshq.get("coin", {}).get(str(from_id), 0)
            if user_coin >= int(price):
                rshq["coin"][str(from_id)] = user_coin - int(price)
                rshq.setdefault("mode", {})[str(from_id)] = "to"
                rshq.setdefault("tp", {})[str(from_id)] = f"view_{platform}"
                rshq.setdefault("3dd", {})[str(from_id)] = 1000
                save_json(RSHQ_FILE, rshq)
                bot('sendMessage', {'chat_id': chat_id, 'text': "🔗 تم خصم النقاط بنجاح. يرجى إرسال رابط الحساب أو المنشور المستهدف الآن:"})
            else:
                bot('sendMessage', {'chat_id': chat_id, 'text': "❌ رصيد نقاطك الحالي غير كافٍ لإتمام هذا الطلب."})
            return

        if data == 'admin':
            if from_id == ADMIN:
                send_admin_panel(chat_id, message_id, from_id)
            return

        if data == 'bak':
            rshq = load_json(RSHQ_FILE)
            coin = rshq.get("coin", {}).get(str(from_id), 0)
            bot_tlb = rshq.get("bot_tlb", 0)
            send_start_message(chat_id, from_id, name, coin, bot_tlb)
            return

        if data == 'abcd':
            if from_id == ADMIN:
                write_file(BOT_TXT_FILE, "متوقف")
                bot('sendMessage', {'chat_id': chat_id, 'text': "🔒 تم قفل وتعطيل البوت بنجاح للأعضاء."})
            return

        if data == 'abcde':
            if from_id == ADMIN:
                write_file(BOT_TXT_FILE, "مفتوح")
                bot('sendMessage', {'chat_id': chat_id, 'text': "🔓 تم فتح وتفعيل البوت بنجاح للاستخدام العادي."})
            return

        if data == 'for':
            if from_id == ADMIN:
                write_file(MSG_FILE, "on")
                bot('sendMessage', {'chat_id': chat_id, 'text': "✍️ أرسل رسالتك النصية الآن ليتم إذاعتها وبثها لكل الأعضاء المسجلين بالخلفية:"})
            return

        if data == 'lIllabbas':
            if from_id == ADMIN:
                rshq = load_json(RSHQ_FILE)
                rshq.setdefault("mode", {})[str(from_id)] = "coins"
                save_json(RSHQ_FILE, rshq)
                bot('sendMessage', {'chat_id': chat_id, 'text': "🆔 أرسل الـ Telegram ID الخاص بالمستخدم المستهدف لتعديل نقاطه:"})
            return

# ========== دوال الواجهات ==========
def send_start_message(chat_id, from_id, name, coin, bot_tlb):
    text = f"✨ أهلاً بك يا {name} في بوت الرشق المتكامل الخاص بك مائة بالمائة مجاناً.\n\n💰 رصيد نقاطك الحالي: *{coin}* نقطة\n📊 إجمالي طلبات البوت الكلية: *{bot_tlb}* طلب"
    keyboard = [
        [{'text': '🚀 طلب خدمات رشق جديدة', 'callback_data': 'order_rshq'}],
        [{'text': '🎯 تجميع نقاط مجانية', 'callback_data': 'collect'}, {'text': '🎟 تفعيل كود الهدية', 'callback_data': 'gift_code'}],
        [{'text': '💳 تحويل رصيد نقاط', 'callback_data': 'transfer_coin'}]
    ]
    if from_id == ADMIN:
        keyboard.append([{'text': '⚙️ لوحة الإدارة والأدمن', 'callback_data': 'admin'}])
        
    bot('sendMessage', {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown',
        'reply_markup': json.dumps({'inline_keyboard': keyboard})
    })

def send_admin_panel(chat_id, message_id, from_id):
    text = "🛠 مرحباً بك في لوحة التحكم الإدارية للبوت الخاص بك:"
    keyboard = [
        [{'text': '📢 إرسال إذاعة عامة للأعضاء', 'callback_data': 'for'}],
        [{'text': '➕ إضافة / خصم نقاط لعضو', 'callback_data': 'lIllabbas'}],
        [{'text': '🔓 فتح البوت', 'callback_data': 'abcde'}, {'text': '🔒 قفل البوت', 'callback_data': 'abcd'}],
        [{'text': 'القائمة الرئيسية للمستخدم 🔙', 'callback_data': 'bak'}]
    ]
    bot('sendMessage', {
        'chat_id': chat_id,
        'text': text,
        'reply_markup': json.dumps({'inline_keyboard': keyboard})
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
