from playwright.sync_api import sync_playwright
import time

def shadow_agent_request(prompt_text):
    with sync_playwright() as p:
        # headless=True означає, що вікно браузера не буде з'являтися на екрані
        print("🌐 Запускаю тіньовий Chromium...")
        browser = p.chromium.launch(headless=True) 
        
        # Створюємо контекст. Для реального демо сюди треба буде підкинути cookies
        context = browser.new_context()
        page = context.new_page()
        
        try:
            print("🔗 Заходжу на https://chat.z.ai/ ...")
            page.goto("https://chat.z.ai/", timeout=30000)
            
            # --- ВАЖЛИВО ---
            # Якщо сайт вимагає авторизації, скрипт зупиниться тут. 
            # Для демо без логіну сайт має бути публічно доступним.
            
            print("⌨️ Вводжу промпт...")
            # Чекаємо, поки поле вводу з'явиться на сторінці
            page.wait_for_selector("textarea#chat-input", timeout=10000)
            page.fill("textarea#chat-input", prompt_text)
            
            print("🚀 Натискаю кнопку відправки...")
            # Чекаємо, поки кнопка стане активною (відключиться атрибут disabled)
            page.wait_for_selector("button#send-message-button:not([disabled])", timeout=5000)
            page.click("button#send-message-button")
            
            print("⏳ Чекаю на генерацію відповіді...")
            # Оскільки ми не знаємо селектор блоку відповіді, для демо ставимо жорстку паузу
            # В ідеалі тут має бути очікування на конкретний елемент
            time.sleep(15) 
            
            print("✅ Запит успішно відпрацював у фоні!")
            
            # Якщо захочеш витягнути текст, треба знайти клас, в якому з'являється відповідь:
            # response = page.locator(".markdown-body").last.inner_text()
            # print(response)
            
        except Exception as e:
            print(f"❌ Виникла помилка під час роботи тіньового браузера: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_prompt = "Створи короткий HTML код для сайту про теорію ймовірностей."
    shadow_agent_request(test_prompt)