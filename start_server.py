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
from threading import Thread

def run_server():
    """運行 Flask 伺服器"""
    print("🚀 啟動 Flask 伺服器...")
    subprocess.run([sys.executable, "server.py"])

def run_keep_alive():
    """運行保活腳本"""
    print("🔄 啟動保活腳本...")
    subprocess.run([sys.executable, "keep_alive.py"])

def main():
    """主函數"""
    print("🤖 Discord Bot 伺服器啟動器")
    print("=" * 50)
    
    # 檢查必要檔案
    required_files = ["server.py", "keep_alive.py"]
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ 缺少必要檔案: {file}")
            return 1
    
    # 設定環境變數
    os.environ.setdefault("SERVER_URL", "http://localhost:5000")
    os.environ.setdefault("PING_INTERVAL", "25")
    os.environ.setdefault("HEALTH_CHECK_INTERVAL", "60")
    
    print("📋 配置:")
    print(f"   - 伺服器 URL: {os.environ['SERVER_URL']}")
    print(f"   - Ping 間隔: {os.environ['PING_INTERVAL']} 秒")
    print(f"   - 健康檢查間隔: {os.environ['HEALTH_CHECK_INTERVAL']} 秒")
    print("=" * 50)
    
    try:
        # 啟動伺服器執行緒
        server_thread = Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # 等待伺服器啟動
        print("⏳ 等待伺服器啟動...")
        time.sleep(5)
        
        # 啟動保活腳本
        keep_alive_thread = Thread(target=run_keep_alive, daemon=True)
        keep_alive_thread.start()
        
        print("✅ 所有服務已啟動")
        print("📊 監控日誌:")
        print("   - 伺服器日誌: server.log")
        print("   - 保活日誌: keep_alive.log")
        print("🌐 訪問 http://localhost:5000 查看狀態")
        print("=" * 50)
        
        # 保持主執行緒運行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 收到中斷信號，正在停止...")
        return 0
    except Exception as e:
        print(f"❌ 啟動錯誤: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 