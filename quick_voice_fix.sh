#!/bin/bash

# 快速語音連接修復腳本
# 專門修復錯誤代碼 4006 "Unknown session"

echo "🚀 快速語音連接修復"
echo "===================="

# 檢查是否在正確目錄
if [ ! -f "bot.py" ]; then
    echo "❌ 錯誤：請在 Bot 目錄中執行此腳本"
    exit 1
fi

# 1. 停止 Bot
echo "🛑 停止 Bot..."
if pgrep -f "bot.py" > /dev/null; then
    pkill -f "bot.py"
    sleep 3
    echo "✅ Bot 已停止"
else
    echo "ℹ️ Bot 未運行"
fi

# 2. 創建優化的 FFmpeg 配置
echo ""
echo "⚙️ 創建優化的 FFmpeg 配置..."
cat > ffmpeg_config.json << 'EOF'
{
  "ffmpeg_path": "ffmpeg",
  "ffmpeg_options": {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 15 -reconnect_at_eof 1 -reconnect_on_network_error 1 -reconnect_on_http_error 1",
    "options": "-vn -b:a 96k -bufsize 2048k -maxrate 128k -ar 48000 -ac 2 -af volume=0.5"
  }
}
EOF
echo "✅ FFmpeg 配置已創建"

# 3. 創建優化的音樂配置
echo ""
echo "🎼 創建優化的音樂配置..."
cat > music_config.json << 'EOF'
{
  "default_volume": 0.5,
  "max_queue_size": 25,
  "auto_disconnect_delay": 900,
  "max_song_duration": 480,
  "enable_cache": true,
  "cache_size": 30,
  "reconnect_attempts": 1,
  "reconnect_delay": 20,
  "voice_timeout": 45,
  "enable_voice_reconnect": true,
  "max_voice_retries": 1,
  "voice_retry_delay": 30
}
EOF
echo "✅ 音樂配置已創建"

# 4. 修改音樂 Cog 的重連設定
echo ""
echo "🔧 修改音樂 Cog 重連設定..."
if [ -f "cogs/music.py" ]; then
    # 備份原檔案
    cp cogs/music.py cogs/music.py.backup
    
    # 修改重連設定
    sed -i 's/self\.max_reconnect_attempts = 3/self.max_reconnect_attempts = 1/g' cogs/music.py
    sed -i 's/self\.reconnect_delay = 5/self.reconnect_delay = 20/g' cogs/music.py
    sed -i 's/timeout=20\.0/timeout=45.0/g' cogs/music.py
    sed -i 's/timeout=30\.0/timeout=45.0/g' cogs/music.py
    
    echo "✅ 音樂 Cog 重連設定已修改"
else
    echo "⚠️ 找不到音樂 Cog 檔案"
fi

# 5. 檢查並安裝依賴
echo ""
echo "📦 檢查依賴..."
if [ -d "venv" ]; then
    source venv/bin/activate
    pip install -r requirements.txt --quiet
    echo "✅ 依賴檢查完成"
else
    echo "⚠️ 虛擬環境不存在，請先創建"
fi

# 6. 清理舊的日誌
echo ""
echo "🧹 清理舊的日誌..."
if [ -f "bot.log" ]; then
    mv bot.log bot.log.old.$(date +%Y%m%d_%H%M%S)
    echo "✅ 舊日誌已備份"
fi

# 7. 檢查網路連接
echo ""
echo "🌐 檢查網路連接..."
if ping -c 3 8.8.8.8 > /dev/null 2>&1; then
    echo "✅ 網路連接正常"
else
    echo "❌ 網路連接異常"
    echo "請檢查網路設定"
fi

# 8. 重新啟動 Bot
echo ""
echo "🚀 重新啟動 Bot..."
if [ -d "venv" ]; then
    source venv/bin/activate
    nohup python3 bot.py > bot.log 2>&1 &
    echo "✅ Bot 已重新啟動"
    echo "📋 查看日誌: tail -f bot.log"
else
    echo "❌ 虛擬環境不存在，無法啟動 Bot"
    echo "請先創建虛擬環境: python3 -m venv venv"
fi

echo ""
echo "✅ 快速修復完成！"
echo ""
echo "📋 修復內容:"
echo "• 減少重連次數 (3 → 1)"
echo "• 增加重連延遲 (5秒 → 20秒)"
echo "• 增加連接超時 (20秒 → 45秒)"
echo "• 優化 FFmpeg 配置"
echo "• 優化音樂配置"
echo ""
echo "💡 建議:"
echo "1. 監控 Bot 運行狀態"
echo "2. 如果問題持續，檢查網路連接"
echo "3. 考慮使用有線網路"
echo ""
echo "🔍 監控命令:"
echo "tail -f bot.log | grep -E '(voice|4006|ConnectionClosed)'" 