#!/usr/bin/env python3
"""
Discord Bot 伺服器啟動腳本
同時啟動 Flask 伺服器和保活腳本
"""

import subprocess
import sys
import time
import signal
import os
import logging
from threading import Thread
from datetime import datetime
from config import config

# 設定日誌
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    format=config.LOG_FORMAT,
    handlers=[
        logging.FileHandler('startup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_server():
    """運行 Flask 伺服器"""
    logger.info("🚀 啟動 Flask 伺服器...")
    try:
        subprocess.run([sys.executable, "server.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 伺服器啟動失敗: {e}")
    except Exception as e:
        logger.error(f"❌ 伺服器執行錯誤: {e}")

def run_keep_alive():
    """運行保活腳本"""
    logger.info("🔄 啟動保活腳本...")
    try:
        subprocess.run([sys.executable, "keep_alive.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 保活腳本啟動失敗: {e}")
    except Exception as e:
        logger.error(f"❌ 保活腳本執行錯誤: {e}")

def main():
    """主函數"""
    logger.info("🤖 Discord Bot 伺服器啟動器")
    logger.info("=" * 50)
    
    # 檢查必要檔案
    required_files = ["server.py", "keep_alive.py", "config.py"]
    for file in required_files:
        if not os.path.exists(file):
            logger.error(f"❌ 缺少必要檔案: {file}")
            return 1
    
    # 顯示配置
    config.print_config()
    
    try:
        # 啟動伺服器執行緒
        server_thread = Thread(target=run_server, daemon=True)
        server_thread.start()
        logger.info("✅ 伺服器執行緒已啟動")
        
        # 等待伺服器啟動
        logger.info("⏳ 等待伺服器啟動...")
        time.sleep(5)
        
        # 啟動保活腳本
        keep_alive_thread = Thread(target=run_keep_alive, daemon=True)
        keep_alive_thread.start()
        logger.info("✅ 保活腳本執行緒已啟動")
        
        logger.info("✅ 所有服務已啟動")
        logger.info("📊 監控日誌:")
        logger.info("   - 啟動日誌: startup.log")
        logger.info("   - 伺服器日誌: server.log")
        logger.info("   - 保活日誌: keep_alive.log")
        logger.info(f"🌐 訪問 {config.SERVER_URL} 查看狀態")
        logger.info("=" * 50)
        
        # 保持主執行緒運行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 收到中斷信號，正在停止...")
        return 0
    except Exception as e:
        logger.error(f"❌ 啟動錯誤: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 