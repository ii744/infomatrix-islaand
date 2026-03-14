import json
import datetime
import os
import tkinter as tk
from PIL import Image, ImageTk
import threading
import time
from typing import Dict, Any
import requests

# URL сервера
SERVER_URL = 'http://localhost:5000'
DATA_FILE = 'achievements_local.json'

# Завантажуємо конфігурацію досягнень
def load_achievements_config() -> Dict[str, Dict[str, Any]]:
    if os.path.exists('achievements_config.json'):
        try:
            with open('achievements_config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Помилка завантаження конфігурації досягнень: {e}. Використовуємо порожню конфігурацію.")
            return {}
    else:
        print(f"⚠️ Файл конфігурації achievements_config.json не знайдено.")
        return {}

ACHIEVEMENTS = load_achievements_config()


class AchievementSystem:
    def __init__(self):
        self.data = self._load_data()
        self.shown_notifications = set(self.data.get('shown_notifications', []))
        self.root = None
        self.ui_ready = False
        self.notification_queue = []  # Черга для сповіщень
        self.active_toast = None  # Поточне активне повідомлення

        # Перевіряємо наявні досягнення (наприклад, якщо прогрес був змінений поза запуском програми)
        self._check_and_unlock()

        # Перевіряємо пропущені сповіщення після завантаження
        self._check_missed_notifications()

        # Зберігаємо поточний стан unlocked для порівняння
        self.last_unlocked = set(self.data['unlocked'])

        # Запускаємо відкладену перевірку стріка (через 15 секунд)
        threading.Thread(target=self._delayed_streak_check, args=(15,), daemon=True).start()

        # Запускаємо polling для перевірки змін на сервері
        threading.Thread(target=self._poll_server, daemon=True).start()

    def _load_data(self) -> Dict:
        data = {}
        try:
            response = requests.get(f"{SERVER_URL}/progress", timeout=5)
            if response.status_code == 200:
                data = response.json()
        except requests.RequestException:
            # Якщо сервер недоступний, завантажуємо з локального файлу
            if os.path.exists(DATA_FILE):
                try:
                    with open(DATA_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except:
                    data = {}

        # Забезпечуємо наявність ключів
        data.setdefault('counters', {})
        data.setdefault('streaks', {'daily': 0})
        data.setdefault('last_login', None)
        data.setdefault('unlocked', {})
        data.setdefault('shown_notifications', [])
        return data

    def _save_data(self):
        """Надсилаємо дані на сервер і зберігаємо локально"""
        # Зберігаємо локально
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"⚠️ Помилка збереження локальних даних: {e}")

        # Надсилаємо на сервер
        try:
            response = requests.post(f"{SERVER_URL}/progress", json=self.data, timeout=5)
            if response.status_code != 200:
                print("⚠️ Помилка збереження даних на сервері.")
        except requests.RequestException as e:
            print(f"⚠️ Помилка з'єднання з сервером: {e}")

    def _check_and_unlock(self):
        """Перевіряємо, чи розблоковано якісь досягнення"""
        for ach_id, ach in ACHIEVEMENTS.items():
            if ach_id in self.data['unlocked']:
                continue  # Вже розблоковано

            unlocked = False
            if ach['type'] == 'counter':
                if self.data['counters'].get(ach['key'], 0) >= ach['threshold']:
                    unlocked = True
            elif ach['type'] == 'streak':
                if self.data['streaks'].get(ach['key'], 0) >= ach['threshold']:
                    unlocked = True

            if unlocked:
                self.data['unlocked'][ach_id] = True
                self.shown_notifications.add(ach_id)
                print(f"🏆 Розблоковано досягнення: {ach['name']}")
                self.notification_queue.append(ach_id)
        self._save_data()
        self._process_notification_queue()

    def _check_missed_notifications(self):
        """Перевіряємо досягнення, які були розблоковані, але сповіщення не показано"""
        for ach_id in self.data['unlocked']:
            if ach_id not in self.shown_notifications:
                self.notification_queue.append(ach_id)
                self.shown_notifications.add(ach_id)
        self._save_data()
        self._process_notification_queue()

    def _process_notification_queue(self):
        """Обробляємо чергу повідомлень, показуючи їх по черзі"""
        if self.notification_queue and self.active_toast is None:
            ach_id = self.notification_queue.pop(0)
            self.show_unlock_notification(ach_id)

    def _delayed_streak_check(self, delay: int):
        """Відкладена перевірка стріка"""
        time.sleep(delay)
        self._check_daily_streak()

    def _check_daily_streak(self):
        """Перевіряємо щоденний стрík"""
        today = datetime.date.today()
        last_login = self.data.get('last_login')
        if last_login:
            last_date = datetime.datetime.fromisoformat(last_login).date()
            if last_date == today:
                print("[Система] Сьогодні ви вже заходили. Стрік не змінено.")
            elif last_date == today - datetime.timedelta(days=1):
                self.data['streaks']['daily'] += 1
                print(f"[Система] Стрік продовжено! Тепер {self.data['streaks']['daily']} днів підряд.")
                self._check_and_unlock()
            else:
                self.data['streaks']['daily'] = 1
                print("[Система] Стрік скинуто. Початок нового стріка.")
        else:
            self.data['streaks']['daily'] = 1
            print("[Система] Початок стріка.")

        self.data['last_login'] = today.isoformat()
        self._save_data()

    def _poll_server(self):
        """Періодично перевіряємо сервер на зміни прогресу"""
        while True:
            time.sleep(5)  # Перевіряємо кожні 5 секунд
            try:
                response = requests.get(f"{SERVER_URL}/progress")
                if response.status_code == 200:
                    new_data = response.json()
                    new_unlocked = set(new_data.get('unlocked', {}))
                    new_unlocked = new_unlocked - self.last_unlocked  # Нові досягнення
                    for ach_id in new_unlocked:
                        if ach_id in ACHIEVEMENTS:
                            self.notification_queue.append(ach_id)
                            self.shown_notifications.add(ach_id)
                    self.last_unlocked = set(new_data.get('unlocked', {}))
                    self._process_notification_queue()
            except requests.RequestException:
                pass  # Ігноруємо помилки з'єднання

    def increment_counter(self, key: str):
        """Збільшуємо лічильник (заглушка для AI)"""
        self.data['counters'][key] = self.data['counters'].get(key, 0) + 1
        print(f"[Система] Лічильник '{key}' збільшено до {self.data['counters'][key]}")
        self._check_and_unlock()

    def add_manual_day(self):
        """Ручне додавання дня для тестування стріка"""
        self.data['streaks']['daily'] += 1
        print(f"[Система] Ручно додано день. Стрік: {self.data['streaks']['daily']}")
        self._check_and_unlock()

    def reset_data(self):
        """Очищає локальні дані (якщо потрібно, в т.ч. файл)."""
        self.data = {
            'counters': {},
            'streaks': {'daily': 0},
            'last_login': None,
            'unlocked': {},
            'shown_notifications': []
        }
        self.shown_notifications = set()
        if os.path.exists(DATA_FILE):
            try:
                os.remove(DATA_FILE)
            except Exception as e:
                print(f"⚠️ Помилка видалення файлу: {e}")

    def show_unlock_notification(self, ach_id: str):
        ach = ACHIEVEMENTS[ach_id]
        if not self.root:
            self.root = tk.Tk()
            self.root.withdraw()
            self.ui_ready = True

        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes('-topmost', True)
        toast.configure(bg='#252526')

        self.active_toast = toast  # Встановлюємо активне повідомлення

        w, h = 350, 100
        screen_w = toast.winfo_screenwidth()
        screen_h = toast.winfo_screenheight()
        toast.geometry(f"{w}x{h}+{screen_w - w - 20}+{screen_h - h - 60}")

        # Початкова прозорість для анімації
        toast.attributes('-alpha', 0.0)

        try:
            img = Image.open(ach['icons']).resize((60, 60))
            photo = ImageTk.PhotoImage(img)
            img_label = tk.Label(toast, image=photo, bg='#252526')
            img_label.image = photo
            img_label.pack(side="left", padx=10)
        except:
            tk.Label(toast, text="🏆", font=("Arial", 30), bg='#252526', fg="gold").pack(side="left", padx=10)

        txt_frame = tk.Frame(toast, bg='#252526')
        txt_frame.pack(side="left", fill="both", expand=True, pady=10)

        tk.Label(txt_frame, text=ach['name'], font=("Arial", 12, "bold"), fg="white", bg='#252526', anchor="w").pack(
            fill="x")
        desc = tk.Label(txt_frame, text=ach['description'], font=("Arial", 9), fg="#cccccc", bg='#252526',
                        wraplength=230, justify="left", anchor="w")
        desc.pack(fill="x")

        # Анімація появи
        def fade_in(alpha=0.0):
            alpha += 0.05
            if alpha <= 1.0:
                toast.attributes('-alpha', alpha)
                toast.after(50, fade_in, alpha)

        fade_in()

        # Закриття через 8 секунд з анімацією зникнення
        def fade_out(alpha=1.0):
            alpha -= 0.05
            if alpha >= 0.0:
                toast.attributes('-alpha', alpha)
                toast.after(50, fade_out, alpha)
            else:
                toast.destroy()
                self.active_toast = None
                self._process_notification_queue()

        toast.after(7000, fade_out)


# ====================== МЕНЮ ======================

def main_menu():
    ach_sys = AchievementSystem()

    print("Програма активна. Авто-перевірка стріка спрацює через 15 секунд.")

    while True:
        print("\n--- МЕНЮ ---")
        print("1. Виконати завдання (task)")
        print("2. Додати день вручну (для тестування стріка)")
        print("3. Показати статистику")
        print("4. Скинути прогрес")
        print("0. Вийти")

        choice = input("Виберіть опцію: ").strip().lower()

        if choice in ['1', 'task']:
            # Заглушка для AI: тут буде виклик AI для перевірки виконання завдання
            # Припустимо, що AI повертає True, якщо виконано
            task_completed = True  # Заглушка: завжди True для тестування
            if task_completed:
                ach_sys.increment_counter('tasks_completed')
            else:
                print("Завдання не виконано.")
        elif choice in ['2', 'day']:
            ach_sys.add_manual_day()
        elif choice in ['3', 'stats']:
            print("\n--- СТАТИСТИКА ---")
            print(f"Виконано завдань: {ach_sys.data['counters'].get('tasks_completed', 0)}")
            print(f"Днів підряд: {ach_sys.data['streaks'].get('daily', 0)}")
            print(f"Розблоковані досягнення: {list(ach_sys.data['unlocked'].keys())}")
        elif choice in ['4', 'reset']:
            confirm = input("Скинути весь прогрес? (yes/no): ").strip().lower()
            if confirm == 'yes':
                ach_sys.reset_data()
                print("Прогрес скинуто.")
        elif choice in ['0', 'exit', 'quit']:
            print("Вимикаємо...")
            break
        else:
            print("⚠️ Невідома команда.")


if __name__ == "__main__":
    main_menu()
