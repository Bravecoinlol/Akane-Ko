import os
import json
import psutil
import subprocess
from flask import Flask, render_template, jsonify, request, send_file
from datetime import datetime

app = Flask(__name__)

# 設定檔案路徑
WELCOME_CONFIG = 'setting.json'
LOG_FILE = 'bot.log'
WELCOME_CARD = 'welcome_card.png'

# 取得系統狀態
def get_system_status():
    return {
        'cpu_percent': psutil.cpu_percent(),
        'memory': psutil.virtual_memory()._asdict(),
        'disk': psutil.disk_usage('/')._asdict(),
        'net': psutil.net_io_counters()._asdict(),
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

# 取得 Bot 狀態
def get_bot_status():
    # 這裡假設 bot.py 以 python3 bot.py 啟動
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        if 'bot.py' in ' '.join(p.info.get('cmdline', [])):
            return {'online': True, 'pid': p.info['pid']}
    return {'online': False, 'pid': None}

# 取得日誌內容
def get_log_content(lines=100):
    if not os.path.exists(LOG_FILE):
        return ''
    with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        return ''.join(f.readlines()[-lines:])

# 取得歡迎卡片設定
def get_welcome_config():
    if not os.path.exists(WELCOME_CONFIG):
        return {}
    with open(WELCOME_CONFIG, 'r', encoding='utf-8') as f:
        return json.load(f)

# 儲存歡迎卡片設定
def save_welcome_config(data):
    with open(WELCOME_CONFIG, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/system')
def api_system():
    return jsonify(get_system_status())

@app.route('/api/bot')
def api_bot():
    return jsonify(get_bot_status())

@app.route('/api/log')
def api_log():
    lines = int(request.args.get('lines', 100))
    return jsonify({'log': get_log_content(lines)})

@app.route('/api/welcome_config', methods=['GET', 'POST'])
def api_welcome_config():
    if request.method == 'POST':
        data = request.json
        save_welcome_config(data)
        return jsonify({'status': 'ok'})
    return jsonify(get_welcome_config())

@app.route('/api/welcome_card')
def api_welcome_card():
    if os.path.exists(WELCOME_CARD):
        return send_file(WELCOME_CARD, mimetype='image/png')
    return '', 404

@app.route('/api/bot/restart', methods=['POST'])
def api_bot_restart():
    # 嘗試重啟 bot（需 root/正確權限）
    status = get_bot_status()
    if status['online'] and status['pid']:
        try:
            os.kill(status['pid'], 9)
            subprocess.Popen(['python3', 'bot.py'])
            return jsonify({'status': 'restarted'})
        except Exception as e:
            return jsonify({'status': 'error', 'msg': str(e)})
    else:
        subprocess.Popen(['python3', 'bot.py'])
        return jsonify({'status': 'started'})

@app.route('/api/bot/stop', methods=['POST'])
def api_bot_stop():
    status = get_bot_status()
    if status['online'] and status['pid']:
        try:
            os.kill(status['pid'], 9)
            return jsonify({'status': 'stopped'})
        except Exception as e:
            return jsonify({'status': 'error', 'msg': str(e)})
    return jsonify({'status': 'not_running'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 