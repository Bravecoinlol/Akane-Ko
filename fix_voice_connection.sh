#!/bin/bash

# 語音連接修復腳本
# 修復 Discord Bot 語音連接問題 (錯誤代碼 4006)

echo "🔧 開始修復語音連接問題..."
echo "=================================="

# 檢查是否在正確目錄
if [ ! -f "bot.py" ]; then
    echo "❌ 錯誤：請在 Bot 目錄中執行此腳本"
    exit 1
fi

# 1. 檢查網路連接
echo "📡 檢查網路連接..."
echo "----------------------------------"

# 檢查基本網路連接
if ping -c 3 8.8.8.8 > /dev/null 2>&1; then
    echo "✅ 基本網路連接正常"
else
    echo "❌ 基本網路連接失敗"
    echo "請檢查網路設定"
    exit 1
fi

# 檢查 Discord API 連接
if curl -s --connect-timeout 10 https://discord.com/api/v10/gateway > /dev/null; then
    echo "✅ Discord API 連接正常"
else
    echo "❌ Discord API 連接失敗"
    echo "可能是 Discord 服務問題或網路限制"
fi

# 2. 檢查 FFmpeg
echo ""
echo "🎵 檢查 FFmpeg..."
echo "----------------------------------"

if command -v ffmpeg > /dev/null 2>&1; then
    ffmpeg_version=$(ffmpeg -version | head -n1 | cut -d' ' -f3)
    echo "✅ FFmpeg 已安裝: $ffmpeg_version"
else
    echo "❌ FFmpeg 未安裝"
    echo "正在安裝 FFmpeg..."
    sudo apt update
    sudo apt install -y ffmpeg
fi

# 3. 檢查 Python 環境
echo ""
echo "🐍 檢查 Python 環境..."
echo "----------------------------------"

# 檢測 Python 命令
if command -v python3 > /dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python > /dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "❌ 未找到 Python"
    exit 1
fi

echo "✅ 使用 Python 命令: $PYTHON_CMD"

# 檢查虛擬環境
if [ -d "venv" ]; then
    echo "✅ 虛擬環境存在"
    VENV_ACTIVATE="source venv/bin/activate"
else
    echo "❌ 虛擬環境不存在"
    echo "正在創建虛擬環境..."
    $PYTHON_CMD -m venv venv
    VENV_ACTIVATE="source venv/bin/activate"
fi

# 4. 檢查依賴
echo ""
echo "📦 檢查依賴..."
echo "----------------------------------"

$VENV_ACTIVATE && pip list | grep -E "(discord|yt-dlp|PyNaCl)" || {
    echo "❌ 缺少必要依賴"
    echo "正在安裝依賴..."
    $VENV_ACTIVATE && pip install -r requirements.txt
}

# 5. 優化 FFmpeg 配置
echo ""
echo "⚙️ 優化 FFmpeg 配置..."
echo "----------------------------------"

# 創建優化的 FFmpeg 配置
cat > ffmpeg_config.json << 'EOF'
{
  "ffmpeg_path": "ffmpeg",
  "ffmpeg_options": {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 10 -reconnect_at_eof 1 -reconnect_on_network_error 1",
    "options": "-vn -b:a 96k -bufsize 2048k -maxrate 128k -ar 48000 -ac 2"
  }
}
EOF

echo "✅ FFmpeg 配置已優化"

# 6. 優化音樂配置
echo ""
echo "🎼 優化音樂配置..."
echo "----------------------------------"

# 創建優化的音樂配置
cat > music_config.json << 'EOF'
{
  "default_volume": 0.5,
  "max_queue_size": 30,
  "auto_disconnect_delay": 600,
  "max_song_duration": 480,
  "enable_cache": true,
  "cache_size": 50,
  "reconnect_attempts": 2,
  "reconnect_delay": 10,
  "voice_timeout": 30,
  "enable_voice_reconnect": true,
  "max_voice_retries": 2,
  "voice_retry_delay": 15
}
EOF

echo "✅ 音樂配置已優化"

