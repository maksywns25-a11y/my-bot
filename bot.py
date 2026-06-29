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

# ========== دوال مساعدة ==========
def bot(method, datas=None):
    if datas is None:
        datas = {}
    url = f"[https://api.telegram.org/bot](https://api.telegram.org/bot){API_KEY}/{method}"
    try:
        if method in ["sendphoto", "senddocument"]:
            # في حالة إرسال ملفات، نستخدم files parameter
            if 'photo' in datas or 'document' in datas:
                # نتعامل مع الملفات بشكل منفصل
                if 'photo' in datas:
                    datas['photo'] = datas['photo']
                if 'document' in datas:
                    datas['document'] = datas['document']
            response = requests.post(url, data=datas)
        else:
            response = requests.post(url, data=datas)
        if response.status_code == 200:
            return response.json()
        else:
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
    return BOT_USERNAME

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

# ========== تهيئة الملفات ==========
os.makedirs("data", exist_ok=True)

# ملفات البيانات الأساسية
if not os.path.exists("saiko.json"):
    save_json("saiko.json", {"gch": "❎"})
if not os.path.exists("abbas.json"):
    write_file("abbas.json", "")
if not os.path.exists("ad.json"):
    append_file("ad.json", str(ADMIN))
if not os.path.exists("rshq.json"):
    save_json("rshq.json", {"rshaq": "on"})
if not os.path.exists("bot.txt"):
    write_file("bot.txt", "مفتوح")
if not os.path.exists("skor.php"):
    write_file("skor.php", "معطل ⚠️")
if not os.path.exists("abbas09.json"):
    save_json("abbas09.json", {"addmessage": 0, "messagee": 0})

# ========== دوال معالجة النصوص ==========
def get_text(message):
    return message.get('text') if message else None

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

def get_data(update):
    if 'callback_query' in update:
        return update['callback_query'].get('data')
    return None

def get_name(update):
    if 'message' in update and update['message']:
        from_user = update['message'].get('from', {})
        return from_user.get('first_name', '')
    elif 'callback_query' in update and update['callback_query']:
        from_user = update['callback_query'].get('from', {})
        return from_user.get('first_name', '')
    return ''

def get_username(update):
    if 'message' in update and update['message']:
        from_user = update['message'].get('from', {})
        return from_user.get('username', '')
    elif 'callback_query' in update and update['callback_query']:
        from_user = update['callback_query'].get('from', {})
        return from_user.get('username', '')
    return ''

def get_photo(update):
    if 'message' in update and update['message']:
        return update['message'].get('photo')
    return None

def get_caption(update):
    if 'message' in update and update['message']:
        return update['message'].get('caption', '')
    return ''

def get_document(update):
    if 'message' in update and update['message']:
        return update['message'].get('document')
    return None

def get_forward_from_chat(update):
    if 'message' in update and update['message']:
        return update['message'].get('forward_from_chat')
    return None

# ========== دوال التحقق من العضوية ==========
def is_member(chat_id, user_id):
    url = f"[https://api.telegram.org/bot](https://api.telegram.org/bot){API_KEY}/getChatMember"
    params = {"chat_id": chat_id, "user_id": user_id}
    try:
        r = requests.get(url, params=params)
        data = r.json()
        if data.get('ok') and data.get('result'):
            status = data['result'].get('status')
            return status not in ['left', 'kicked'] and 'status' not in ['left', 'kicked']
        else:
            return False
    except:
        return False

# ========== معالجة Webhook ==========
@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if not update:
        return 'ok', 200

    # بدء المعالجة
    process_update(update)
    return 'ok', 200

