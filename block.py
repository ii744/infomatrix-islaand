import os
import json
import random
import threading # Додали для фонової генерації
import time
from mitmproxy import http

# Імпортуємо нашого агента (переконайся, що файл agent_matrix.py лежить у цій же папці)
import agent_matrix

class KairosProxy:
    def __init__(self):
        self.blocked_sites_file = "blocked_sites.json"
        self.load_sites()
        
        self.settings_html = "index-ai.html"
        self.settings_css = "style-ai.css"

        # --- Змінні для ШІ-генерації ---
        self.is_generating = False
        self.generated_lesson_html = None

        self.quotes = [
            {"text": "«Не витрачай час на ХУЙНЮ»", "author": "Ірина Сацюк"},
            {"text": "«Не важно»", "author": "Ірина Сацюк"},
            {"text": "«Клас! ой це не додавай»", "author": "Ірина Сацюк"},
            {"text": "«хзпавхпїхавпхїа»", "author": "Ірина Сацюк"},
            {"text": "«...»", "author": "Ірина Сацюк"},
            {"text": "Бачиш, що я плачу", "author": "Ірина Сацюк"},
            {"text": "«Кхе кхе»", "author": "Ірина Сацюк"},
            {"text": "«👍»", "author": "Ірина Сацюк"},
            {"text": "«Дуже»", "author": "Ірина Сацюк"},
            {"text": "«👍»", "author": "Ірина Сацюк"},
            {"text": "«шо»", "author": "Ірина Сацюк"},
            {"text": "«Ми є тим, що ми робимо постійно. Досконалість — це не дія, а звичка»", "author": "Арістотель"},
            {"text": "«Той, хто має 'Навіщо' жити, витримає майже будь-яке 'Як'»", "author": "Фрідріх Ніцше"},
            {"text": "«Свобода — це можливість робити те, що є правильним, а не те, що хочеться»", "author": "Іммануїл Кант"},
            {"text": "«Ваш час обмежений, тому не витрачайте його, живучи чужим життям»", "author": "Стів Джобс"},
            {"text": "«Дисципліна — це міст між цілями та досягненнями»", "author": "Джим Рон"}
        ]

    def load_sites(self):
        if os.path.exists(self.blocked_sites_file):
            with open(self.blocked_sites_file, "r") as f:
                self.target_sites = json.load(f)
        else:
            self.target_sites = ["instagram.com", "facebook.com"]

    def save_sites(self):
        with open(self.blocked_sites_file, "w") as f:
            json.dump(self.target_sites, f)

    # --- Фонова задача для агента ---
    def generate_lesson_bg(self):
        if self.is_generating:
            return # Якщо вже генерується, не запускаємо вдруге
        
        self.is_generating = True
        self.generated_lesson_html = None
        
        try:
            print("🤖 [Kairos] Запускаю ШІ-агента...")
            task = "1. Перевір календар і знайди PDF. 2. Прочитай його. 3. Згенеруй єдиний інтерактивний HTML-файл для навчання на основі матеріалу. 4. Збережи його як lesson.html"
            
            # Викликаємо нашого агента
            agent_matrix.run_agent(task)
            
            # Після того, як агент закінчив, читаємо створений ним файл
            if os.path.exists("lesson.html"):
                with open("lesson.html", "r", encoding="utf-8") as f:
                    self.generated_lesson_html = f.read()
                print("✅ [Kairos] Навчальний сайт успішно згенеровано і завантажено в пам'ять!")
            else:
                print("❌ [Kairos] Агент завершив роботу, але файл lesson.html не знайдено.")
        except Exception as e:
            print(f"❌ [Kairos] Помилка під час генерації: {e}")
        finally:
            self.is_generating = False

    def request(self, flow: http.HTTPFlow) -> None:
        host = flow.request.pretty_host

        # --- 1. Керування через kairos.api ---
        if host == "kairos.api":
            if flow.request.path == "/" or flow.request.path == "/index.html":
                with open(self.settings_html, "r", encoding="utf-8") as f:
                    content = f.read()
                flow.response = http.Response.make(200, content, {"Content-Type": "text/html; charset=utf-8"})
            
            elif flow.request.path == "/index-settings.html":
                with open("index-settings.html", "r", encoding="utf-8") as f:
                    content = f.read()
                flow.response = http.Response.make(200, content, {"Content-Type": "text/html; charset=utf-8"})

            elif flow.request.path == "/get_sites" and flow.request.method == "GET":
                sites_json = json.dumps(self.target_sites)
                flow.response = http.Response.make(200, sites_json.encode('utf-8'), {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"})

            elif "style.css" in flow.request.path:
                with open(self.settings_css, "r", encoding="utf-8") as f:
                    content = f.read()
                flow.response = http.Response.make(200, content, {"Content-Type": "text/css"})

            elif flow.request.path.startswith("/img/"):
                image_path = flow.request.path.lstrip("/")
                try:
                    with open(image_path, "rb") as f:
                        content = f.read()
                    content_type = "image/png" if image_path.endswith(".png") else "image/jpeg"
                    flow.response = http.Response.make(200, content, {"Content-Type": content_type})
                except FileNotFoundError:
                    flow.response = http.Response.make(404, b"Image not found")

            elif flow.request.path == "/add" and flow.request.method == "POST":
                try:
                    data = json.loads(flow.request.content)
                    new_site = data.get("site", "").replace("https://", "").replace("http://", "").strip("/")
                    if new_site and new_site not in self.target_sites:
                        self.target_sites.append(new_site)
                        self.save_sites()
                    flow.response = http.Response.make(200, b"Success", {"Access-Control-Allow-Origin": "*"})
                except:
                    flow.response = http.Response.make(400, b"Error")

            # 👇 НОВИЙ ЕНДПОІНТ ДЛЯ ПЕРЕВІРКИ ГОТОВНОСТІ УРОКУ 👇
            elif flow.request.path == "/check_lesson":
                if self.generated_lesson_html:
                    # Якщо урок готовий, віддаємо його HTML-код і скидаємо кеш
                    lesson = self.generated_lesson_html
                    self.generated_lesson_html = None # Щоб наступного разу генерувало новий
                    flow.response = http.Response.make(200, lesson, {"Content-Type": "text/html; charset=utf-8", "Access-Control-Allow-Origin": "*"})
                else:
                    # Якщо ще не готово, повертаємо статус 202 (Accepted)
                    flow.response = http.Response.make(202, b"Generating...", {"Access-Control-Allow-Origin": "*"})


        # --- 2. Логіка блокування ---
        elif any(site in host for site in self.target_sites):
            # Запускаємо ШІ-агента у фоновому режимі (якщо він ще не працює)
            if not self.is_generating:
                threading.Thread(target=self.generate_lesson_bg).start()

            selected = random.choice(self.quotes)
            
            html_block = f"""
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>Блокувальник | Час вчитися</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            justify-content: center; 
            height: 100vh; 
            margin: 0; 
            background-color: #1a1a1a; 
            color: #f0f0f0;
        }}
        .quote {{ 
            font-size: 2.5em; 
            font-weight: bold; 
            color: #ff4757; 
            margin-bottom: 10px; 
            text-align: center; 
            padding: 0 20px;
        }}
        .author {{ 
            font-size: 1.2em; 
            color: #a4b0be; 
            font-style: italic; 
            margin-bottom: 50px; 
        }}
        .nav-link {{
            color: #3742fa;
            text-decoration: none;
            font-weight: bold;
        }}
        .loader {{
            margin-top: 40px;
            font-size: 1.2em;
            color: #2ecc71;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="quote">{selected['text']}</div>
    <div class="author">{selected['author']}</div>
    <p style='text-align:center;'><a href='http://kairos.api/' class="nav-link">Налаштування Kairos</a></p>
    
    <div class="loader">
        🤖 ШІ аналізує ваші задачі і створює навчальний сайт... <span id="dots"></span>
    </div>

    <script>
        // Анімація крапок
        let dots = 0;
        setInterval(() => {{
            dots = (dots + 1) % 4;
            document.getElementById('dots').innerText = '.'.repeat(dots);
        }}, 500);

        // Опитування сервера: чи готовий урок?
        setInterval(() => {{
            fetch('http://kairos.api/check_lesson')
            .then(res => {{
                if (res.status === 200) {{
                    // Якщо сервер повернув 200 OK, значить прийшов HTML-код уроку!
                    res.text().then(html => {{
                        document.open();
                        document.write(html);
                        document.close();
                    }});
                }}
            }});
        }}, 3000); // Перевіряємо кожні 3 секунди
    </script>
</body>
</html>
            """
            flow.response = http.Response.make(200, html_block, {"Content-Type": "text/html; charset=utf-8"})

addons = [KairosProxy()]