# 7. 創建語音連接修復腳本
echo ""
echo "🔧 創建語音連接修復腳本..."
echo "----------------------------------"

cat > voice_connection_fix.py << 'EOF'
#!/usr/bin/env python3
"""
語音連接修復工具
修復 Discord Bot 語音連接問題
"""

import asyncio
import discord
import json
import logging
import time
from discord.ext import commands

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('VoiceFix')

class VoiceConnectionFixer:
    def __init__(self):
        self.reconnect_attempts = {}
        self.max_reconnect_attempts = 2
        self.reconnect_delay = 15
        
    async def fix_voice_connection(self, voice_client):
        """修復語音連接"""
        if not voice_client:
            return False
            
        guild_id = voice_client.guild.id
        
        # 檢查重連次數
        if guild_id in self.reconnect_attempts:
            if self.reconnect_attempts[guild_id] >= self.max_reconnect_attempts:
                logger.warning(f"重連次數已達上限: {voice_client.guild.name}")
                return False
        else:
            self.reconnect_attempts[guild_id] = 0
            
        try:
            # 斷開現有連接
            if voice_client.is_connected():
                await voice_client.disconnect()
                await asyncio.sleep(2)
                
            # 等待一段時間後重連
            await asyncio.sleep(self.reconnect_delay)
            
            # 重新連接
            if voice_client.channel:
                await voice_client.connect(timeout=30.0, self_deaf=True)
                self.reconnect_attempts[guild_id] = 0
                logger.info(f"語音連接修復成功: {voice_client.guild.name}")
                return True
                
        except Exception as e:
            self.reconnect_attempts[guild_id] += 1
            logger.error(f"語音連接修復失敗: {e}")
            return False
            
    async def cleanup_voice_clients(self, bot):
        """清理無效的語音客戶端"""
        for guild in bot.guilds:
            if guild.voice_client:
                if not guild.voice_client.is_connected():
                    try:
                        await guild.voice_client.disconnect()
                        logger.info(f"清理無效語音客戶端: {guild.name}")
                    except:
                        pass

async def main():
    """主函數"""
    print("🔧 語音連接修復工具")
    print("=" * 30)
    
    # 載入配置
    try:
        with open('config.py', 'r', encoding='utf-8') as f:
            exec(f.read())
    except Exception as e:
        print(f"❌ 載入配置失敗: {e}")
        return
        
    # 創建 bot 實例
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True
    
    bot = commands.Bot(command_prefix='!', intents=intents)
    fixer = VoiceConnectionFixer()
    
    @bot.event
    async def on_ready():
        print(f"✅ Bot 已登入: {bot.user}")
        
        # 清理無效的語音客戶端
        await fixer.cleanup_voice_clients(bot)
        
        # 修復現有的語音連接
        for guild in bot.guilds:
            if guild.voice_client:
                print(f"🔧 修復語音連接: {guild.name}")
                success = await fixer.fix_voice_connection(guild.voice_client)
                if success:
                    print(f"✅ 修復成功: {guild.name}")
                else:
                    print(f"❌ 修復失敗: {guild.name}")
                    
        print("🔧 語音連接修復完成")
        await bot.close()
    
    try:
        await bot.start(TOKEN)
    except Exception as e:
        print(f"❌ 啟動 Bot 失敗: {e}")

if __name__ == "__main__":
    asyncio.run(main())
EOF

chmod +x voice_connection_fix.py
echo "✅ 語音連接修復腳本已創建"

# 8. 創建網路診斷腳本
echo ""
echo "🌐 創建網路診斷腳本..."
echo "----------------------------------"

cat > network_diagnosis.sh << 'EOF'
#!/bin/bash

echo "🌐 網路診斷工具"
echo "================"

echo "1. 基本網路連接測試..."
ping -c 4 8.8.8.8

echo ""
echo "2. DNS 解析測試..."
nslookup discord.com

echo ""
echo "3. Discord API 連接測試..."
curl -I --connect-timeout 10 https://discord.com/api/v10/gateway

