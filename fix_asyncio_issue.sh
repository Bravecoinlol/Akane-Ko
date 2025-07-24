#!/bin/bash

# 修復 Discord Bot asyncio 問題的腳本

echo "=== 修復 Discord Bot asyncio 問題 ==="
echo ""

# 檢查是否在正確的目錄
if [ ! -f "bot.py" ]; then
    echo "❌ 錯誤: 請在 Bot 目錄中運行此腳本"
    exit 1
fi

echo "1. 停止現有的 bot 進程..."
pkill -f "python.*bot.py" 2>/dev/null || true
pkill -f "python3.*bot.py" 2>/dev/null || true

echo "2. 等待進程完全停止..."
sleep 5

echo "3. 檢查是否還有進程在運行..."
if pgrep -f "python.*bot.py" > /dev/null; then
    echo "強制終止進程..."
    pkill -9 -f "python.*bot.py" 2>/dev/null || true
    sleep 3
fi

echo "4. 備份舊日誌..."
if [ -f "bot.log" ]; then
    mv bot.log "bot.log.backup.$(date +%Y%m%d_%H%M%S)"
    echo "日誌已備份"
fi

echo "5. 啟動修復後的 bot..."

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

if [ -d "venv" ]; then
    echo "使用虛擬環境..."
    echo "虛擬環境路徑: $(pwd)/venv"
    
    # 檢查虛擬環境中的 Python
    if [ -f "venv/bin/python" ]; then
        VENV_PYTHON="venv/bin/python"
        echo "虛擬環境 Python: $VENV_PYTHON"
        
        # 測試虛擬環境中的 discord 模組
        if $VENV_PYTHON -c "import discord; print('Discord.py 可用')" 2>/dev/null; then
            echo "✅ 虛擬環境中的 Discord.py 可用"
        else
            echo "❌ 虛擬環境中的 Discord.py 不可用"
            echo "正在安裝依賴..."
            $VENV_PYTHON -m pip install -r requirements.txt
        fi
        
        # 使用虛擬環境啟動
        echo "使用虛擬環境啟動 bot..."
        nohup $VENV_PYTHON bot.py > bot.log 2>&1 &
    else
        echo "❌ 虛擬環境中的 Python 不可用"
        echo "重新創建虛擬環境..."
        rm -rf venv
        $PYTHON_CMD -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        nohup venv/bin/python bot.py > bot.log 2>&1 &
    fi
else
    echo "使用系統 Python..."
    nohup $PYTHON_CMD bot.py > bot.log 2>&1 &
fi

BOT_PID=$!

echo "6. 等待 bot 啟動..."
sleep 10

echo "7. 檢查 bot 狀態..."
if kill -0 $BOT_PID 2>/dev/null; then
    echo "✅ Bot 啟動成功！"
    echo "進程 ID: $BOT_PID"
    echo ""
    echo "最近的日誌:"
    tail -10 bot.log
else
    echo "❌ Bot 啟動失敗！"
    echo ""
    echo "錯誤日誌:"
    tail -20 bot.log
    echo ""
    echo "請檢查以下項目:"
    echo "1. Python 是否正確安裝: $PYTHON_CMD --version"
    echo "2. 依賴是否安裝: pip list | grep discord"
    echo "3. 配置文件是否存在: ls -la .env"
    echo "4. 權限是否正確: ls -la bot.py"
    echo ""
    echo "嘗試手動啟動:"
    if [ -d "venv" ]; then
        echo "source venv/bin/activate && python bot.py"
    else
        echo "$PYTHON_CMD bot.py"
    fi
fi

echo ""
echo "修復完成！" 