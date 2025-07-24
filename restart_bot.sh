#!/bin/bash

# Discord Bot 重啟腳本
# 適用於 Orange Pi One

echo "=== Discord Bot 重啟腳本 ==="
echo ""

# 檢查是否在正確的目錄
if [ ! -f "bot.py" ]; then
    echo "❌ 錯誤: 請在 Bot 目錄中運行此腳本"
    exit 1
fi

# 檢查 Python 環境
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ 錯誤: 找不到 Python 命令"
    echo "請安裝 Python3: sudo apt install python3"
    exit 1
fi

echo "使用 Python 命令: $PYTHON_CMD"

# 檢查 systemd 服務是否存在
if systemctl list-unit-files | grep -q "discord-bot"; then
    echo "使用 systemd 服務重啟..."
    
    # 停止服務
    echo "停止 Discord Bot 服務..."
    sudo systemctl stop discord-bot 2>/dev/null || true
    
    # 等待服務完全停止
    sleep 3
    
    # 啟動服務
    echo "啟動 Discord Bot 服務..."
    sudo systemctl start discord-bot
    
    # 檢查狀態
    sleep 2
    if systemctl is-active --quiet discord-bot; then
        echo "✅ Discord Bot 重啟成功！"
        echo ""
        echo "服務狀態:"
        sudo systemctl status discord-bot --no-pager -l
    else
        echo "❌ Discord Bot 重啟失敗！"
        echo ""
        echo "錯誤日誌:"
        sudo journalctl -u discord-bot --no-pager -l -n 20
    fi
else
    echo "使用手動方式重啟..."
    
    # 查找並終止現有的 bot 進程
    echo "查找並終止現有的 bot 進程..."
    pkill -f "python.*bot.py" 2>/dev/null || true
    pkill -f "python3.*bot.py" 2>/dev/null || true
    
    # 等待進程完全終止
    sleep 3
    
    # 檢查是否還有進程在運行
    if pgrep -f "python.*bot.py" > /dev/null; then
        echo "強制終止進程..."
        pkill -9 -f "python.*bot.py" 2>/dev/null || true
        sleep 2
    fi
    
    # 啟動新的 bot 進程
    echo "啟動新的 Discord Bot..."
    if [ -d "venv" ]; then
        # 使用虛擬環境
        source venv/bin/activate
        nohup $PYTHON_CMD bot.py > bot.log 2>&1 &
    else
        # 直接使用系統 Python
        nohup $PYTHON_CMD bot.py > bot.log 2>&1 &
    fi
    
    # 獲取進程 ID
    BOT_PID=$!
    
    # 等待一下讓進程啟動
    sleep 5
    
    # 檢查進程是否還在運行
    if kill -0 $BOT_PID 2>/dev/null; then
        echo "✅ Discord Bot 重啟成功！"
        echo "進程 ID: $BOT_PID"
        echo "日誌文件: bot.log"
    else
        echo "❌ Discord Bot 重啟失敗！"
        echo ""
        echo "最近的日誌:"
        tail -20 bot.log 2>/dev/null || echo "無法讀取日誌文件"
    fi
fi

echo ""
echo "重啟完成！" 