import subprocess
import os
import sys

def main():
    """啟動 Discord Bot"""
    try:
        # 檢查 bot.py 是否存在
        if not os.path.exists("bot.py"):
            print("❌ bot.py 不存在！")
            return
        
        # 檢查 .env 檔案
        if not os.path.exists(".env"):
            print("⚠️ .env 檔案不存在，請確認環境變數設定")
        
        print("🚀 正在啟動 Discord Bot...")
        subprocess.run([sys.executable, "bot.py"])
        
    except KeyboardInterrupt:
        print("\n👋 Bot 已停止")
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")

if __name__ == "__main__":
    main()