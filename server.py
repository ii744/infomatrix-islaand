import json
import os
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

DATA_FILE = 'achievements.json'
CONFIG_FILE = 'achievements_config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

ACHIEVEMENTS = load_config()

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route('/progress', methods=['GET'])
def get_progress():
    data = load_data()
    return jsonify(data)

@app.route('/progress', methods=['POST'])
def update_progress():
    update = request.json
    data = load_data()
    # Оновлюємо дані
    for key, value in update.items():
        if key in ['counters', 'streaks', 'unlocked', 'shown_notifications', 'last_login']:
            if isinstance(value, dict):
                data.setdefault(key, {}).update(value)
            else:
                data[key] = value
    save_data(data)
    return jsonify({"status": "updated"})

@app.route('/achievements')
def show_achievements():
    data = load_data()
    html = f"""
    <!DOCTYPE html>
    <html lang="uk">
    <head>
        <meta charset="UTF-8">
        <title>Досягнення</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f0f0f0; margin: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; text-align: center; }}
            .stats {{ display: flex; justify-content: space-around; margin-bottom: 20px; }}
            .stat {{ text-align: center; }}
            .stat-value {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
            .achievements {{ list-style: none; padding: 0; }}
            .achievement {{ display: flex; align-items: center; padding: 10px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 5px; }}
            .achievement.unlocked {{ background-color: #e8f5e8; border-color: #4CAF50; }}
            .achievement-info {{ flex-grow: 1; }}
            .achievement-name {{ font-weight: bold; margin-bottom: 5px; }}
            .achievement-desc {{ color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Ваші досягнення</h1>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{data.get('counters', {}).get('tasks_completed', 0)}</div>
                    <div>Виконано завдань</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{data.get('streaks', {}).get('daily', 0)}</div>
                    <div>Днів підряд</div>
                </div>
            </div>
            <ul class="achievements">
    """
    for ach_id, ach in ACHIEVEMENTS.items():
        unlocked = ach_id in data.get('unlocked', {})
        status_class = "unlocked" if unlocked else ""
        html += f"""
                <li class="achievement {status_class}">
                    <div class="achievement-info">
                        <div class="achievement-name">{ach['name']}</div>
                        <div class="achievement-desc">{ach['description']}</div>
                    </div>
                </li>
        """
    html += """
            </ul>
        </div>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)