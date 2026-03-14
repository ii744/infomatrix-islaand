import os
import ssl

# ==========================================
# 1. АБСОЛЮТНИЙ АНТИ-ПРОКСІ БЛОК ДЛЯ macOS
# ==========================================
# Ця зірочка каже системі: "Забудь про проксі для будь-яких адрес взагалі"
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

# Очищаємо залишки
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''

# Вимикаємо перевірку сертифікатів
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''
ssl._create_default_https_context = ssl._create_unverified_context

# ==========================================
# 2. ВСІ ІНШІ ІМПОРТИ
# ==========================================
import datetime
import io
import re
import PyPDF2
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from zai import ZaiClient

# Завантажуємо змінні з файлу .env
load_dotenv()

# ==========================================
# НАЛАШТУВАННЯ ПРОМПТА
# ==========================================
PROMPT_TEMPLATE = """Ти експерт зі створення інтерактивних навчальних матеріалів.
Створи єдиний інтерактивний сайт-навчання (де HTML, CSS та JS знаходяться в одному файлі) на основі наданого матеріалу. 
Сайт має бути красивим, з тестами або вікторинами для перевірки знань.
ВАЖЛИВО: Поверни весь фінальний код сайту всередині блоку ```html ... ```.

Ось матеріал для вивчення:
{text}"""
# ==========================================

SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

def main():
    api_key = os.getenv("ZAI_API_KEY")
    if not api_key:
        print("❌ Помилка: Ключ ZAI_API_KEY не знайдено! Переконайся, що ти створила файл .env і додала туди ключ.")
        return

    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        calendar_service = build('calendar', 'v3', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)
        
        now = datetime.datetime.utcnow().isoformat() + 'Z'  
        print('Шукаю задачі з PDF-файлами...\n')
        
        events_result = calendar_service.events().list(
            calendarId='primary', timeMin=now,
            maxResults=1, singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        if not events:
            print('Немає найближчих подій.')
            return

        for event in events:
            print(f"🎯 Задача: {event.get('summary', 'Без назви')}")
            attachments = event.get('attachments', [])
            
            if attachments:
                for file in attachments:
                    file_id = file.get('fileId')
                    mime_type = file.get('mimeType', '')
                    
                    if file_id and 'pdf' in mime_type.lower():
                        print(f"   ⬇️ Завантажую PDF файл...")
                        request = drive_service.files().get_media(fileId=file_id)
                        fh = io.BytesIO()
                        downloader = MediaIoBaseDownload(fh, request)
                        done = False
                        while not done:
                            status, done = downloader.next_chunk()
                        
                        print("   📖 Читаю текст із PDF...")
                        fh.seek(0)
                        pdf_reader = PyPDF2.PdfReader(fh)
                        extracted_text = ""
                        for page in pdf_reader.pages:
                            extracted_text += page.extract_text() + "\n"
                        
                        context_text = extracted_text[:8000]
                        
                        print("   🧠 Запускаю агента GLM-5...\n")
                        client = ZaiClient(api_key=api_key) 
                        
                        # Формуємо фінальний промпт, підставляючи текст із PDF
                        prompt = PROMPT_TEMPLATE.format(text=context_text)
                        
                        response = client.chat.completions.create(
                            model="glm-5",
                            messages=[
                                {"role": "user", "content": prompt}
                            ],
                            thinking={
                                "type": "enabled",
                            },
                            stream=True,
                            max_tokens=8192,
                            temperature=0.7,
                        )

                        print("--- 💭 ПРОЦЕС МИСЛЕННЯ АГЕНТА ---")
                        thinking_finished = False
                        full_content = ""
                        
                        for chunk in response:
                            reasoning = getattr(chunk.choices[0].delta, 'reasoning_content', None)
                            if reasoning:
                                print(reasoning, end="", flush=True)
                                
                            content = getattr(chunk.choices[0].delta, 'content', None)
                            if content:
                                if not thinking_finished:
                                    print("\n\n--- 🚀 ГЕНЕРАЦІЯ САЙТУ ---\n")
                                    thinking_finished = True
                                print(content, end="", flush=True)
                                full_content += content
                                
                        print("\n\n✅ Зберігаю результат у файл...")
                        
                        # Шукаємо HTML код у відповіді ШІ
                        html_match = re.search(r"```html\n(.*?)```", full_content, re.DOTALL)
                        if html_match:
                            html_code = html_match.group(1)
                        else:
                            # Якщо модель не використала маркдаун, пробуємо зберегти все як є, очистивши від зайвого
                            html_code = full_content.replace("```html", "").replace("```", "").strip()
                            
                        # Зберігаємо файл у поточну папку
                        with open("index.html", "w", encoding="utf-8") as f:
                            f.write(html_code)
                            
                        print("\n🎉 Файл index.html успішно створено! Відкрий його у своєму браузері.")
            else:
                print("📎 Вкладень немає.")

    except Exception as e:
        print(f'Виникла помилка: {e}')

if __name__ == '__main__':
    main()