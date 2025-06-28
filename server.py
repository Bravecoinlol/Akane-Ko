import os
import time
import threading
import requests
import logging
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
import schedule
from config import config

# 設定日誌
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    format=config.LOG_FORMAT,
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 伺服器狀態追蹤
server_stats = {
    'start_time': datetime.now(),
    'last_ping': None,
    'ping_count': 0,
    'health_checks': 0,
    'uptime': 0,
    'status': 'running',
    'server_url': config.SERVER_URL
}

# 配置設定
CONFIG = {
    'ping_interval': config.PING_INTERVAL,
    'health_check_interval': config.HEALTH_CHECK_INTERVAL,
    'ping_urls': config.EXTERNAL_PING_URLS,
    'backup_ping_url': 'https://discord.com/api/v9/gateway',
    'max_retries': config.MAX_RETRIES,
    'retry_delay': config.RETRY_DELAY
}

logger.info(f"🚀 伺服器啟動 - URL: {server_stats['server_url']}")
logger.info(f"📋 配置: Ping間隔={CONFIG['ping_interval']}s, 健康檢查間隔={CONFIG['health_check_interval']}s")

def ping_server():
    """Ping 外部服務以保持連線活躍"""
    try:
        # 輪流使用不同的 ping URL
        url = CONFIG['ping_urls'][server_stats['ping_count'] % len(CONFIG['ping_urls'])]
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            server_stats['last_ping'] = datetime.now()
            server_stats['ping_count'] += 1
            server_stats['status'] = 'running'
            logger.info(f"✅ Ping 成功: {url} (狀態碼: {response.status_code})")
            return True
        else:
            logger.warning(f"⚠️ Ping 警告: {url} (狀態碼: {response.status_code})")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Ping 失敗: {e}")
        
        # 嘗試備用 URL
        try:
            backup_response = requests.get(CONFIG['backup_ping_url'], timeout=15)
            if backup_response.status_code in [200, 401, 403]:  # Discord API 可能返回 401/403
                server_stats['last_ping'] = datetime.now()
                server_stats['ping_count'] += 1
                server_stats['status'] = 'running'
                logger.info(f"✅ 備用 Ping 成功: Discord API")
                return True
        except:
            pass
            
        server_stats['status'] = 'warning'
        return False

def health_check():
    """健康檢查函數"""
    try:
        server_stats['health_checks'] += 1
        server_stats['uptime'] = (datetime.now() - server_stats['start_time']).total_seconds()
        
        # 檢查最後一次 ping 是否太舊
        if server_stats['last_ping']:
            time_since_last_ping = (datetime.now() - server_stats['last_ping']).total_seconds()
            if time_since_last_ping > 300:  # 5分鐘沒有成功 ping
                logger.warning(f"⚠️ 長時間沒有成功 ping: {time_since_last_ping:.1f} 秒")
                server_stats['status'] = 'warning'
        
        logger.info(f"🏥 健康檢查 #{server_stats['health_checks']} - 狀態: {server_stats['status']}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 健康檢查失敗: {e}")
        return False

def start_background_tasks():
    """啟動背景任務"""
    def run_scheduler():
        # 設定定時任務
        schedule.every(CONFIG['ping_interval']).seconds.do(ping_server)
        schedule.every(CONFIG['health_check_interval']).seconds.do(health_check)
        
        logger.info("🚀 背景任務已啟動")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"❌ 背景任務錯誤: {e}")
                time.sleep(5)
    
    # 啟動背景執行緒
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # 立即執行一次 ping
    ping_server()

@app.route("/")
def home():
    """主頁面"""
    uptime = datetime.now() - server_stats['start_time']
    return f"""
    <html>
    <head>
        <title>Discord Bot Server</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f0f0f0; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .status {{ padding: 10px; border-radius: 5px; margin: 10px 0; }}
            .running {{ background: #d4edda; color: #155724; }}
            .warning {{ background: #fff3cd; color: #856404; }}
            .error {{ background: #f8d7da; color: #721c24; }}
            .stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
            .stat-item {{ background: #f8f9fa; padding: 15px; border-radius: 5px; }}
        </style>
        <meta http-equiv="refresh" content="30">
    </head>
    <body>
        <div class="container">
            <h1>🤖 Discord Bot Server</h1>
            <div class="status {server_stats['status']}">
                <strong>狀態:</strong> {server_stats['status'].upper()}
            </div>
            
            <div class="stats">
                <div class="stat-item">
                    <h3>⏱️ 運行時間</h3>
                    <p>{str(uptime).split('.')[0]}</p>
                </div>
                <div class="stat-item">
                    <h3>🔄 Ping 次數</h3>
                    <p>{server_stats['ping_count']}</p>
                </div>
                <div class="stat-item">
                    <h3>🏥 健康檢查</h3>
                    <p>{server_stats['health_checks']}</p>
                </div>
                <div class="stat-item">
                    <h3>📡 最後 Ping</h3>
                    <p>{server_stats['last_ping'].strftime('%H:%M:%S') if server_stats['last_ping'] else '無'}</p>
                </div>
            </div>
            
            <p><em>此頁面每30秒自動刷新</em></p>
        </div>
    </body>
    </html>
    """

@app.route("/health")
def health():
    """健康檢查端點"""
    try:
        # 執行健康檢查
        health_ok = health_check()
        
        response = {
            'status': 'healthy' if health_ok else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'uptime': server_stats['uptime'],
            'ping_count': server_stats['ping_count'],
            'health_checks': server_stats['health_checks'],
            'last_ping': server_stats['last_ping'].isoformat() if server_stats['last_ping'] else None
        }
        
        status_code = 200 if health_ok else 503
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"❌ 健康檢查端點錯誤: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route("/ping")
def manual_ping():
    """手動觸發 ping"""
    try:
        success = ping_server()
        response = {
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'ping_count': server_stats['ping_count'],
            'last_ping': server_stats['last_ping'].isoformat() if server_stats['last_ping'] else None
        }
        
        status_code = 200 if success else 503
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"❌ 手動 ping 錯誤: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/status")
def status():
    """詳細狀態端點"""
    uptime = datetime.now() - server_stats['start_time']
    
    response = {
        'server_status': server_stats['status'],
        'uptime_seconds': server_stats['uptime'],
        'uptime_formatted': str(uptime).split('.')[0],
        'ping_count': server_stats['ping_count'],
        'health_checks': server_stats['health_checks'],
        'last_ping': server_stats['last_ping'].isoformat() if server_stats['last_ping'] else None,
        'start_time': server_stats['start_time'].isoformat(),
        'config': {
            'ping_interval': CONFIG['ping_interval'],
            'health_check_interval': CONFIG['health_check_interval']
        }
    }
    
    return jsonify(response)

@app.route("/restart")
def restart():
    """重啟伺服器（僅用於開發）"""
    if app.debug:
        logger.info("🔄 手動重啟伺服器")
        # 在生產環境中，這裡可以觸發重啟邏輯
        return jsonify({'message': 'Restart initiated'})
    else:
        return jsonify({'error': 'Restart only available in debug mode'}), 403

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"❌ 內部伺服器錯誤: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == "__main__":
    # 啟動背景任務
    start_background_tasks()
    
    # 獲取伺服器配置
    server_config = config.get_server_config()
    
    logger.info(f"🚀 啟動 Discord Bot 伺服器 (端口: {server_config['port']}, 除錯: {server_config['debug']})")
    logger.info(f"🌐 伺服器將在 http://{server_config['host']}:{server_config['port']} 上運行")
    
    # 啟動 Flask 應用
    app.run(**server_config)
