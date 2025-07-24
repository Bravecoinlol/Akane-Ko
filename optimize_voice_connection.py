#!/usr/bin/env python3
"""
語音連接優化工具
優化 Discord Bot 的語音連接機制，減少錯誤代碼 4006 的發生
"""

import json
import os
import re
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('VoiceOptimizer')

class VoiceConnectionOptimizer:
    def __init__(self):
        self.music_file = 'cogs/music.py'
        self.ffmpeg_config_file = 'ffmpeg_config.json'
        self.music_config_file = 'music_config.json'
        
    def optimize_ffmpeg_config(self):
        """優化 FFmpeg 配置"""
        optimized_config = {
            "ffmpeg_path": "ffmpeg",
            "ffmpeg_options": {
                "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 15 -reconnect_at_eof 1 -reconnect_on_network_error 1 -reconnect_on_http_error 1",
                "options": "-vn -b:a 96k -bufsize 2048k -maxrate 128k -ar 48000 -ac 2 -af volume=0.5"
            }
        }
        
        with open(self.ffmpeg_config_file, 'w', encoding='utf-8') as f:
            json.dump(optimized_config, f, indent=2, ensure_ascii=False)
            
        logger.info("✅ FFmpeg 配置已優化")
        
    def optimize_music_config(self):
        """優化音樂配置"""
        optimized_config = {
            "default_volume": 0.5,
            "max_queue_size": 25,
            "auto_disconnect_delay": 900,
            "max_song_duration": 480,
            "enable_cache": True,
            "cache_size": 30,
            "reconnect_attempts": 1,
            "reconnect_delay": 20,
            "voice_timeout": 45,
            "enable_voice_reconnect": True,
            "max_voice_retries": 1,
            "voice_retry_delay": 30,
            "connection_timeout": 30,
            "voice_heartbeat_interval": 60,
            "enable_voice_heartbeat": True
        }
        
        with open(self.music_config_file, 'w', encoding='utf-8') as f:
            json.dump(optimized_config, f, indent=2, ensure_ascii=False)
            
        logger.info("✅ 音樂配置已優化")
        
    def optimize_music_cog(self):
        """優化音樂 Cog 的重連機制"""
        if not os.path.exists(self.music_file):
            logger.error(f"❌ 找不到音樂檔案: {self.music_file}")
            return False
            
        try:
            with open(self.music_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 優化重連設定
            optimizations = [
                # 減少最大重連次數
                (r'self\.max_reconnect_attempts = \d+', 'self.max_reconnect_attempts = 1'),
                (r'self\.reconnect_delay = \d+', 'self.reconnect_delay = 20'),
                
                # 優化語音連接超時
                (r'timeout=20\.0', 'timeout=45.0'),
                (r'timeout=30\.0', 'timeout=45.0'),
                
                # 增加連接前的等待時間
                (r'await asyncio\.sleep\(retry_delay\)', 'await asyncio.sleep(retry_delay * 2)'),
                
                # 優化重連延遲計算
                (r'retry_delay \*= 2', 'retry_delay = min(retry_delay * 2, 30)'),
            ]
            
            for pattern, replacement in optimizations:
                content = re.sub(pattern, replacement, content)
                
            # 添加語音連接穩定性檢查
            stability_check = '''
    async def check_voice_stability(self, voice_client):
        """檢查語音連接穩定性"""
        if not voice_client or not voice_client.is_connected():
            return False
            
        try:
            # 檢查 WebSocket 連接狀態
            if hasattr(voice_client, 'ws') and voice_client.ws:
                if voice_client.ws.closed:
                    logger.warning(f"[check_voice_stability] WebSocket 已關閉: {voice_client.guild.name}")
                    return False
                    
            # 檢查語音狀態
            if voice_client.is_playing() or voice_client.is_paused():
                return True
                
            # 如果沒有播放但連接正常，也認為是穩定的
            return True
            
        except Exception as e:
            logger.error(f"[check_voice_stability] 檢查語音穩定性失敗: {e}")
            return False
'''
            
            # 在 Music 類中添加穩定性檢查方法
            if 'async def check_voice_stability' not in content:
                # 找到 Music 類的結束位置
                class_end = content.rfind('class Music(commands.Cog):')
                if class_end != -1:
                    # 找到第一個方法的位置
                    first_method = content.find('def load_ffmpeg_config', class_end)
                    if first_method != -1:
                        content = content[:first_method] + stability_check + '\n    ' + content[first_method:]
                        
            # 優化語音連接方法
            voice_connection_optimization = '''
    async def ensure_voice_connection(self, interaction, auto_join=True):
        """確保語音連線存在 - 優化版本"""
        try:
            # 檢查用戶是否在語音頻道
            if not interaction.user.voice:
                embed = discord.Embed(
                    title="❌ 未連接語音頻道",
                    description="請先加入語音頻道",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="如何加入",
                    value="1. 點擊語音頻道\\n2. 等待連接完成\\n3. 再次使用命令",
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return None

            voice_channel = interaction.user.voice.channel
            
            # 檢查 Bot 權限
            if not voice_channel.permissions_for(interaction.guild.me).connect:
                embed = discord.Embed(
                    title="❌ 權限不足",
                    description="Bot 無法加入語音頻道",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="需要的權限",
                    value="• 連接語音頻道\\n• 說話\\n• 使用語音活動",
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return None

            # 檢查是否已經連接且穩定
            vc = interaction.guild.voice_client
            if vc and vc.is_connected():
                # 檢查連接穩定性
                if await self.check_voice_stability(vc):
                    # 檢查是否在同一個頻道
                    if vc.channel == voice_channel:
                        return vc
                    else:
                        # 在不同頻道，需要移動
                        try:
                            await vc.move_to(voice_channel)
                            logger.info(f"[ensure_voice_connection] 已移動到頻道: {voice_channel.name}")
                            return vc
                        except Exception as e:
                            logger.error(f"[ensure_voice_connection] 移動頻道失敗: {e}")
                            # 如果移動失敗，斷開重連
                            await vc.disconnect()
                            vc = None
                else:
                    # 連接不穩定，斷開重連
                    logger.warning(f"[ensure_voice_connection] 語音連接不穩定，重新連接: {voice_channel.name}")
                    await vc.disconnect()
                    vc = None

            # 如果沒有連接且允許自動加入
            if auto_join and not vc:
                try:
                    # 添加重連機制 - 優化版本
                    max_retries = 2  # 減少重試次數
                    retry_delay = 5   # 增加初始延遲
                    
                    for attempt in range(max_retries):
                        try:
                            # 連接前等待
                            if attempt > 0:
                                await asyncio.sleep(retry_delay)
                                retry_delay = min(retry_delay * 2, 20)  # 限制最大延遲
                            
                            vc = await voice_channel.connect(timeout=45.0, self_deaf=True)
                            logger.info(f"[ensure_voice_connection] 成功連接到頻道: {voice_channel.name}")
                            
                            # 設定語音客戶端屬性
                            vc.retry_count = 0
                            vc.max_retries = 1  # 減少最大重試次數
                            
                            # 等待連接穩定
                            await asyncio.sleep(2)
                            
                            return vc
                            
                        except asyncio.TimeoutError:
                            logger.warning(f"[ensure_voice_connection] 連接超時，嘗試 {attempt + 1}/{max_retries}")
                            if attempt < max_retries - 1:
                                continue
                            else:
                                embed = discord.Embed(
                                    title="⏰ 連接超時",
                                    description="連接語音頻道時發生超時",
                                    color=discord.Color.orange()
                                )
                                embed.add_field(
                                    name="可能原因",
                                    value="• 網路連線不穩定\\n• Discord服務繁忙\\n• 頻道擁擠",
                                    inline=False
                                )
                                embed.add_field(
                                    name="建議",
                                    value="• 檢查網路連線\\n• 稍後再試\\n• 嘗試其他頻道",
                                    inline=False
                                )
                                await interaction.followup.send(embed=embed, ephemeral=True)
                                return None
                                
                        except discord.ClientException as e:
                            if "Already connected to a voice channel" in str(e):
                                # 已經連接，獲取現有連接
                                vc = interaction.guild.voice_client
                                if vc and vc.is_connected():
                                    return vc
                            else:
                                raise e
                                
                        except Exception as e:
                            logger.error(f"[ensure_voice_connection] 連接失敗 (嘗試 {attempt + 1}): {e}")
                            if attempt < max_retries - 1:
                                continue
                            else:
                                embed = discord.Embed(
                                    title="❌ 連接失敗",
                                    description="無法連接到語音頻道",
                                    color=discord.Color.red()
                                )
                                embed.add_field(
                                    name="錯誤詳情",
                                    value=str(e)[:100] + "..." if len(str(e)) > 100 else str(e),
                                    inline=False
                                )
                                embed.add_field(
                                    name="建議",
                                    value="• 檢查網路連線\\n• 確認頻道權限\\n• 稍後再試",
                                    inline=False
                                )
                                await interaction.followup.send(embed=embed, ephemeral=True)
                                return None
                                
                except Exception as e:
                    logger.error(f"[ensure_voice_connection] 連接過程發生錯誤: {e}")
                    embed = discord.Embed(
                        title="❌ 連接錯誤",
                        description="連接語音頻道時發生未預期的錯誤",
                        color=discord.Color.red()
                    )
                    embed.add_field(
                        name="錯誤詳情",
                        value=str(e)[:100] + "..." if len(str(e)) > 100 else str(e),
                        inline=False
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return None

            return None
            
        except Exception as e:
            logger.error(f"[ensure_voice_connection] 確保語音連線失敗: {e}")
            try:
                embed = discord.Embed(
                    title="❌ 語音連線錯誤",
                    description="處理語音連線時發生錯誤",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="錯誤詳情",
                    value=str(e)[:100] + "..." if len(str(e)) > 100 else str(e),
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            except:
                logger.error(f"[ensure_voice_connection] 無法發送錯誤訊息: {e}")
            return None
'''
            
            # 替換原有的 ensure_voice_connection 方法
            if 'async def ensure_voice_connection' in content:
                # 找到方法開始和結束
                method_start = content.find('async def ensure_voice_connection')
                if method_start != -1:
                    # 找到方法結束（下一個方法開始或類結束）
                    next_method = content.find('\n    async def ', method_start + 1)
                    class_end = content.find('\nclass ', method_start + 1)
                    
                    end_pos = -1
                    if next_method != -1 and class_end != -1:
                        end_pos = min(next_method, class_end)
                    elif next_method != -1:
                        end_pos = next_method
                    elif class_end != -1:
                        end_pos = class_end
                        
                    if end_pos != -1:
                        content = content[:method_start] + voice_connection_optimization + content[end_pos:]
                        
            with open(self.music_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info("✅ 音樂 Cog 已優化")
            return True
            
        except Exception as e:
            logger.error(f"❌ 優化音樂 Cog 失敗: {e}")
            return False
            
    def create_voice_monitor(self):
        """創建語音連接監控腳本"""
        monitor_script = '''#!/usr/bin/env python3
"""
語音連接監控工具
實時監控 Discord Bot 的語音連接狀態
"""

import asyncio
import discord
import logging
import time
from discord.ext import commands

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('VoiceMonitor')

class VoiceConnectionMonitor:
    def __init__(self):
        self.voice_stats = {}
        self.connection_errors = []
        
    async def monitor_voice_connections(self, bot):
        """監控語音連接"""
        while True:
            try:
                for guild in bot.guilds:
                    if guild.voice_client:
                        vc = guild.voice_client
                        guild_id = guild.id
                        
                        # 記錄連接狀態
                        status = {
                            'connected': vc.is_connected(),
                            'playing': vc.is_playing(),
                            'paused': vc.is_paused(),
                            'channel': vc.channel.name if vc.channel else None,
                            'timestamp': time.time()
                        }
                        
                        self.voice_stats[guild_id] = status
                        
                        # 檢查連接問題
                        if not vc.is_connected():
                            error_msg = f"語音連接斷開: {guild.name}"
                            if error_msg not in self.connection_errors:
                                self.connection_errors.append(error_msg)
                                logger.warning(error_msg)
                                
                        # 檢查 WebSocket 狀態
                        if hasattr(vc, 'ws') and vc.ws:
                            if vc.ws.closed:
                                logger.warning(f"WebSocket 已關閉: {guild.name}")
                                
                # 清理舊的錯誤記錄
                current_time = time.time()
                self.connection_errors = [e for e in self.connection_errors 
                                       if current_time - getattr(e, 'timestamp', 0) < 300]
                                       
                await asyncio.sleep(10)  # 每10秒檢查一次
                
            except Exception as e:
                logger.error(f"監控語音連接失敗: {e}")
                await asyncio.sleep(30)

async def main():
    """主函數"""
    print("📊 語音連接監控工具")
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
    monitor = VoiceConnectionMonitor()
    
    @bot.event
    async def on_ready():
        print(f"✅ Bot 已登入: {bot.user}")
        print("📊 開始監控語音連接...")
        
        # 啟動監控任務
        asyncio.create_task(monitor.monitor_voice_connections(bot))
        
        # 保持運行
        while True:
            await asyncio.sleep(60)
            
            # 顯示統計信息
            print("\\n📊 語音連接統計:")
            for guild_id, stats in monitor.voice_stats.items():
                guild = bot.get_guild(guild_id)
                if guild:
                    print(f"  {guild.name}: {'連接' if stats['connected'] else '斷開'}")
                    
            if monitor.connection_errors:
                print("\\n⚠️ 最近的連接錯誤:")
                for error in monitor.connection_errors[-5:]:
                    print(f"  {error}")
    
    try:
        await bot.start(TOKEN)
    except Exception as e:
        print(f"❌ 啟動 Bot 失敗: {e}")

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        with open('voice_monitor.py', 'w', encoding='utf-8') as f:
            f.write(monitor_script)
            
        # 設定執行權限
        os.chmod('voice_monitor.py', 0o755)
        logger.info("✅ 語音連接監控工具已創建")
        
    def run_optimization(self):
        """執行所有優化"""
        print("🔧 開始優化語音連接...")
        print("=" * 40)
        
        # 1. 優化 FFmpeg 配置
        print("1. 優化 FFmpeg 配置...")
        self.optimize_ffmpeg_config()
        
        # 2. 優化音樂配置
        print("2. 優化音樂配置...")
        self.optimize_music_config()
        
        # 3. 優化音樂 Cog
        print("3. 優化音樂 Cog...")
        if self.optimize_music_cog():
            print("✅ 音樂 Cog 優化成功")
        else:
            print("❌ 音樂 Cog 優化失敗")
            
        # 4. 創建監控工具
        print("4. 創建監控工具...")
        self.create_voice_monitor()
        
        print("\\n✅ 語音連接優化完成！")
        print("\\n📋 優化內容:")
        print("• 減少重連次數 (從 3 次改為 1 次)")
        print("• 增加重連延遲 (從 5 秒改為 20 秒)")
        print("• 優化 FFmpeg 參數，提高穩定性")
        print("• 添加語音連接穩定性檢查")
        print("• 創建語音連接監控工具")
        print("\\n💡 建議:")
        print("1. 重新啟動 Bot 以應用優化")
        print("2. 使用 ./voice_monitor.py 監控語音連接")
        print("3. 如果問題持續，檢查網路連接")

if __name__ == "__main__":
    optimizer = VoiceConnectionOptimizer()
    optimizer.run_optimization() 