def process_update(update):
    # جلب المتغيرات الأساسية
    message = update.get('message')
    callback_query = update.get('callback_query')
    chat_id = get_chat_id(update)
    from_id = get_from_id(update)
    message_id = get_message_id(update)
    data = get_data(update)
    text = get_text(message) if message else None
    name = get_name(update)
    username = get_username(update)

    # إذا لم يكن هناك chat_id أو from_id، نتجاهل
    if not chat_id or not from_id:
        return

    # التحقق من نوع الرسالة (خاص أم لا)
    if message:
        chat_type = message['chat'].get('type')
    else:
        chat_type = None

    # ========== معالجة الاشتراك الإجباري ==========
    # القناة الثابتة
    ch = "@zaidmfj"
    if message and not is_member(ch, from_id):
        bot('sendMessage', {
            'chat_id': chat_id,
            'text': f"🚸| عذرا عزيزي\n🔰| عليك الاشتراك بقناة البوت لتتمكن من استخدامه\n\n- [اضغط هنا للشتراك في القناة](https://t.me/zaidmfj)\n\n‼️| اشترك ثم ارسل /start",
            'parse_mode': 'MarkDown',
            'disable_web_page_preview': True
        })
        return

    # قناة الاشتراك العامة/الخاصة (من ملف uuser.php)
    uuser = read_file("uuser.php").strip()
    if uuser and uuser != "" and message and not is_member(uuser, from_id):
        bot('sendMessage', {
            'chat_id': chat_id,
            'text': f"🚸| عذرا عزيزي\n🔰| عليك الاشتراك بقناة البوت لتتمكن من استخدامه\n\n- {uuser}\n\n‼️| اشترك ثم ارسل /start"
        })
        return

    # ========== تسجيل الأعضاء ==========
    users = file_lines("abbas.json")
    if message and from_id not in users:
        append_file("abbas.json", f"{from_id}\n")

    # ========== تحديث الإحصائيات ==========
    abbas09 = load_json("abbas09.json")
    if message:
        if from_id == ADMIN:
            abbas09['addmessage'] = abbas09.get('addmessage', 0) + 1
        else:
            abbas09['messagee'] = abbas09.get('messagee', 0) + 1
        save_json("abbas09.json", abbas09)

    # ========== إحصاء الأعضاء اليوم ==========
    d = datetime.now().strftime('%a')
    day_file = f"{d}.txt"
    day_users = file_lines(day_file)
    if message and from_id not in day_users:
        append_file(day_file, f"{from_id}\n")
    # حذف ملفات الأيام السابقة (لنحاكي الكود الأصلي)
    if d == "Sat": os.remove("Fri.txt") if os.path.exists("Fri.txt") else None
    if d == "Sun": os.remove("Sat.txt") if os.path.exists("Sat.txt") else None
    if d == "Mon": os.remove("Sun.txt") if os.path.exists("Sun.txt") else None
    if d == "Tue": os.remove("Mon.txt") if os.path.exists("Mon.txt") else None
    if d == "Wed": os.remove("The.txt") if os.path.exists("The.txt") else None
    if d == "Thu": os.remove("Wedtxt") if os.path.exists("Wedtxt") else None
    if d == "Fri": os.remove("Thu.txt") if os.path.exists("Thu.txt") else None

    # ========== إضافة الأدمن في أول مرة ==========
    adminss = file_lines("ad.json")
    if message and str(ADMIN) not in adminss:
        append_file("ad.json", f"{ADMIN}\n")

    # ========== متغيرات عامة ==========
    all_users = len(file_lines("abbas.json"))
    today_users = len(day_users)
    bot_status = read_file("bot.txt").strip()
    skor = read_file("skor.php").strip()

    # ========== معالجة الأوامر النصية ==========
    if text:
        # === أمر /start ===
        if text.startswith('/start'):
            # معالجة رابط الدعوة
            e1 = text.replace('/start', '').strip()
            if e1 and e1.isdigit() and '#Bero' not in text:
                rshq = load_json("rshq.json")
                if e1 != str(from_id):
                    if from_id not in rshq.get("3thu", []):
                        bot('sendMessage', {
                            'chat_id': chat_id,
                            'text': "لقد دخلت لرابط الدعوه الخاص بصديقك وحصل علي *5* نقاط",
                            'parse_mode': 'Markdown'
                        })
                        # إضافة نقاط للمدعو
                        rshq.setdefault("coin", {})
                        rshq["coin"][str(e1)] = rshq["coin"].get(str(e1), 0) + 5
                        rshq.setdefault("mshark", {})
                        rshq["mshark"][str(e1)] = rshq["mshark"].get(str(e1), 0) + 1
                        rshq.setdefault("3thu", []).append(from_id)
                        save_json("rshq.json", rshq)
            # عرض رسالة الترحيب
            coin = load_json("rshq.json").get("coin", {}).get(str(from_id), 0)
            bot_tlb = load_json("rshq.json").get("bot_tlb", 0)
            send_start_message(chat_id, from_id, name, coin, bot_tlb)
            return

        # === أمر /admin ===
        if text == '/admin' and chat_id == ADMIN:
            send_admin_panel(chat_id, message_id, from_id)
            return

        # === معالجة حالة k088 (رفع ادمن) ===
        k088 = read_file("data/k088.txt").strip()
        if k088 == "k088" and from_id == ADMIN:
            if text != "/start":
                adminss = file_lines("ad.json")
                if text not in adminss:
                    append_file("ad.json", f"{text}\n")
                    write_file("data/k088.txt", "none")
                    bot('sendMessage', {'chat_id': chat_id, 'text': f"تم رفع العضو {text}"})
                    bot('sendMessage', {'chat_id': int(text), 'text': "تم رفعك ادمن في البوت"})
                else:
                    write_file("data/k088.txt", "none")
                    bot('sendMessage', {'chat_id': chat_id, 'text': "العضو ادمن بالفعل"})

        # === معالجة رسالة الاستارت (q1) ===
        q1 = read_file("data/q1.txt").strip()
        if q1 == "q1" and text != "/start" and from_id == ADMIN:
            write_file("data/q1.txt", "none")
            write_file("q2.txt", text)
            bot('sendMessage', {'chat_id': chat_id, 'text': "تم التعين بنجاح"})

        # === معالجة إذاعة رسالة ===
        msg = read_file("msg.php").strip()
        if msg == "on":
            for uid in file_lines("abbas.json"):
                if uid:
                    bot('sendMessage', {'chat_id': int(uid), 'text': text})
            bot('sendMessage', {
                'chat_id': chat_id,
                'text': f"حسنا عزيزي\nتم عمل اذاعه بنجاح\nالى ( {all_users} ) مشترك",
                'reply_markup': json.dumps({
                    'inline_keyboard': [[{'text': 'رجوع', 'callback_data': 'bak'}]]
                })
            })
            os.remove("msg.php") if os.path.exists("msg.php") else None
            return

        # === معالجة إذاعة توجيه ===
        forward = read_file("forward.php").strip()
        if forward == "on":
            pass

        # === معالجة إذاعة ميديا ===
        midea = read_file("midea.php").strip()

        # === معالجة إذاعة صورة ===
        photoi = read_file("photoi.php").strip()

        # === معالجة إذاعة انلاين ===
        inlin = read_file("inlin.php").strip()

        # === معالجة رابط القناة (link) ===
        link = read_file("link2.php").strip()
        if link == "on":
            if re.search(r'(http|https|t\.me|telegram\.me)', text, re.IGNORECASE):
                write_file("link2.php", text)
                write_file("skor.php", "مفعل ✅")
                bot('sendMessage', {
                    'chat_id': chat_id,
                    'text': "حسنا عزيزي\nتم تفعيل الاشتراك بنجاح",
                    'reply_markup': json.dumps({
                        'inline_keyboard': [[{'text': 'اتمام العملية', 'callback_data': 'bak'}]]
                    })
                })
            else:
                bot('sendMessage', {'chat_id': chat_id, 'text': "عذرا عزيزي\nقم بأرسال الرابط بصورة صحيحه"})
            return

        # === معالجة يوزر القناة (uuser) ===
        uuser = read_file("uuser.php").strip()
        if uuser == "on":
            if re.search(r'@|#', text):
                write_file("uuser.php", text)
                write_file("skor.php", "مفعل ✅")
                bot('sendMessage', {
                    'chat_id': chat_id,
                    'text': "حسنا عزيزي\nتم تفعيل الاشتراك بنجاح",
                    'reply_markup': json.dumps({
                        'inline_keyboard': [[{'text': 'اتمام العملية ⏱', 'callback_data': 'bak'}]]
                    })
                })
            else:
                bot('sendMessage', {'chat_id': chat_id, 'text': "عذرا عزيزي\nقم بأرسال يوزر بصورة صحيحه"})
            return

        # === معالجة كود الهدية (hdia) ===
        rshq = load_json("rshq.json")
        mode = rshq.get("mode", {}).get(str(from_id))
        if mode == "hdia":
            if text in rshq and rshq[text].startswith("on|"):
                points = int(rshq[text].split('|')[1])
                if from_id not in rshq.get("mehdia", {}).get(text, {}):
                    rshq.setdefault("mehdia", {})
                    rshq["mehdia"].setdefault(str(from_id), {})[text] = "on"
                    rshq.setdefault("coin", {})
                    rshq["coin"][str(from_id)] = rshq["coin"].get(str(from_id), 0) + points
                    save_json("rshq.json", rshq)
                    bot('sendMessage', {
                        'chat_id': chat_id,
                        'text': f"~ لقد حصلت علي {points} نقطه من كود الهديه",
                        'reply_markup': json.dumps({
                            'inline_keyboard': [[{'text': 'رجوع', 'callback_data': 'tobot'}]]
                        })
                    })
                else:
                    bot('sendMessage', {'chat_id': chat_id, 'text': "انت مستخدم الكود من قبل"})
            else:
                bot('sendMessage', {'chat_id': chat_id, 'text': "كود الهدية خطأ"})
            return

        # === معالجة تحويل النقاط (transer) ===
        if mode == "transer" and is_numeric(text):
            coin = rshq.get("coin", {}).get(str(from_id), 0)
            if coin >= int(text) and int(text) >= 20:
                MakLink = ''.join(random.choices('AbCdEfGhIjKlMnOpQrStU12345689807', k=13))
                new_coin = coin - int(text)
                rshq["coin"][str(from_id)] = new_coin
                rshq.setdefault("thoiler", {})
                rshq["thoiler"][MakLink] = {"coin": int(text), "to": from_id}
                save_json("rshq.json", rshq)
                bot('sendMessage', {
                    'chat_id': chat_id,
                    'text': f"تم صنع رابط تحويل بقيمه {text} نقاط 💲\n- وتم استقطاع *{text}* من نقاطك ➖\n\nالرابط : [https://t.me/](https://t.me/){get_bot_username()}?start=Bero{MakLink}\n\nايدي وصل التحويل : `{base64.b64encode(MakLink.encode()).decode()}`\n\nصار عدد نقاطك : *{new_coin}*",
                    'parse_mode': 'Markdown',
                    'reply_markup': json.dumps({
                        'inline_keyboard': [[{'text': 'رجوع', 'callback_data': 'tobot'}]]
                    })
                })
            else:
                bot('sendMessage', {'chat_id': chat_id, 'text': "نقاطك غير كافية أو أقل من 20", 'reply_markup': json.dumps({'inline_keyboard': [[{'text': 'رجوع', 'callback_data': 'tobot'}]]})})
            return

        # === معالجة coins (إضافة/خصم نقاط) ===
        if mode == "coins":
            rshq['mode'][str(from_id)] = "coins2"
            rshq['id'][str(from_id)] = text
            save_json("rshq.json", rshq)
            bot('sendMessage', {
                'chat_id': chat_id,
                'text': "ارسل عدد النقاط لاضافته للشخص\nاذا تريد تخصم كتب ويا -",
                'reply_markup': json.dumps({
                    'inline_keyboard': [[{'text': 'رجوع', 'callback_data': 'admin'}]]
                })
            })
            return

        if mode == "coins2" and from_id == ADMIN:
            target_id = rshq.get('id', {}).get(str(from_id))
            if target_id:
                rshq.setdefault("coin", {})
                rshq["coin"][target_id] = rshq["coin"].get(target_id, 0) + int(text)
                rshq['mode'][str(from_id)] = None
                save_json("rshq.json", rshq)
                bot('sendMessage', {
                    'chat_id': chat_id,
                    'text': f"تم اضافه {text} ل {target_id}",
                    'reply_markup': json.dumps({
                        'inline_keyboard': [[{'text': 'رجوع', 'callback_data': 'admin'}]]
                    })
                })
            return

        # === معالجة hdiMk (صنع كود هدية) ===
        if mode == "hdiMk" and from_id == ADMIN and is_numeric(text):
            rnd = random.randint(999, 99999)
            rshq[f"Bero{rnd}"] = f"on|{text}"
            rshq['mode'][str(from_id)] = None
            save_json("rshq.json", rshq)
            bot('sendMessage', {
                'chat_id': chat_id,
                'text': f"تم اضافة كود هدية جديد\n- - - - - - - - - - - - - - - - - - \n الكود : `Bero{rnd}`\n عدد النقاط : {text}\n- - - - - - - - - - - - - - - - - - \n بوت الرشق المجاني : [@{get_bot_username()}]",
                'parse_mode': 'Markdown',
                'reply_markup': json.dumps({
                    'inline_keyboard': [[{'text': 'رجوع', 'callback_data': 'admin'}]]
                })
            })
            return

        # === معالجة shhn (شحن تلقائي) ===
        shhn = rshq.get('shhn', {}).get(str(from_id))
        if shhn and is_numeric(text):
            if shhn == "thoil":
                TypeShhn = "تحويل الرصيد"
                ws = f"رقمك : {text}"
                mshkl = "مامحول الرصيد سيتم حظرك نهائيا من البوت"
            elif shhn == "cart":
                TypeShhn = "ارسال كارت اسيا"
                ws = f"رقم الكارت : `{text}`"
                mshkl = "ارسلت رقم الكارت غلط سيتم حظرك نهائيا من البوت"
            else:
                return
            bot('sendMessage', {
                'chat_id': chat_id,
                'text': f"نوع طلبك : {TypeShhn}\n{ws}\nسيتم مراجعه طلبك خلال 24 ساعه في حال كنت {mshkl}",
                'parse_mode': 'Markdown',
                'reply_markup': json.dumps({
                    'inline_keyboard': [[{'text': 'رجوع', 'callback_data': 'tobot'}]]
                })
            })
            bot('sendMessage', {
                'chat_id': ADMIN,
                'text': f"طلب شحن تلقائي ✅\n\nالشحن عن طريق : {TypeShhn}\n\n{ws.replace('رقمك', 'رقم الشخص')}",
                'parse_mode': 'Markdown',
                'reply_markup': json.dumps({
                    'inline_keyboard': [[{'text': 'تأكيد طلبه ⚡', 'callback_data': f"ok|{from_id}"}]]
                })
            })
            del rshq['shhn'][str(from_id)]
            save_json("rshq.json", rshq)
            return

        # === معالجة shneru (تأكيد شحن من الأدمن) ===
        mode = rshq.get('mode', {}).get(str(from_id))
        if mode == "shneru" and from_id == ADMIN and is_numeric(text):
            target = rshq.get('coi', {}).get(str(from_id))
            if target:
                rshq.setdefault("coin", {})
                rshq["coin"][target] = rshq["coin"].get(target, 0) + int(text)
                rshq['mode'][str(from_id)] = None
                rshq['coi'][str(from_id)] = None
                save_json("rshq.json", rshq)
                bot('sendMessage', {
                    'chat_id': chat_id,
                    'text': f"تم تأكيد طلبه في الشحن التلقائي وتم ارسال {text} نقاط ل {target}",
                    'reply_markup': json.dumps({
                        'inline_keyboard': [[{'text': 'رجوع', 'callback_data': 'back'}]]
                    })
                })
                bot('sendMessage', {
                    'chat_id': int(target),
                    'text': f"~ تم تأكيد طلبك بنجاح (شحن التلقائي) ✅\n\nوتم ارسال {text} نقاط لحسابك"
                })
            return

        # === معالجة infotlb (معلومات طلب) ===
        if mode == "infotlb" and is_numeric(text):
            order_id = rshq.get("order", {}).get(text)
            if order_id:
                req = requests.get(f"[https://smmlox.com/api/v2?key=](https://smmlox.com/api/v2?key=){API_TOK}&action=status&order={order_id}")
                if req.status_code == 200:
                    res = req.json()
                    startcc = res.get('start_count', 0)
                    remains = res.get('remains', 0)
                    status = "طلب مكتمل 🟢" if remains == 0 else "قيد الانتضار ...."
                    bot('sendMessage', {
                        'chat_id': chat_id,
                        'text': f"معلومات الطلب ،\nحاله الطلب : {status}\nالعدد قبل الرشق : {startcc}",
                        'parse_mode': 'Markdown',
                        'reply_markup': json.dumps({
                            'inline_keyboard': [
                                [{'text': 'تحديث', 'callback_data': f"updates|{order_id}"}],
                                [{'text': 'رجوع', 'callback_data': 'tobot'}]
                            ]
                        })
                    })
                    rshq['mode'][str(from_id)] = None
                    save_json("rshq.json", rshq)
            return

        # === معالجة to (طلب رشق) ===
        if mode == "to":
            tp = rshq.get('tp', {}).get(str(from_id))
            if not tp:
                return
            service_map = {
                'thbt': 9650, 'mthbt': 9650, 'hq': 9650,
                'view': 5132, 'like': 9168, 'likrels': 8303,
                'vuerils': 7921, 'foloarb': 5166, 'commlik': 5788,
                'realkil': 5087, 'mixfla': 5081, 'ralvew': 5198,
                'spefom': 7871, 'qwaty': 9042, 'livty': 5919,
                'peptri': 8504, 'peobsvh': 10266, 'pelbxsvc': 10316,
                'vionew': 10401, 'viwefiv': 10402, 'commionb': 8584,
                'indiaco': 8587, 'taswet': 9481, 'thya': 8593,
                'nothya': 8594, 'hartthu': 8595, 'firerak': 8596,
                'starreak': 8598, 'surarek': 8597, 'demareak': 8599,
                'sorkre': 8600, 'smirseb': 8601, 'kakarekt': 8602,
                'targrekt': 8603, 'fackyourect': 10559,
                'facepeb': 10540, 'favelik': 6020, 'faceegbo': 6043,
                'facflk': 6046, 'facharch': 7094, 'sminshfacwc': 7095,
                'wowrafv': 7098, 'sadface': 7096, 'angrefaceb': 7097,
                'carefacec': 7099, 'comlikfav': 6053, 'viewvidfa': 6057,
                'actoreface': 10383, 'viewyoutube': 6128,
                'viewralyou': 6088, 'vierahfyou': 6139,
                'likecomyo': 8372, 'likeyoufa': 6180,
                'peopltik': 10498, 'liketikbr': 6267,
                'tikviesto': 10451, 'freeviewtik': 9308,
                'livliktk': 9619, 'sahretik': 6285,
                'pepltwi': 6307, 'taswttwi': 6336,
                'vidvitwi': 6349, 'menhtwi': 8634
            }
            service_id = service_map.get(tp)
            if not service_id:
                return
            quantity = rshq.get('3dd', {}).get(str(from_id), {}).get(str(from_id), 0)
            req = requests.get(f"[https://smmlox.com/api/v2?key=](https://smmlox.com/api/v2?key=){API_TOK}&action=add&service={service_id}&link={text}&quantity={quantity}")
            if req.status_code == 200:
                res = req.json()
                order = res.get('order')
                rnd_order = random.randint(9999999, 9999999999)
                bot('sendMessage', {
                    'chat_id': chat_id,
                    'text': f"تم ارسال طلبك بنجاح ✅\n- - - - - - - - - - - - - - - - - - \nرقم طلبك : `{rnd_order}`\nالعدد : *{quantity}*\n\nسيتم ارسال خلال دقائق",
                    'parse_mode': 'Markdown',
                    'reply_markup': json.dumps({
                        'inline_keyboard': [
                            [{'text': 'طلب مراجعه الطلب ✅', 'callback_data': f"sendrq|{order}|{rnd_order}|{rshq.get('s3rltlb', {}).get(str(from_id), 0)}"}]
                        ]
                    })
                })
                bot('sendMessage', {
                    'chat_id': ADMIN,
                    'text': f"⌯طلب جديد ⌯\n▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱▱\nمعلومات العضو \nايديه : `{from_id}`\nيوزره : @{username}\nاسمه : [{name}](tg://user?id={chat_id})\n\nمعلومات الطلب ~\nايدي الطلب : `{rnd_order}`\nالعدد {quantity}\n\nنقاطه : {rshq.get('coin', {}).get(str(from_id), 0)}",
                    'parse_mode': 'Markdown',
                    'reply_markup': json.dumps({
                        'inline_keyboard': [
                            [{'text': 'ترجيع نقاطه', 'callback_data': f"ins|{from_id}|{rshq.get('coinn', 0)}"}],
                            [{'text': 'طلب تعويض تلقائيا', 'callback_data': f"tEwth|{order}"}],
                            [{'text': 'تصفير نقاطه', 'callback_data': f"msft|{from_id}"}]
                        ]
                    })
                })
                bot('sendMessage', {
                    'chat_id': CHNL,
                    'text': f"✅ اكتمل طـلب الخدمة بنجاح .\n- - - - - - - - - - - - - - - - - - \nايدي الطلب : `{rnd_order}`\nنوع الطلب :{rshq.get('tlbia', {}).get(str(from_id), '')}\nسعر الطلب :{rshq.get('s3rltlb', {}).get(str(from_id), 0)}\nالعدد {quantity}\nحساب المشتري : [{name}](tg://user?id={chat_id})",
                    'parse_mode': 'Markdown',
                    'reply_markup': json.dumps({
                        'inline_keyboard': [
                            [{'text': 'Social Plus ➕', 'url': f"[https://t.me/](https://t.me/){get_bot_username()}"}]
                        ]
                    })
                })
                rshq.setdefault("order", {})[str(rnd_order)] = order
                rshq['3dd'][str(from_id)][str(from_id)] = None
                rshq['mode'][str(from_id)] = None
                rshq['bot_tlb'] = rshq.get('bot_tlb', 0) + 1
                save_json("rshq.json", rshq)
            return

        # === معالجة روابط التحويل (start Bero) ===
        if text.startswith('/start Bero'):
            code = text.replace('/start Bero', '').strip()
            rshq = load_json("rshq.json")
            if code in rshq.get('thoiler', {}) and rshq['thoiler'][code].get('to'):
                coin = rshq['thoiler'][code]['coin']
                rshq.setdefault("coin", {})
                rshq["coin"][str(from_id)] = rshq["coin"].get(str(from_id), 0) + coin
                bot('sendMessage', {
                    'chat_id': chat_id,
                    'text': f"لقد حصلت علي *{coin}* نقاط من رابط التحويل",
                    'parse_mode': 'Markdown',
                    'reply_markup': json.dumps({
                        'inline_keyboard': [[{'text': 'رجوع', 'callback_data': 'tobot'}]]
                    })
                })
                bot('sendMessage', {
                    'chat_id': rshq['thoiler'][code]['to'],
                    'text': f"تحويل مكتمل 💯\n\nمعلومات الي دخل للرابط ✅\nاسمه : [{name}](tg://user?id={chat_id})\nايديه : `{from_id}`\n\nوتم تحويل {coin} نقاط لحسابه",
                    'parse_mode': 'Markdown'
                })
                del rshq['thoiler'][code]
                save_json("rshq.json", rshq)
            else:
                bot('sendMessage', {'chat_id': from_id, 'text': "رابط التحويل هذا غير صالح ❌"})
            return

    # ========== معالجة callback_query ==========
    if callback_query:
        data = callback_query.get('data')
        if not data:
            return
        parts = data.split('|')
        main = parts[0]

        # === القائمة الرئيسية ===
        if main == 'bak':
            send_main_menu(chat_id, message_id, from_id)
            return

        # === قفل/فتح البوت ===
        if main == 'abcd':
            write_file("bot.txt", "متوقف")
            bot('editMessageText', {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': "- اهلا بك عزيزي\n- تم قفل البوت\n- /start",
                'reply_markup': json.dumps({
                    'inline_keyboard': [[{'text': 'الصفحه الرئيسيه', 'callback_data': 'bak'}]]
                })
            })
            return
        if main == 'abcde':
            write_file("bot.txt", "مفتوح")
            bot('editMessageText', {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': "- اهلا بك عزيزي\n- تم فتح البوت \n- /start",
                'reply_markup': json.dumps({
                    'inline_keyboard': [[{'text': 'الصفحه الرئيسيه', 'callback_data': 'bak'}]]
                })
            })
            return

        # === قسم الادمن ===
        if main == 'lIllabbas':
            bot('editMessageText', {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': "اهلا",
                'reply_markup': json.dumps({
                    'inline_keyboard': [
                        ['• رفع ادمن •', 'callback_data', 'adl'],
                        ['• اخر الادمن •', 'callback_data', 'addmin'],
                        ['• حذف الادمنيه •', 'callback_data', 'delateaddmin']
                    ]
                })
            })
            return

        if main == 'adl':
            bot('editMessageText', {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': "قم بارسال ايدي العضو"
            })
            write_file("data/k088.txt", "k088")
            return

        if main == 'addmin':
            adminss = file_lines("ad.json")
            text_list = ""
            for i in range(1, 6):
                idx = len(adminss) - i
                if idx >= 0:
                    text_list += f"{i} - {adminss[idx]}\n"
            bot('editMessageText', {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': f"اخر خمس ادمنيه :\n{text_list}",
                'reply_markup': json.dumps({
                    'inline_keyboard': [[{'text': '- الصفحه الرئيسيه.', 'callback_data': 'bak'}]]
                })
            })
            return

        if main == 'delateaddmin' and chat_id == ADMIN:
            bot('editMessageText', {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': "هل انت متاكد من الحذف",
                'reply_markup': json.dumps({
                    'inline_keyboard': [
                        [{'text': 'لا', 'callback_data': 'bak'}],
                        [{'text': 'نعم', 'callback_data': 'yesaarsslan'}]
                    ]
                })
            })
            return

        if main == 'yesaarsslan':
            os.remove("ad.json") if os.path.exists("ad.json") else None
            append_file("ad.json", str(ADMIN))
            bot('editMessageText', {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': "تم حذف الادمنيه",
                'reply_markup': json.dumps({
                    'inline_keyboard': [[{'text': 'الصفحه الرئيسيه', 'callback_data': 'bak'}]]
                })
            })
            return

        # === تفعيل/تعطيل التنبيه ===
        if main == 'ont':
            write_file("ont.php", "on")
            bot('answerCallbackQuery', {
                'callback_query_id': callback_query['id'],
                'text': "مرحبا عزيزي\nتم تفعيل الاشعارات في البوت",
                'show_alert': True
            })
            return
        if main == 'oft':
            write_file("ont.php", "off")
            bot('answerCallbackQuery', {
                'callback_query_id': callback_query['id'],
                'text': "مرحبا عزيزي\n⚠ تم تعطيل الاشعارات في البوت",
                'show_alert': True
            })
            return

        # === قسم الاذاعة ===
        if main == 'for':
            bot('editMessageText', {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': "حسنا عزيزي\nقم باختيار ما يناسبك",
                'reply_markup': json.dumps({
                    'inline_keyboard': [
                        [{'text': 'اذاعه صورة', 'callback_data': 'photoi'}],
                        [{'text': 'اذاعه رسالة', 'callback_data': 'msg'}, {'text': 'اذاعه توجيه', 'callback_data': 'forward'}],
                        [{'text': 'اذاعه ميديا', 'callback_data': 'midea'}, {'text': 'اذاعه انلاين', 'callback_data': 'inline'}],
                        [{'text': 'رجوع', 'callback_data': 'bak'}]
                    ]
                })
            })
            return

        if main == 'msg':
            write_file("msg.php", "on")
            bot('editMessageText', {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': "حسنا عزيزي\nقم بأرسال رسالتك لتحويلها لجميع المشتركين",
                'reply_markup': json.dumps({
                    'inline_keyboard': [[{'text': 'الغاء', 'callback_data': 'bak'}]]
                })
            })
            return

        if main == 'forward':
            write_file("forward.php", "on")
            bot('editMessageText', {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': "حسنا عزيزي\nقم بأرسال رسالتك لتحويلها لجميع المشتركين على شكل توجيه",
                'reply_markup': json.dumps({
                    'inline_keyboard': [[{'text': 'الغاء', 'callback_data': 'bak'}]]
                })
            })
            return

        if main == 'midea':
            write_file("midea.php", "on")
            bot('editMessageText', {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': "حسنا عزيزي\nيمكنك استخدام جميع انوع الميديا ماعدى الصوره\n(ملصق - فيديو - بصمه - ملف صوتي - ملف - متحركه - جهة اتصال)",
                'reply_markup': json.dumps({
                    'inline_keyboard': [[{'text': 'الغاء', 'callback_data': 'bak'}]]
                })
            })
            return

        if main == 'photoi':
            write_file("photoi.php", "on")
            bot('editMessageText', {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': "حسنا عزيزي\nقم بأرسال الصورة لنشرها لجميع المشتركين",
                'reply_markup': json.dumps({
                    'inline_keyboard': [[{'text': 'الغاء', 'callback_data': 'bak'}]]
                })
            })
            return

        if main == 'inline':
            write_file("inlin.php", "on")
            bot('editMessageText', {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': "حسنا عزيزي\nقم بتوجيه نص الانلاين لاقوم بنشره للمشتركين",
                'reply_markup': json.dumps({
                    'inline_keyboard': [[{'text': 'الغاء', 'callback_data': 'bak'}]]
                })
            })
            return

        # === قائمة الاشتراك ===
        if main == 'channel':
            bot('editMessageText', {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': "حسنا عزيزي\nقم بتحديد الامر لأتمكن من تنفيذه",
                'reply_markup': json.dumps({
                    'inline_keyboard': [
                        [{'text': 'قناة خاصة', 'callback_data': 'link'}],
                        [{'text': 'قناة عامة', 'callback_data': 'user'}],
                        [{'text': 'رجوع', 'callback_data': 'bak'}]
                    ]
                })
            })
            return

        if main == 'link':
            write_file("link.php", "on")
            bot('editMessageText', {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': "حسنا عزيزي\nقم برفع البوت ادمن في القناة\nثم ارسل توجيه من القناة الى هنا",
                'reply_markup': json.dumps({
                    'inline_keyboard': [[{'text': 'رجوع', 'callback_data': 'bak'}]]
                })
            })
            return

        if main == 'user':
            bot('editMessageText', {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': "حسنا عزيزي\nقم برفع البوت ادمن في القناة\nثم ارسل يوزر القناة لتفعيل الاشتراك",
                'reply_markup': json.dumps({
                    'inline_keyboard': [[{'text': 'رجوع', 'callback_data': 'bak'}]]
                })
            })
            write_file("uuser.php", "on")
            return

        # === تعطيل الاشتراك ===
        if main == 'off':
            skor = read_file("skor.php").strip()
            if skor == "معطل ⚠️":
                bot('answerCallbackQuery', {
                    'callback_query_id': callback_query['id'],
                    'text': "مرحبا عزيزي\nحالة الاشتراك الاجباري معطل\nقم بختيار - قائمةه الاشتراك .وقم بتفعيله",
                    'show_alert': True
                })
            else:
                bot('editMessageText', {
                    'chat_id': chat_id,
                    'message_id': message_id,
                    'text': "حسنا عزيزي\nحالت الاشتراك الخاص بك مفعل\nهل انت متأكد من رغبتك في تعطيل الاشتراك",
                    'reply_markup': json.dumps({
                        'inline_keyboard': [
                            [{'text': 'نعم', 'callback_data': 'yesde2'}, {'text': 'لا', 'callback_data': 'bak'}]
                        ]
                    })
                })
            return

        if main == 'yesde2':
            os.remove("uuser.php") if os.path.exists("uuser.php") else None
            os.remove("link.php") if os.path.exists("link.php") else None
            write_file("skor.php", "معطل ⚠️")
            bot('editMessageText', {
                'chat_id': chat_id,
                'message_id': message_id,
                'text': "حسنا عزيزي\nتم تعطيل الاشتراك في جميع القنواة\nيمكنك تفعيل الاشتراك لقناتك في مابعد",
                'reply_markup': json.dumps({
                    'inline_keyboard': [[{'text': 'رجوع', 'callback_data': 'bak'}]]
                })
            })
            return

