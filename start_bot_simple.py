#!/usr/bin/env python3
"""
簡化的 Discord Bot 啟動腳本
適用於 FreeServer 環境，不依賴 Flask 伺服器
"""

import subprocess
import sys
import os
import logging
from datetime import datetime

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_simple.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """主函數"""
    logger.info("🤖 簡化 Discord Bot 啟動器")
    logger.info("=" * 50)
    
    # 檢查必要檔案
    required_files = ["bot.py"]
    for file in required_files:
        if not os.path.exists(file):
            logger.error(f"❌ 缺少必要檔案: {file}")
            return 1
    
    # 檢查環境變數
    token = os.environ.get('TOKEN') or os.environ.get('DISCORD_TOKEN')
    if not token:
        logger.warning("⚠️ 未找到 Discord Token，請確認環境變數設定")
        logger.info("💡 請在 .env 檔案中設定 TOKEN 或 DISCORD_TOKEN")
    
    logger.info("🚀 啟動 Discord Bot...")
    logger.info("📝 注意：此模式不包含 Flask 伺服器")
    logger.info("🌐 適用於 FreeServer 等受限環境")
    logger.info("=" * 50)
    
    try:
        # 啟動 Discord Bot
        subprocess.run([sys.executable, "bot.py"], check=True)
        
    except KeyboardInterrupt:
        logger.info("🛑 收到中斷信號，正在停止...")
        return 0
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Bot 啟動失敗: {e}")
        return 1
    except Exception as e:
        logger.error(f"❌ 啟動錯誤: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 