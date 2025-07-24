#!/bin/bash

# 查看 Discord Bot 日誌的腳本

echo "=== Discord Bot 日誌查看器 ==="
echo ""

# 檢查日誌文件
if [ ! -f "bot.log" ]; then
    echo "❌ 日誌文件不存在: bot.log"
    echo "Bot 可能還沒有啟動或日誌文件被刪除"
    exit 1
fi

echo "日誌文件大小: $(du -h bot.log | cut -f1)"
echo "最後修改時間: $(stat -c %y bot.log)"
echo ""

echo "=== 選項 ==="
echo "1. 實時查看日誌 (tail -f)"
echo "2. 查看最近的 50 行"
echo "3. 查看最近的 100 行"
echo "4. 查看錯誤信息"
echo "5. 查看警告信息"
echo "6. 查看連接信息"
echo "7. 查看音樂播放信息"
echo "8. 查看完整日誌"
echo "9. 退出"

read -p "請選擇操作 (1-9): " choice

case $choice in
    1)
        echo ""
        echo "=== 實時日誌 (按 Ctrl+C 停止) ==="
        tail -f bot.log
        ;;
    2)
        echo ""
        echo "=== 最近的 50 行日誌 ==="
        tail -50 bot.log
        ;;
    3)
        echo ""
        echo "=== 最近的 100 行日誌 ==="
        tail -100 bot.log
        ;;
    4)
        echo ""
        echo "=== 錯誤信息 ==="
        grep -i "error\|exception\|traceback" bot.log | tail -20
        ;;
    5)
        echo ""
        echo "=== 警告信息 ==="
        grep -i "warning" bot.log | tail -20
        ;;
    6)
        echo ""
        echo "=== 連接信息 ==="
        grep -i "connect\|login\|ready" bot.log | tail -20
        ;;
    7)
        echo ""
        echo "=== 音樂播放信息 ==="
        grep -i "play\|music\|song" bot.log | tail -20
        ;;
    8)
        echo ""
        echo "=== 完整日誌 ==="
        cat bot.log
        ;;
    9)
        echo "退出"
        exit 0
        ;;
    *)
        echo "無效選擇"
        exit 1
        ;;
esac

echo ""
echo "日誌查看完成！" 