echo ""
echo "4. 語音服務連接測試..."
curl -I --connect-timeout 10 https://voice.discord.com

echo ""
echo "5. 網路延遲測試..."
ping -c 4 discord.com

echo ""
echo "6. 路由追蹤..."
traceroute -m 15 discord.com

echo ""
echo "診斷完成！"
EOF

chmod +x network_diagnosis.sh
echo "✅ 網路診斷腳本已創建"

# 9. 創建語音連接監控腳本
echo ""
echo "📊 創建語音連接監控腳本..."
echo "----------------------------------"

cat > monitor_voice_connection.sh << 'EOF'
#!/bin/bash

echo "📊 語音連接監控工具"
echo "===================="

# 檢查 Bot 進程
if pgrep -f "bot.py" > /dev/null; then
    echo "✅ Bot 正在運行"
    BOT_PID=$(pgrep -f "bot.py")
    echo "Bot PID: $BOT_PID"
else
    echo "❌ Bot 未運行"
    exit 1
fi

# 監控語音連接狀態
echo ""
echo "🔍 監控語音連接狀態..."
echo "按 Ctrl+C 停止監控"

while true; do
    clear
    echo "📊 語音連接狀態監控"
    echo "===================="
    echo "時間: $(date)"
    echo ""
    
    # 檢查 Bot 進程
    if pgrep -f "bot.py" > /dev/null; then
        echo "✅ Bot 狀態: 運行中"
    else
        echo "❌ Bot 狀態: 已停止"
        break
    fi
    
    # 檢查最近的日誌
    echo ""
    echo "📋 最近的語音相關日誌:"
    echo "----------------------------------------"
    if [ -f "bot.log" ]; then
        tail -n 10 bot.log | grep -E "(voice|Voice|VOICE|4006|ConnectionClosed)" || echo "無語音相關日誌"
    else
        echo "日誌檔案不存在"
    fi
    
    # 檢查網路連接
    echo ""
    echo "🌐 網路連接狀態:"
    echo "----------------------------------------"
    if ping -c 1 discord.com > /dev/null 2>&1; then
        echo "✅ Discord 連接正常"
    else
        echo "❌ Discord 連接異常"
    fi
    
    # 檢查系統資源
    echo ""
    echo "💻 系統資源使用:"
    echo "----------------------------------------"
    echo "CPU 使用率: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
    echo "記憶體使用: $(free -h | grep Mem | awk '{print $3"/"$2}')"
    echo "磁碟使用: $(df -h / | tail -1 | awk '{print $5}')"
    
    sleep 5
done
EOF

chmod +x monitor_voice_connection.sh
echo "✅ 語音連接監控腳本已創建"

# 10. 執行修復
echo ""
echo "🔧 執行語音連接修復..."
echo "----------------------------------"

# 停止現有的 Bot
if pgrep -f "bot.py" > /dev/null; then
    echo "🛑 停止現有的 Bot..."
    pkill -f "bot.py"
    sleep 3
fi

# 清理無效的語音客戶端
echo "🧹 清理無效的語音客戶端..."
$VENV_ACTIVATE && python3 voice_connection_fix.py

# 重新啟動 Bot
echo "🚀 重新啟動 Bot..."
$VENV_ACTIVATE && nohup python3 bot.py > bot.log 2>&1 &

echo ""
echo "✅ 語音連接修復完成！"
echo ""
echo "📋 可用的工具:"
echo "• ./network_diagnosis.sh - 網路診斷"
echo "• ./monitor_voice_connection.sh - 語音連接監控"
echo "• ./voice_connection_fix.py - 語音連接修復"
echo ""
echo "💡 建議:"
echo "1. 如果問題持續，請檢查網路連接"
echo "2. 確保 Orange Pi 有穩定的網路連接"
echo "3. 考慮使用有線網路而非 WiFi"
echo "4. 檢查 Discord 服務狀態"
echo ""
echo "🔍 監控命令:"
echo "tail -f bot.log | grep -E '(voice|4006|ConnectionClosed)'" 