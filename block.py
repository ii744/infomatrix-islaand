import os
import json
import random  # Додали для випадкового вибору
from mitmproxy import http


class KairosProxy:
    def __init__(self):
        self.blocked_sites_file = "blocked_sites.json"
        self.load_sites()
        
        self.settings_html = "index-ai.html"
        self.settings_css = "style-ai.css"

        # Список твоїх цитат
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

    def request(self, flow: http.HTTPFlow) -> None:
        host = flow.request.pretty_host

        # --- 1. Керування через kairos.api ---
        # --- 1. Керування через kairos.api ---
        if host == "kairos.api":
            if flow.request.path == "/" or flow.request.path == "/index.html":
                with open(self.settings_html, "r", encoding="utf-8") as f:
                    content = f.read()
                flow.response = http.Response.make(200, content, {"Content-Type": "text/html; charset=utf-8"})
            
            # 👇 ОСЬ ЦЕЙ БЛОК ТРЕБА ДОДАТИ 👇
            elif flow.request.path == "/index-settings.html":
                with open("index-settings.html", "r", encoding="utf-8") as f:
                    content = f.read()
                flow.response = http.Response.make(200, content, {"Content-Type": "text/html; charset=utf-8"})
            # 👆 КІНЕЦЬ НОВОГО БЛОКУ 👆

            elif flow.request.path == "/get_sites" and flow.request.method == "GET":
                # Перетворюємо список сайтів у JSON-формат
                sites_json = json.dumps(self.target_sites)
                flow.response = http.Response.make(200, sites_json.encode('utf-8'), {
                    "Content-Type": "application/json", 
                    "Access-Control-Allow-Origin": "*"
                })

            elif "style.css" in flow.request.path:
                with open(self.settings_css, "r", encoding="utf-8") as f:
                    content = f.read()
                flow.response = http.Response.make(200, content, {"Content-Type": "text/css"})

            elif flow.request.path.startswith("/img/"):
                # Прибираємо початковий слеш, щоб шлях вказував на локальну папку (наприклад, img/setting.png)
                image_path = flow.request.path.lstrip("/")
                try:
                    with open(image_path, "rb") as f:
                        content = f.read()
                    
                    # Визначаємо правильний Content-Type
                    content_type = "image/png" if image_path.endswith(".png") else "image/jpeg"
                    
                    flow.response = http.Response.make(200, content, {"Content-Type": content_type})
                except FileNotFoundError:
                    # Якщо картинки немає в папці, повертаємо помилку 404
                    flow.response = http.Response.make(404, b"Image not found")
            # 👆 КІНЕЦЬ НОВОГО БЛОКУ 👆

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
        
        

        # --- 2. Логіка блокування ---
        elif any(site in host for site in self.target_sites):
            # Обираємо випадкову цитату
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
    </style>
</head>
<body>
    <div class="quote">{selected['text']}</div>
    <div class="author">{selected['author']}</div>
    <p style='text-align:center;'><a href='http://kairos.api/tree' class="nav-link">Ваше дерево</a></p>
</body>
</html>
            """
            flow.response = http.Response.make(200, html_block, {"Content-Type": "text/html; charset=utf-8"})

addons = [KairosProxy()]