import os
import sys
import time
import threading
from flask import Flask

# ====================== НАЛАШТУВАННЯ ======================
BLOCKED_SITES = [
    "facebook.com", "www.facebook.com",
    "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be",
    "instagram.com", "www.instagram.com",
    "tiktok.com", "www.tiktok.com",
    "twitter.com", "x.com", "www.twitter.com"
]

REDIRECT_TO = "https://google.com"
HOSTS_PATH = "/etc/hosts"
REDIRECT_IP = "127.0.0.1" # Тільки IP! Без http і портів.

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def blocked_page(path):
    return f'''
    <html>
    <head><meta charset="utf-8"><title>Не витрачай час!</title></head>
    <body style="font-family:Arial;background:#0d1117;color:white;text-align:center;padding:100px;">
        <h1 style="font-size:50px; color:#ff4757;">"Не витрачай час на Хуйню"</h1>
        <p style="font-size:24px; color:#747d8c; margin-bottom:40px;">— Ірина Сацюк</p>
        <div style="background:#161b22; padding:40px; border-radius:20px; display:inline-block; border:1px solid #30363d;">
            <h2 style="color:#2ed573;">Твоя задача: Теорія ймовірності</h2>
            <p style="font-size:20px;">Пройди матеріал, щоб отримати доступ.</p>
            <a href="http://localhost:3000" 
               style="display:inline-block;background:#3742fa;color:white;padding:15px 30px;
                      font-size:20px;border-radius:10px;text-decoration:none;margin-top:20px;font-weight:bold;">
               🚀 Вчити теорію
            </a>
        </div>
    </body>
    </html>
    '''

def check_sudo():
    if os.geteuid() != 0:
        print("❌ Потрібні права sudo! Запусти скрипт через: sudo python3 script.py")
        sys.exit(1)

def block_sites():
    try:
        with open(HOSTS_PATH, "r") as f:
            content = f.read()

        with open(HOSTS_PATH, "a") as f:
            for site in BLOCKED_SITES:
                entry = f"{REDIRECT_IP} {site}"
                if entry not in content:
                    f.write(f"\n{entry}")
                    print(f"✅ Заблоковано: {site}")
        
        # Flush DNS для macOS
        os.system("sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder")
    except Exception as e:
        print(f"Помилка при записі в hosts: {e}")

def unblock_sites():
    try:
        with open(HOSTS_PATH, "r") as f:
            lines = f.readlines()
        with open(HOSTS_PATH, "w") as f:
            for line in lines:
                if not any(site in line for site in BLOCKED_SITES):
                    f.write(line)
        print("✅ Сайти розблоковано!")
        os.system("sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder")
    except Exception as e:
        print(f"Помилка розблокування: {e}")

if __name__ == "__main__":
    check_sudo()
    block_sites()

    def run_server():
        # Запускаємо на 443 порту для перехоплення HTTPS
        # Увага: браузер ВСЕ ОДНО покаже попередження SSL без mitmproxy сертифіката
        app.run(host="127.0.0.1", port=443, ssl_context='adhoc')

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    print("\n🔴 Блокувальник активний! Натисни Ctrl+C для виходу.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Зупиняю...")
        unblock_sites()