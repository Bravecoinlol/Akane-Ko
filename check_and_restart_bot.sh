#!/bin/bash

# Discord Bot 狀態檢查和重啟腳本

echo "=== Discord Bot 狀態檢查 ==="
echo ""

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

# 檢查 bot 進程
echo "檢查 bot 進程..."
BOT_PROCESSES=$(pgrep -f "python.*bot.py" 2>/dev/null || echo "")

if [ -n "$BOT_PROCESSES" ]; then
    echo "✅ 找到運行中的 bot 進程:"
    ps aux | grep "python.*bot.py" | grep -v grep
    echo ""
    
    # 檢查進程是否響應
    echo "檢查進程健康狀態..."
    for pid in $BOT_PROCESSES; do
        if kill -0 $pid 2>/dev/null; then
            echo "✅ 進程 $pid 正在運行"
        else
            echo "❌ 進程 $pid 無響應"
        fi
    done
else
    echo "❌ 沒有找到運行中的 bot 進程"
fi

echo ""
echo "=== 重啟選項 ==="
echo "1. 重啟 bot (保留日誌)"
echo "2. 強制重啟 bot (清除日誌)"
echo "3. 僅檢查狀態"
echo "4. 查看日誌"
echo "5. 退出"

read -p "請選擇操作 (1-5): " choice

case $choice in
    1)
        echo ""
        echo "正在重啟 bot..."
        ./restart_bot.sh
        ;;
    2)
        echo ""
        echo "正在強制重啟 bot..."
        # 備份舊日誌
        if [ -f "bot.log" ]; then
            mv bot.log "bot.log.backup.$(date +%Y%m%d_%H%M%S)"
            echo "舊日誌已備份"
        fi
        ./restart_bot.sh
        ;;
    3)
        echo ""
        echo "狀態檢查完成"
        ;;
    4)
        echo ""
        echo "=== 最近的日誌 ==="
        if [ -f "bot.log" ]; then
            tail -30 bot.log
        else
            echo "日誌文件不存在"
        fi
        ;;
    5)
        echo "退出"
        exit 0
        ;;
    *)
        echo "無效選擇"
        exit 1
        ;;
esac

echo ""
echo "操作完成！" 