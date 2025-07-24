#!/bin/bash

# 查看 Discord Bot 狀態的腳本

echo "=== Discord Bot 狀態檢查 ==="
echo ""

# 檢查 bot 進程
echo "1. 檢查 bot 進程..."
BOT_PROCESSES=$(pgrep -f "python.*bot.py" 2>/dev/null || echo "")

if [ -n "$BOT_PROCESSES" ]; then
    echo "✅ 找到運行中的 bot 進程:"
    ps aux | grep "python.*bot.py" | grep -v grep
    echo ""
    
    # 檢查進程是否響應
    echo "2. 檢查進程健康狀態..."
    for pid in $BOT_PROCESSES; do
        if kill -0 $pid 2>/dev/null; then
            echo "✅ 進程 $pid 正在運行"
            
            # 獲取進程詳細信息
            echo "   進程信息:"
            ps -p $pid -o pid,ppid,cmd,etime,pcpu,pmem --no-headers
        else
            echo "❌ 進程 $pid 無響應"
        fi
    done
else
    echo "❌ 沒有找到運行中的 bot 進程"
fi

echo ""
echo "3. 檢查系統資源使用..."
if [ -n "$BOT_PROCESSES" ]; then
    echo "CPU 和記憶體使用情況:"
    for pid in $BOT_PROCESSES; do
        if kill -0 $pid 2>/dev/null; then
            top -p $pid -b -n 1 | tail -2
        fi
    done
else
    echo "沒有 bot 進程運行"
fi

echo ""
echo "4. 檢查日誌文件..."
if [ -f "bot.log" ]; then
    echo "✅ 日誌文件存在"
    echo "   文件大小: $(du -h bot.log | cut -f1)"
    echo "   最後修改: $(stat -c %y bot.log)"
    echo "   最近更新: $(tail -1 bot.log | cut -c1-50)..."
else
    echo "❌ 日誌文件不存在"
fi

echo ""
echo "5. 檢查網路連接..."
NETWORK_CONNECTIONS=$(netstat -tlnp 2>/dev/null | grep python || echo "沒有找到網路連接")
if [ "$NETWORK_CONNECTIONS" != "沒有找到網路連接" ]; then
    echo "✅ 找到網路連接:"
    echo "$NETWORK_CONNECTIONS"
else
    echo "❌ 沒有找到網路連接"
fi

echo ""
echo "6. 檢查磁碟空間..."
DISK_USAGE=$(df -h . | tail -1)
echo "當前目錄磁碟使用: $DISK_USAGE"

echo ""
echo "7. 檢查記憶體使用..."
MEMORY_INFO=$(free -h | grep Mem)
echo "系統記憶體: $MEMORY_INFO"

echo ""
echo "=== 快速命令 ==="
echo "查看實時日誌: tail -f bot.log"
echo "查看進程: ps aux | grep python | grep bot"
echo "停止 bot: pkill -f 'python.*bot.py'"
echo "重啟 bot: ./start_bot_background.sh"
echo "查看錯誤: grep -i error bot.log | tail -10"

echo ""
echo "狀態檢查完成！" 