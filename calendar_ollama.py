import datetime
import os.path
import io
import requests
import PyPDF2
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

def main():
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
                        
                        # Беремо перші 2000 символів, щоб перевірити концепт і не перевантажити пам'ять моделі одразу
                        context_text = extracted_text[:2000]
                        
                        print("   🧠 Відправляю матеріал до Gemma3 4b через Ollama...")
                        prompt = f"Ти агент-помічник. Ось уривок з матеріалу, який я зараз вивчаю. Будь ласка, проаналізуй його і склади 3 короткі контрольні запитання для перевірки моїх знань:\n\n{context_text}"
                        
                        try:
                            # Стандартний порт Ollama - 11434. Якщо Ollama на іншому сервері, заміни localhost на IP сервера
                            response = requests.post("http://localhost:11434/api/generate", json={
                                "model": "gemma3:4b",
                                "prompt": prompt,
                                "stream": False
                            })
                            
                            if response.status_code == 200:
                                result = response.json().get("response", "")
                                print("\n🤖 Відповідь від ШІ-агента:\n")
                                print(result)
                            else:
                                print(f"❌ Помилка Ollama: {response.status_code} - {response.text}")
                        except requests.exceptions.ConnectionError:
                            print("❌ Помилка: не вдалося з'єднатися з Ollama. Перевір, чи вона запущена (ollama run gemma3-4b).")
            else:
                print("📎 Вкладень немає.")

    except Exception as e:
        print(f'Виникла помилка: {e}')

if __name__ == '__main__':
    main()