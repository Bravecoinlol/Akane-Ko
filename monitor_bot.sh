#!/bin/bash

# Discord Bot 綜合監控腳本

echo "=== Discord Bot 監控面板 ==="
echo ""

# 檢查 bot 進程
BOT_PROCESSES=$(pgrep -f "python.*bot.py" 2>/dev/null || echo "")
BOT_RUNNING=false

if [ -n "$BOT_PROCESSES" ]; then
    BOT_RUNNING=true
    echo "🟢 Bot 狀態: 運行中"
    echo "進程 ID: $BOT_PROCESSES"
else
    echo "🔴 Bot 狀態: 已停止"
fi

echo ""
echo "=== 監控選項 ==="
echo "1. 實時監控 (持續顯示狀態)"
echo "2. 查看日誌"
echo "3. 查看狀態"
echo "4. 重啟 Bot"
echo "5. 停止 Bot"
echo "6. 查看系統資源"
echo "7. 查看錯誤日誌"
echo "8. 退出"

read -p "請選擇操作 (1-8): " choice

case $choice in
    1)
        echo ""
        echo "=== 實時監控 (按 Ctrl+C 停止) ==="
        echo "每 5 秒更新一次狀態..."
        echo ""
        
        while true; do
            clear
            echo "=== Discord Bot 實時監控 ==="
            echo "時間: $(date)"
            echo ""
            
            # 檢查進程
            BOT_PROCESSES=$(pgrep -f "python.*bot.py" 2>/dev/null || echo "")
            if [ -n "$BOT_PROCESSES" ]; then
                echo "🟢 Bot 狀態: 運行中"
                echo "進程 ID: $BOT_PROCESSES"
                
                # 顯示進程信息
                for pid in $BOT_PROCESSES; do
                    if kill -0 $pid 2>/dev/null; then
                        echo "   進程 $pid: $(ps -p $pid -o etime,pcpu,pmem --no-headers)"
                    fi
                done
            else
                echo "🔴 Bot 狀態: 已停止"
            fi
            
            # 顯示日誌最後一行
            if [ -f "bot.log" ]; then
                echo ""
                echo "最新日誌:"
                tail -1 bot.log 2>/dev/null || echo "無法讀取日誌"
            fi
            
            # 顯示系統資源
            echo ""
            echo "系統資源:"
            echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
            echo "記憶體: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
            echo "磁碟: $(df -h . | tail -1 | awk '{print $5}')"
            
            sleep 5
        done
        ;;
    2)
        echo ""
        echo "=== 日誌查看 ==="
        if [ -f "bot.log" ]; then
            echo "選擇查看方式:"
            echo "1. 實時查看 (tail -f)"
            echo "2. 最近 50 行"
            echo "3. 最近 100 行"
            echo "4. 只顯示錯誤"
            echo "5. 只顯示警告"
            
            read -p "請選擇 (1-5): " log_choice
            
            case $log_choice in
                1) tail -f bot.log ;;
                2) tail -50 bot.log ;;
                3) tail -100 bot.log ;;
                4) grep -i "error\|exception" bot.log | tail -20 ;;
                5) grep -i "warning" bot.log | tail -20 ;;
                *) echo "無效選擇" ;;
            esac
        else
            echo "❌ 日誌文件不存在"
        fi
        ;;
    3)
        echo ""
        echo "=== 詳細狀態 ==="
        ./view_bot_status.sh
        ;;
    4)
        echo ""
        echo "=== 重啟 Bot ==="
        ./start_bot_background.sh
        ;;
    5)
        echo ""
        echo "=== 停止 Bot ==="
        pkill -f "python.*bot.py"
        echo "Bot 已停止"
        ;;
    6)
        echo ""
        echo "=== 系統資源 ==="
        echo "CPU 使用率:"
        top -bn1 | grep "Cpu(s)"
        echo ""
        echo "記憶體使用:"
        free -h
        echo ""
        echo "磁碟使用:"
        df -h
        echo ""
        echo "網路連接:"
        netstat -tlnp | grep python 2>/dev/null || echo "沒有找到 Python 網路連接"
        ;;
    7)
        echo ""
        echo "=== 錯誤日誌 ==="
        if [ -f "bot.log" ]; then
            echo "最近的錯誤:"
            grep -i "error\|exception\|traceback" bot.log | tail -20
        else
            echo "❌ 日誌文件不存在"
        fi
        ;;
    8)
        echo "退出監控"
        exit 0
        ;;
    *)
        echo "無效選擇"
        exit 1
        ;;
esac

echo ""
echo "監控完成！" 