# ========== دوال الواجهات القوائم ==========
def send_start_message(chat_id, from_id, name, coin, bot_tlb):
    # دالة وهمية لمحاكاة إرسال رسالة start الأصلية بناءً على منطق الكود
    text = f"مرحبا بك {name} في بوت الرشق\nنقاطك: {coin}\nعدد الطلبات الكلي: {bot_tlb}"
    bot('sendMessage', {
        'chat_id': chat_id,
        'text': text,
        'reply_markup': json.dumps({
            'inline_keyboard': [[{'text': 'لوحة التحكم بـ البوت ⚙️', 'callback_data': 'admin'}]] if from_id == ADMIN else []
        })
    })

def send_admin_panel(chat_id, message_id, from_id):
    bot('sendMessage', {
        'chat_id': chat_id,
        'text': "مرحباً بك في لوحة الإدارة",
        'reply_markup': json.dumps({
            'inline_keyboard': [
                [{'text': 'قسم الإذاعة', 'callback_data': 'for'}, {'text': 'الاشتراك الإجباري', 'callback_data': 'channel'}],
                [{'text': 'تعطيل الاشتراك', 'callback_data': 'off'}, {'text': 'إدارة الأدمنية', 'callback_data': 'lIllabbas'}]
            ]
        })
    })

def send_main_menu(chat_id, message_id, from_id):
    bot('sendMessage', {
        'chat_id': chat_id,
        'text': "القائمة الرئيسية"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
