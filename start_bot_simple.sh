#!/bin/bash

# 簡單的 Discord Bot 啟動腳本

echo "=== Discord Bot 啟動腳本 ==="
echo ""

# 檢查是否在正確的目錄
if [ ! -f "bot.py" ]; then
    echo "❌ 錯誤: 請在 Bot 目錄中運行此腳本"
    exit 1
fi

# 停止現有的進程
echo "停止現有的 bot 進程..."
pkill -f "python.*bot.py" 2>/dev/null || true
sleep 3

# 檢查虛擬環境
if [ -d "venv" ]; then
    echo "使用虛擬環境..."
    
    # 激活虛擬環境並啟動
    echo "激活虛擬環境並啟動 bot..."
    cd "$(dirname "$0")"
    source venv/bin/activate
    
    # 檢查 discord 模組
    if python -c "import discord" 2>/dev/null; then
        echo "✅ Discord.py 可用，啟動 bot..."
        python bot.py
    else
        echo "❌ Discord.py 不可用，正在安裝..."
        pip install -r requirements.txt
        echo "✅ 依賴安裝完成，啟動 bot..."
        python bot.py
    fi
else
    echo "❌ 虛擬環境不存在"
    echo "請先創建虛擬環境:"
    echo "python3 -m venv venv"
    echo "source venv/bin/activate"
    echo "pip install -r requirements.txt"
    exit 1
fi 