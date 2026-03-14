import os
import ssl
import subprocess

# ==========================================
# 1. АБСОЛЮТНИЙ АНТИ-ПРОКСІ БЛОК
# ==========================================
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''
ssl._create_default_https_context = ssl._create_unverified_context

# ==========================================
# 2. ІМПОРТИ
# ==========================================
import datetime
import io
import json
import PyPDF2
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from zai import ZaiClient

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/drive.readonly']
ZAI_API_KEY = os.getenv("ZAI_API_KEY")
client = ZaiClient(api_key=ZAI_API_KEY)

# =========================================================
# НОВІ ІНСТРУМЕНТИ АГЕНТА (COMPUTER USE)
# =========================================================

def execute_terminal_command(command):
    """Виконує будь-яку команду в терміналі і повертає результат."""
    print(f"   [Термінал] Виконую: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120)
        output = result.stdout if result.stdout else result.stderr
        return output[:4000] if output else "Команда виконана успішно (без виводу)."
    except Exception as e:
        return f"Помилка виконання: {str(e)}"

def read_file_content(filepath):
    """Читає вміст будь-якого локального файлу."""
    print(f"   [Файлова система] Читаю: {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()[:8000]
    except Exception as e:
        return f"Помилка читання: {str(e)}"

def write_to_file(filepath, content):
    """Створює або перезаписує файл із заданим контентом."""
    print(f"   [Файлова система] Записую у: {filepath}")
    try:
        # Автоматично створюємо папки, якщо їх ще немає
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Файл {filepath} успішно створено/оновлено."
    except Exception as e:
        return f"Помилка запису: {str(e)}"

def get_calendar_events():
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(calendarId='primary', timeMin=now, maxResults=1, singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])
    return json.dumps(events[0]) if events else "Подій не знайдено."

def read_pdf_from_drive(file_id):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.seek(0)
    pdf_reader = PyPDF2.PdfReader(fh)
    text = "".join([page.extract_text() for page in pdf_reader.pages])
    return text[:8000] 

# JSON схеми для GLM-5
tools = [
    {"type": "function", "function": {"name": "get_calendar_events", "description": "Отримати задачу з Google Календаря"}},
    {"type": "function", "function": {"name": "read_pdf_from_drive", "description": "Прочитати текст PDF", "parameters": {"type": "object", "properties": {"file_id": {"type": "string"}}, "required": ["file_id"]}}},
    {"type": "function", "function": {"name": "execute_terminal_command", "description": "Виконати команду bash/zsh в терміналі (наприклад, npm install, mkdir, ls). Використовуй це для ініціалізації проєктів.", "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
    {"type": "function", "function": {"name": "read_file_content", "description": "Прочитати код або текст із локального файлу", "parameters": {"type": "object", "properties": {"filepath": {"type": "string"}}, "required": ["filepath"]}}},
    {"type": "function", "function": {"name": "write_to_file", "description": "Записати згенерований код у файл. Підтримує створення нових файлів.", "parameters": {"type": "object", "properties": {"filepath": {"type": "string"}, "content": {"type": "string"}}, "required": ["filepath", "content"]}}}
]

# =========================================================
# АГЕНТНИЙ ЦИКЛ (RE-ACT)
# =========================================================

def run_agent(user_prompt):
    messages = [
        {"role": "system", "content": "Ти автономний AI-розробник. Твоя ціль — розгортати повноцінні веб-проєкти (наприклад, Next.js чи HTML/CSS/JS) використовуючи термінал та файлову систему. Крок за кроком думай, виконуй команди термінала, створюй папки, читай та пиши файли, поки проєкт не буде повністю готовий."},
        {"role": "user", "content": user_prompt}
    ]
    
    print("\n🚀 Запускаю автономного агента...")
    
    # Захист від нескінченного циклу (максимум 15 кроків)
    for step in range(15):
        print(f"\n--- Крок {step + 1} ---")
        response = client.chat.completions.create(
            model="glm-5",
            messages=messages,
            tools=tools,
            thinking={"type": "enabled"}
        )
        
        msg = response.choices[0].message
        
        # Виводимо думки агента
        if getattr(msg, 'reasoning_content', None):
            print(f"💭 Думка: {msg.reasoning_content.strip()}")
            
        messages.append(msg)

        # Якщо агент більше не використовує інструменти, значить він закінчив
        if not msg.tool_calls:
            print("\n✅ Завдання виконано!")
            return msg.content

        # Виконання інструментів
        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            print(f"🛠 Дія: {name}({args})")
            
            if name == "get_calendar_events": result = get_calendar_events()
            elif name == "read_pdf_from_drive": result = read_pdf_from_drive(args.get('file_id'))
            elif name == "execute_terminal_command": result = execute_terminal_command(args.get('command'))
            elif name == "read_file_content": result = read_file_content(args.get('filepath'))
            elif name == "write_to_file": result = write_to_file(args.get('filepath'), args.get('content'))
            else: result = "Невідома функція"
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })
            
    return "Агент зупинено (перевищено ліміт кроків)."

if __name__ == "__main__":
    task = "1. Перевір календар і знайди PDF. 2. Прочитай його. 3. Використай термінал, щоб створити папку 'probability_site'. 4. Згенеруй туди структуру файлів (HTML, CSS, JS) для інтерактивного навчання. 5. Переконайся, що файли створено успішно."
    final_answer = run_agent(task)
    print(f"\nФінальний звіт:\n{final_answer}")