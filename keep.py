import gkeepapi

keep = gkeepapi.Keep()

# Заміни на свій email та згенерований 16-значний пароль додатка
email = 'tvoy_email@gmail.com'
app_password = 'lrbr rnxx tiad xrkx'

try:
    # Авторизація
    print("Підключаюсь до Google Keep...")
    keep.login(email, app_password)
    print("Успішно підключено!\n")
    
    # Отримуємо всі активні (не видалені і не заархівовані) нотатки
    notes = keep.find(trashed=False, archived=False)
    
    print("Твої актуальні задачі/нотатки:")
    for note in notes:
        # Виводимо заголовок та перші 50 символів тексту нотатки
        title = note.title if note.title else "Без назви"
        text = note.text[:50].replace('\n', ' ') + '...' if note.text else "Пусто"
        print(f"- {title}: {text}")
        
except gkeepapi.exception.LoginException:
    print("Помилка авторизації. Перевір email та пароль додатка.")
except Exception as e:
    print(f"Виникла помилка: {e}")