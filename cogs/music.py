import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import yt_dlp
import random
import re
import time
import hashlib
import json
import os
import logging
from collections import deque

# 設定 logger
logger = logging.getLogger('Music')

def is_url(text):
    url_pattern = re.compile(r'https?://')
    return bool(url_pattern.match(text))

class SongCache:
    """歌曲快取系統，減少重複下載"""
    def __init__(self, cache_file="song_cache.json", max_cache_size=100):
        self.cache_file = cache_file
        self.max_cache_size = max_cache_size
        self.cache = {}
        self.load_cache()
    
    def load_cache(self):
        """載入快取"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
        except Exception as e:
            logger.error(f"[SongCache] 載入快取失敗: {e}")
            self.cache = {}
    
    def save_cache(self):
        """保存快取"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[SongCache] 保存快取失敗: {e}")
    
    def get_cache_key(self, query):
        """生成快取鍵"""
        return hashlib.md5(query.encode()).hexdigest()
    
    def get(self, query):
        """獲取快取"""
        key = self.get_cache_key(query)
        if key in self.cache:
            cache_data = self.cache[key]
            # 檢查快取是否過期（24小時）
            if time.time() - cache_data.get('timestamp', 0) < 86400:
                return cache_data.get('data')
        return None
    
    def set(self, query, data):
        """設置快取"""
        key = self.get_cache_key(query)
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
        
        # 如果快取太大，清理舊的項目
        if len(self.cache) > self.max_cache_size:
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k].get('timestamp', 0))
            del self.cache[oldest_key]
        
        self.save_cache()

class AutoMusicPlayer:
    def __init__(self):
        self.queue = deque()  # 使用 deque 提高效能
        self.current = None
        self.repeat = False
        self.volume = 0.5
        self.is_paused = False
        self.autoplay = False
        self.category = None
        self.retry_count = 0
        self.max_retries = 3

    def add(self, song):
        logger.debug(f"[Queue] 新增歌曲：{song['title']}")
        self.queue.append(song)

    def next(self):
        # 如果開啟重複播放且有當前歌曲
        if self.repeat and self.current:
            logger.debug(f"[Queue] 重複播放：{self.current['title']}")
            return self.current
        
        # 如果隊列中有歌曲
        if self.queue:
            self.current = self.queue.popleft()
            logger.debug(f"[Queue] 取出下一首：{self.current['title']}")
            return self.current
        
        # 如果沒有歌曲且開啟重複播放，但沒有當前歌曲
        if self.repeat and not self.current:
            logger.debug("[Queue] 重複播放開啟但沒有當前歌曲")
            return None
            
        # 播放隊列空了
        self.current = None
        logger.debug("[Queue] 播放隊列空了")
        return None

    def clear_queue(self):
        """清空播放隊列"""
        self.queue.clear()
        logger.info("[Queue] 播放隊列已清空")

class MusicControls(discord.ui.View):
    def __init__(self, bot, guild_id, voice_client, player):
        super().__init__(timeout=300)  # 5分鐘後按鈕失效
        self.bot = bot
        self.guild_id = guild_id
        self.vc = voice_client
        self.player = player

    async def update_message(self, interaction, content):
        try:
            await interaction.message.edit(content=content, view=self)
        except Exception as e:
            logger.error(f"[MusicControls] 更新訊息失敗: {e}")

    @discord.ui.button(label='🔉', style=discord.ButtonStyle.secondary)
    async def volume_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if not self.vc or not self.vc.is_connected():
                await interaction.response.send_message("❌ 機器人未連接到語音頻道", ephemeral=True)
                return
                
            self.player.volume = max(0.0, self.player.volume - 0.1)
            if self.vc.source:
                self.vc.source.volume = self.player.volume
            await interaction.response.send_message(f"🔉 音量調低為 {int(self.player.volume * 100)}%", ephemeral=True)
            await self.update_message(interaction, f"▶️ 正在播放：{self.player.current['title']}")
        except Exception as e:
            logger.error(f"[MusicControls] 音量調低失敗: {e}")
            await interaction.response.send_message("❌ 調整音量失敗", ephemeral=True)

    @discord.ui.button(label='🔊', style=discord.ButtonStyle.secondary)
    async def volume_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if not self.vc or not self.vc.is_connected():
                await interaction.response.send_message("❌ 機器人未連接到語音頻道", ephemeral=True)
                return
                
            self.player.volume = min(1.0, self.player.volume + 0.1)
            if self.vc.source:
                self.vc.source.volume = self.player.volume
            await interaction.response.send_message(f"🔊 音量調高為 {int(self.player.volume * 100)}%", ephemeral=True)
            await self.update_message(interaction, f"▶️ 正在播放：{self.player.current['title']}")
        except Exception as e:
            logger.error(f"[MusicControls] 音量調高失敗: {e}")
            await interaction.response.send_message("❌ 調整音量失敗", ephemeral=True)

    @discord.ui.button(label='⏯️', style=discord.ButtonStyle.blurple)
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if not self.vc or not self.vc.is_connected():
                await interaction.response.send_message("❌ 機器人未連接到語音頻道", ephemeral=True)
                return
                
            if not self.vc.is_playing() and not self.vc.is_paused():
                await interaction.response.send_message("❌ 目前沒有播放中的音樂", ephemeral=True)
                return
                
            if self.vc.is_playing():
                self.vc.pause()
                self.player.is_paused = True
                await interaction.response.send_message("⏸ 已暫停播放", ephemeral=True)
            elif self.vc.is_paused():
                self.vc.resume()
                self.player.is_paused = False
                await interaction.response.send_message("▶️ 已繼續播放", ephemeral=True)
        except Exception as e:
            logger.error(f"[MusicControls] 暫停/繼續播放失敗: {e}")
            await interaction.response.send_message("❌ 操作失敗", ephemeral=True)

    @discord.ui.button(label='⏭', style=discord.ButtonStyle.green)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if not self.vc or not self.vc.is_connected():
                await interaction.response.send_message("❌ 機器人未連接到語音頻道", ephemeral=True)
                return
                
            if not self.vc.is_playing() and not self.vc.is_paused():
                await interaction.response.send_message("❌ 目前沒有播放中的音樂", ephemeral=True)
                return
                
            self.vc.stop()
            await interaction.response.send_message("⏭ 跳到下一首", ephemeral=True)
        except Exception as e:
            logger.error(f"[MusicControls] 跳過歌曲失敗: {e}")
            await interaction.response.send_message("❌ 跳過歌曲失敗", ephemeral=True)

    @discord.ui.button(label='🔁', style=discord.ButtonStyle.secondary)
    async def toggle_repeat(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            self.player.repeat = not self.player.repeat
            status = "開啟" if self.player.repeat else "關閉"
            await interaction.response.send_message(f"🔁 重複播放：{status}", ephemeral=True)
        except Exception as e:
            logger.error(f"[MusicControls] 切換重複播放失敗: {e}")
            await interaction.response.send_message("❌ 切換重複播放失敗", ephemeral=True)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = {}
        self.song_cache = SongCache()
        self.ffmpeg_config = self.load_ffmpeg_config()
        self.connection_retries = {}
        self.auto_stream_categories = {}
        self.reconnect_attempts = {}
        self.max_reconnect_attempts = 1
        self.reconnect_delay = 20
        
        # 載入音樂配置
        self.load_music_config()
        
        # 標記需要啟動清理任務
        self._cleanup_task_started = False
        
        logger.info("[Music] 音樂系統已啟動")
        
        # 自動串流類別對應搜尋關鍵字
        self.category_keywords = {
            "日文流行": [
                "J-Pop hits",
                "Japanese idol songs", 
                "Anime theme songs",
                "Tokyo pop tunes",
                "日本流行樂",
                "日本偶像音樂",
                "動漫主題曲",
                "東京流行旋律",
                "和風流行曲"
            ],
            "英文流行": [
                "Top Billboard hits",
                "US pop charts",
                "Global pop anthems", 
                "Modern pop tunes",
                "Western chart toppers",
                "American pop hits",
                "Contemporary hits",
                "International pop",
                "Hot radio singles"
            ],
            "中文流行": [
                "華語金曲",
                "台灣熱門歌曲",
                "大陸流行音樂",
                "中文排行榜",
                "華語新歌",
                "國語熱門曲",
                "中港台流行曲",
                "華人音樂推薦",
                "中文青春歌曲"
            ]
        }

    def load_ffmpeg_config(self):
        """載入 FFmpeg 配置"""
        try:
            with open('ffmpeg_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info("[Music] FFmpeg 配置載入成功")
                return config
        except FileNotFoundError:
            logger.warning("[Music] FFmpeg 配置檔案不存在，使用預設配置")
            config = {
                "ffmpeg_path": "ffmpeg",
                "ffmpeg_options": {
                    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                    "options": "-vn -b:a 128k -bufsize 3072k"
                }
            }
            self.save_ffmpeg_config(config)
            return config
        except json.JSONDecodeError as e:
            logger.error(f"[Music] FFmpeg 配置檔案格式錯誤: {e}")
            return self.get_default_ffmpeg_config()
        except Exception as e:
            logger.error(f"[Music] 載入 FFmpeg 配置失敗: {e}")
            return self.get_default_ffmpeg_config()

    def load_music_config(self):
        """載入音樂配置"""
        try:
            with open('music_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info("[Music] 音樂配置載入成功")
                return config
        except FileNotFoundError:
            logger.warning("[Music] 音樂配置檔案不存在，使用預設配置")
            config = {
                "default_volume": 0.5,
                "max_queue_size": 50,
                "auto_disconnect_delay": 300,
                "max_song_duration": 600,
                "enable_cache": True,
                "cache_size": 100,
                "reconnect_attempts": 3,
                "reconnect_delay": 5
            }
            self.save_music_config(config)
            return config
        except json.JSONDecodeError as e:
            logger.error(f"[Music] 音樂配置檔案格式錯誤: {e}")
            return self.get_default_music_config()
        except Exception as e:
            logger.error(f"[Music] 載入音樂配置失敗: {e}")
            return self.get_default_music_config()

    def save_music_config(self, config=None):
        """保存音樂配置"""
        if config is None:
            config = self.load_music_config()
        try:
            with open('music_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info("[Music] 音樂配置保存成功")
        except Exception as e:
            logger.error(f"[Music] 保存音樂配置失敗: {e}")

    def get_default_music_config(self):
        """取得預設音樂配置"""
        return {
            "default_volume": 0.5,
            "max_queue_size": 50,
            "auto_disconnect_delay": 300,
            "max_song_duration": 600,
            "enable_cache": True,
            "cache_size": 100,
            "reconnect_attempts": 3,
            "reconnect_delay": 5
        }

    def get_player(self, guild_id):
        return self.players.setdefault(guild_id, AutoMusicPlayer())

    async def fetch_song_with_retry(self, keyword_or_url, max_retries=3):
        """帶重試機制的歌曲獲取"""
        if isinstance(keyword_or_url, list):
            keyword_or_url = keyword_or_url[0] if keyword_or_url else ""
        if not isinstance(keyword_or_url, str):
            logger.error(f"[fetch_song] 參數型態錯誤，期望字串，得到：{type(keyword_or_url)}")
            return None

        # 檢查快取
        cached_result = self.song_cache.get(keyword_or_url)
        if cached_result:
            logger.debug(f"[fetch_song] 使用快取結果：{cached_result.get('title', '未知標題')}")
            return cached_result

        # 多個 ytdl 配置，按優先順序嘗試，針對網路不穩定優化
        ytdl_configs = [
            # 配置1: 標準配置，較短超時
            {
                'format': 'bestaudio/best',
                'noplaylist': True,
                'quiet': True,
                'default_search': 'ytsearch',
                'extract_flat': 'in_playlist',
                'socket_timeout': 60,
                'retries': 5,
                'fragment_retries': 5,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            },
            # 配置2: 更長的超時，更多重試
            {
                'format': 'bestaudio/best',
                'noplaylist': True,
                'quiet': True,
                'default_search': 'ytsearch',
                'extract_flat': 'in_playlist',
                'socket_timeout': 120,
                'retries': 10,
                'fragment_retries': 10,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            },
            # 配置3: 最保守的配置
            {
                'format': 'bestaudio/best',
                'noplaylist': True,
                'quiet': True,
                'default_search': 'ytsearch',
                'extract_flat': 'in_playlist',
                'socket_timeout': 180,
                'retries': 15,
                'fragment_retries': 15,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
                }
            }
        ]

        for config_idx, ytdl_opts in enumerate(ytdl_configs):
            for attempt in range(max_retries):
                try:
                    logger.debug(f"[fetch_song] 嘗試配置 {config_idx + 1}，第 {attempt + 1} 次嘗試")
                    
                    # 添加額外的錯誤處理選項
                    ytdl_opts.update({
                        'ignoreerrors': True,
                        'no_warnings': False,
                        'extractor_retries': 3,
                        'file_access_retries': 3,
                        'fragment_retries': ytdl_opts.get('fragment_retries', 5),
                        'retry_sleep': 2,
                        'max_sleep_interval': 10,
                    })
                    
                    with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
                        info = ytdl.extract_info(keyword_or_url, download=False)
                        
                        if not info:
                            logger.warning(f"[fetch_song] 配置 {config_idx + 1} 無法提取資訊")
                            continue
                        
                        if 'entries' in info:
                            entries = info['entries']
                            if entries:
                                song_info = random.choice(entries)
                                try:
                                    full_info = ytdl.extract_info(song_info['url'], download=False)
                                    if full_info and 'url' in full_info:
                                        logger.info(f"[fetch_song] 找到歌曲：{full_info['title']}")
                                        self.song_cache.set(keyword_or_url, full_info)
                                        return full_info
                                except Exception as e:
                                    logger.warning(f"[fetch_song] 提取完整資訊失敗: {e}")
                                    continue
                        else:
                            if 'url' in info:
                                logger.info(f"[fetch_song] 找到歌曲：{info.get('title', '未知標題')}")
                                self.song_cache.set(keyword_or_url, info)
                                return info
                            
                except Exception as e:
                    logger.warning(f"[fetch_song] 配置 {config_idx + 1} 失敗: {e}")
                    if attempt < max_retries - 1:
                        wait_time = min(2 ** attempt, 10)  # 指數退避，最大等待10秒
                        logger.debug(f"[fetch_song] 等待 {wait_time} 秒後重試...")
                        await asyncio.sleep(wait_time)
                        continue
                    
        logger.error(f"[fetch_song] 所有嘗試都失敗了")
        return None

    async def ensure_voice_connection(self, interaction, auto_join=True):
        """確保語音連線存在"""
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
                    value="1. 點擊語音頻道\n2. 等待連接完成\n3. 再次使用命令",
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
                    value="• 連接語音頻道\n• 說話\n• 使用語音活動",
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return None

            # 檢查是否已經連接
            vc = interaction.guild.voice_client
            if vc and vc.is_connected():
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
                        embed = discord.Embed(
                            title="❌ 移動頻道失敗",
                            description="無法移動到新的語音頻道",
                            color=discord.Color.red()
                        )
                        embed.add_field(
                            name="錯誤詳情",
                            value=str(e)[:100] + "..." if len(str(e)) > 100 else str(e),
                            inline=False
                        )
                        await interaction.followup.send(embed=embed, ephemeral=True)
                        return None

            # 如果沒有連接且允許自動加入
            if auto_join:
                try:
                    # 添加重連機制
                    max_retries = 3
                    retry_delay = 2
                    
                    for attempt in range(max_retries):
                        try:
                            vc = await voice_channel.connect(timeout=45.0, self_deaf=True)
                            logger.info(f"[ensure_voice_connection] 成功連接到頻道: {voice_channel.name}")
                            
                            # 設定語音客戶端屬性
                            vc.retry_count = 0
                            vc.max_retries = 3
                            
                            return vc
                            
                        except asyncio.TimeoutError:
                            logger.warning(f"[ensure_voice_connection] 連接超時，嘗試 {attempt + 1}/{max_retries}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay)
                                retry_delay *= 2  # 指數退避
                            else:
                                embed = discord.Embed(
                                    title="⏰ 連接超時",
                                    description="連接語音頻道時發生超時",
                                    color=discord.Color.orange()
                                )
                                embed.add_field(
                                    name="可能原因",
                                    value="• 網路連線不穩定\n• Discord服務繁忙\n• 頻道擁擠",
                                    inline=False
                                )
                                embed.add_field(
                                    name="建議",
                                    value="• 檢查網路連線\n• 稍後再試\n• 嘗試其他頻道",
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
                                await asyncio.sleep(retry_delay)
                                retry_delay *= 2
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
                                    value="• 檢查網路連線\n• 確認頻道權限\n• 稍後再試",
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

    async def play_next(self, vc, guild_id, interaction=None):
        player = self.get_player(guild_id)
        song = player.next()

        # 如果播放隊列沒歌且開啟自動串流，嘗試自動找歌加入
        if not song and player.autoplay and player.category:
            keywords = self.category_keywords.get(player.category)
            if keywords:
                keyword = random.choice(keywords)
                print(f"[play_next] 自動串流模式，隨機搜尋關鍵字：{keyword}")
                song = await self.fetch_song_with_retry(keyword)
                if song:
                    player.add({"url": song['url'], "title": song['title']})
                    song = player.next()

        if not song:
            if interaction:
                await interaction.followup.send("🎵 播放隊列已結束")
            return

        # 使用配置檔案中的 FFmpeg 選項
        ffmpeg_options = self.ffmpeg_config.get('ffmpeg_options', {})
        executable = self.ffmpeg_config.get('ffmpeg_path', 'ffmpeg')
        
        try:
            # 嘗試使用標準 FFmpeg 選項
            try:
                source = discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(
                        song['url'],
                        before_options=ffmpeg_options.get('before_options', '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'),
                        options=ffmpeg_options.get('options', '-vn -b:a 128k -bufsize 3072k'),
                        executable=executable
                    ),
                    volume=player.volume
                )
            except Exception as ffmpeg_error:
                print(f"[play_next] 標準 FFmpeg 選項失敗，使用備用選項: {ffmpeg_error}")
                # 使用備用 FFmpeg 選項
                source = discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(
                        song['url'],
                        before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                        options='-vn -b:a 96k -bufsize 2048k',
                        executable=executable
                    ),
                    volume=player.volume
                )
            
            def after_callback(error):
                if error:
                    print(f"[after_callback] 播放錯誤: {error}")
                # 使用線程安全的方式調用異步函數
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.run_coroutine_threadsafe(
                            self.after_playing(error, vc, guild_id), 
                            loop
                        )
                    else:
                        # 如果沒有運行中的事件循環，創建一個新的
                        asyncio.run(self.after_playing(error, vc, guild_id))
                except Exception as e:
                    print(f"[after_callback] 調用 after_playing 失敗: {e}")
            
            vc.play(source, after=after_callback)
            
            if interaction:
                try:
                    await interaction.followup.send(
                        f"▶️ 正在播放：{song['title']}", 
                        view=MusicControls(self.bot, guild_id, vc, player), 
                        ephemeral=False
                    )
                except Exception as e:
                    print(f"[play_next] 發送互動訊息失敗: {e}")
                    
        except Exception as e:
            print(f"[play_next] 播放失敗: {e}")
            player.retry_count += 1
            if player.retry_count < player.max_retries:
                await asyncio.sleep(2)
                await self.play_next(vc, guild_id, interaction)
            else:
                player.retry_count = 0
                if interaction:
                    await interaction.followup.send("❌ 播放失敗，請稍後再試")

    async def after_playing(self, error, vc, guild_id):
        """播放結束後的處理"""
        if error:
            print(f"[after_playing] 播放錯誤: {error}")
        
        try:
            # 檢查是否仍在語音頻道
            if vc.is_connected():
                await self.play_next(vc, guild_id)
            else:
                await vc.disconnect()
                if guild_id in self.players:
                    del self.players[guild_id]
        except Exception as e:
            print(f"[after_playing] 處理播放結束時發生錯誤: {e}")

    @app_commands.command(name="play", description="播放音樂 (支援連結與關鍵字)")
    @app_commands.describe(query="YouTube 連結或搜尋字詞")
    async def play(self, interaction: discord.Interaction, query: str):
        try:
            # 先回應互動，避免超時
            await interaction.response.defer(thinking=True)
        except discord.NotFound:
            # 如果互動已經超時，直接返回
            logger.warning(f"[play] 互動已超時，用戶: {interaction.user.name}")
            return
        except Exception as e:
            logger.error(f"[play] 回應互動失敗: {e}")
            return

        try:
            # 檢查查詢字串
            if not query or len(query.strip()) == 0:
                embed = discord.Embed(
                    title="❌ 參數錯誤",
                    description="請提供有效的連結或搜尋關鍵字",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="正確用法",
                    value="`/play 歌曲名稱` 或 `/play YouTube連結`",
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
                
            if len(query) > 200:
                embed = discord.Embed(
                    title="❌ 查詢過長",
                    description="查詢字串太長，請縮短後再試",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="限制",
                    value="查詢字串不能超過200個字符",
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # 確保語音連接
            vc = await self.ensure_voice_connection(interaction)
            if not vc:
                return

            player = self.get_player(interaction.guild.id)
            player.retry_count = 0  # 重置重試計數

            # 顯示載入訊息
            loading_embed = discord.Embed(
                title="🔍 正在搜尋歌曲...",
                description=f"正在處理：`{query[:50]}{'...' if len(query) > 50 else ''}`",
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=loading_embed, ephemeral=True)

            # 獲取歌曲資訊（添加超時處理）
            try:
                song_info = await asyncio.wait_for(
                    self.fetch_song_with_retry(query), 
                    timeout=45.0  # 30秒超時
                )
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="⏰ 搜尋超時",
                    description="搜尋歌曲時發生超時，請稍後再試",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="可能原因",
                    value="• 網路連線不穩定\n• YouTube服務繁忙\n• 搜尋關鍵字太複雜",
                    inline=False
                )
                embed.add_field(
                    name="建議",
                    value="• 嘗試使用更簡單的關鍵字\n• 直接使用YouTube連結\n• 稍後再試",
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            except Exception as e:
                logger.error(f"[play] 搜尋歌曲失敗: {e}")
                embed = discord.Embed(
                    title="❌ 搜尋失敗",
                    description="搜尋歌曲時發生錯誤",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="錯誤詳情",
                    value=str(e)[:100] + "..." if len(str(e)) > 100 else str(e),
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            if not song_info:
                embed = discord.Embed(
                    title="❌ 無法獲取歌曲資訊",
                    description="請檢查以下項目：",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="可能的原因",
                    value="• 連結無效或已失效\n• 搜尋關鍵字太模糊\n• 網路連線問題\n• YouTube服務暫時無法使用",
                    inline=False
                )
                embed.add_field(
                    name="建議",
                    value="• 嘗試使用更明確的關鍵字\n• 檢查網路連線\n• 稍後再試",
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            url = song_info['url']
            title = song_info.get('title', '未知標題')
            player.add({"url": url, "title": title})

            if not vc.is_playing() and not vc.is_paused():
                # 開始播放
                try:
                    await self.play_next(vc, interaction.guild.id, interaction)
                except Exception as e:
                    logger.error(f"[play] 播放失敗: {e}")
                    embed = discord.Embed(
                        title="❌ 播放失敗",
                        description="開始播放時發生錯誤",
                        color=discord.Color.red()
                    )
                    embed.add_field(
                        name="錯誤詳情",
                        value=str(e)[:100] + "..." if len(str(e)) > 100 else str(e),
                        inline=False
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                # 加入佇列
                embed = discord.Embed(
                    title="✅ 已加入佇列",
                    description=f"**{title}**",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="佇列位置",
                    value=f"第 {len(player.queue)} 首",
                    inline=True
                )
                embed.add_field(
                    name="預估等待時間",
                    value=f"約 {len(player.queue) * 3} 分鐘",
                    inline=True
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except discord.NotFound:
            # 互動已失效
            logger.warning(f"[play] 互動已失效，用戶: {interaction.user.name}")
        except discord.Forbidden:
            logger.error(f"[play] 權限不足: {interaction.guild.name}")
        except Exception as e:
            logger.error(f"[play] 播放命令失敗: {e}")
            try:
                embed = discord.Embed(
                    title="❌ 執行錯誤",
                    description="播放命令執行時發生未預期的錯誤",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="錯誤詳情",
                    value=str(e)[:100] + "..." if len(str(e)) > 100 else str(e),
                    inline=False
                )
                embed.add_field(
                    name="建議",
                    value="• 檢查網路連線\n• 確認語音頻道權限\n• 稍後再試",
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            except:
                # 如果連錯誤訊息都無法發送，記錄到日誌
                logger.error(f"[play] 無法發送錯誤訊息: {e}")

    @app_commands.command(name="volume", description="設定音量 (1-100)")
    @app_commands.describe(level="音量等級")
    async def volume(self, interaction: discord.Interaction, level: int):
        try:
            if not 1 <= level <= 100:
                embed = discord.Embed(
                    title="❌ 音量設定錯誤",
                    description="音量必須在 1-100 之間",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="正確用法",
                    value="`/volume 50` - 設定音量為50%",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            vc = interaction.guild.voice_client
            if not vc or not vc.is_connected():
                await interaction.response.send_message("❌ 機器人未連接到語音頻道", ephemeral=True)
                return
                
            if not vc.source:
                await interaction.response.send_message("❌ 目前沒有播放中的音樂", ephemeral=True)
                return

            player = self.get_player(interaction.guild.id)
            player.volume = level / 100
            if vc.source:
                vc.source.volume = player.volume

            embed = discord.Embed(
                title="🔊 音量已調整",
                description=f"音量設定為 **{level}%**",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"[volume] 音量設定失敗: {e}")
            await interaction.response.send_message(f"❌ 音量設定失敗：{str(e)}", ephemeral=True)

    @app_commands.command(name="pause", description="暫停播放")
    async def pause(self, interaction: discord.Interaction):
        try:
            vc = interaction.guild.voice_client
            if not vc or not vc.is_connected():
                await interaction.response.send_message("❌ 機器人未連接到語音頻道", ephemeral=True)
                return
                
            if not vc.is_playing():
                await interaction.response.send_message("❌ 目前沒有播放中的音樂", ephemeral=True)
                return
                
            vc.pause()
            player = self.get_player(interaction.guild.id)
            player.is_paused = True
            
            embed = discord.Embed(
                title="⏸ 已暫停播放",
                description="使用 `/resume` 繼續播放",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"[pause] 暫停播放失敗: {e}")
            await interaction.response.send_message(f"❌ 暫停播放失敗：{str(e)}", ephemeral=True)

    @app_commands.command(name="resume", description="繼續播放")
    async def resume(self, interaction: discord.Interaction):
        try:
            vc = interaction.guild.voice_client
            if not vc or not vc.is_connected():
                await interaction.response.send_message("❌ 機器人未連接到語音頻道", ephemeral=True)
                return
                
            if not vc.is_paused():
                await interaction.response.send_message("❌ 目前沒有暫停中的音樂", ephemeral=True)
                return
                
            vc.resume()
            player = self.get_player(interaction.guild.id)
            player.is_paused = False
            
            embed = discord.Embed(
                title="▶️ 已繼續播放",
                description="音樂已恢復播放",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"[resume] 繼續播放失敗: {e}")
            await interaction.response.send_message(f"❌ 繼續播放失敗：{str(e)}", ephemeral=True)

    @app_commands.command(name="skip", description="跳到下一首")
    async def skip(self, interaction: discord.Interaction):
        try:
            vc = interaction.guild.voice_client
            if not vc or not vc.is_connected():
                await interaction.response.send_message("❌ 機器人未連接到語音頻道", ephemeral=True)
                return
                
            if not vc.is_playing() and not vc.is_paused():
                await interaction.response.send_message("❌ 目前沒有播放中的音樂", ephemeral=True)
                return

            player = self.get_player(interaction.guild.id)
            player.repeat = False  # 關閉重複播放，避免跳過無效
            player.retry_count = 0  # 重置重試計數
            vc.stop()
            
            embed = discord.Embed(
                title="⏭ 已跳到下一首",
                description="正在播放下一首歌曲",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"[skip] 跳過歌曲失敗: {e}")
            await interaction.response.send_message(f"❌ 跳過歌曲失敗：{str(e)}", ephemeral=True)

    @app_commands.command(name="repeat", description="切換重複播放")
    async def repeat(self, interaction: discord.Interaction):
        try:
            player = self.get_player(interaction.guild.id)
            player.repeat = not player.repeat
            status = "開啟" if player.repeat else "關閉"
            
            embed = discord.Embed(
                title="🔁 重複播放設定",
                description=f"重複播放已**{status}**",
                color=discord.Color.green() if player.repeat else discord.Color.light_gray()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"[repeat] 切換重複播放失敗: {e}")
            await interaction.response.send_message(f"❌ 切換重複播放失敗：{str(e)}", ephemeral=True)

    @app_commands.command(name="queue", description="顯示播放隊列")
    async def queue(self, interaction: discord.Interaction):
        player = self.get_player(interaction.guild.id)
        
        if not player.current and not player.queue:
            await interaction.response.send_message("❌ 目前沒有播放隊列。", ephemeral=True)
            return
            
        embed = discord.Embed(title="🎵 播放隊列", color=discord.Color.blue())
        
        if player.current:
            embed.add_field(name="▶️ 正在播放", value=player.current['title'], inline=False)
            
        if player.queue:
            queue_text = ""
            for i, song in enumerate(player.queue[:10], 1):  # 只顯示前10首
                queue_text += f"{i}. {song['title']}\n"
            if len(player.queue) > 10:
                queue_text += f"... 還有 {len(player.queue) - 10} 首"
            embed.add_field(name="📋 等待中", value=queue_text, inline=False)
            
        embed.add_field(name="🔁 重複播放", value="開啟" if player.repeat else "關閉", inline=True)
        embed.add_field(name="🔊 音量", value=f"{int(player.volume * 100)}%", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="clear", description="清空播放隊列")
    async def clear(self, interaction: discord.Interaction):
        player = self.get_player(interaction.guild.id)
        player.clear_queue()
        await interaction.response.send_message("🗑️ 播放隊列已清空。", ephemeral=True)

    @app_commands.command(name="autoplay", description="設定自動串流類別並立即加入歌曲")
    @app_commands.choices(category=[
        app_commands.Choice(name="不設定（關閉自動串流）", value="off"),
        app_commands.Choice(name="日文流行", value="日文流行"),
        app_commands.Choice(name="英文流行", value="英文流行"),
        app_commands.Choice(name="中文流行", value="中文流行"),
    ])
    async def autoplay(self, interaction: discord.Interaction, category: app_commands.Choice[str]):
        await interaction.response.defer()
        player = self.get_player(interaction.guild.id)

        if category.value == "off":
            player.autoplay = False
            player.category = None
            await interaction.followup.send("❌ 已關閉自動串流功能。")
            return

        player.autoplay = True
        player.category = category.value

        # 確保語音連接
        vc = await self.ensure_voice_connection(interaction)
        if not vc:
            return

        # 直接抓一首該類別歌加入佇列並播放（如果沒在播）
        keywords = self.category_keywords.get(category.value)
        song = None
        if keywords:
            keyword = random.choice(keywords)
            song = await self.fetch_song_with_retry(keyword)
        if song:
            player.add({"url": song['url'], "title": song['title']})
            if not vc.is_playing() and not vc.is_paused():
                await self.play_next(vc, interaction.guild.id)
            await interaction.followup.send(f"▶️ 自動串流已啟動，並加入歌曲：{song['title']}")
        else:
            await interaction.followup.send("❌ 找不到符合類別的歌曲。")

    @app_commands.command(name="join", description="讓機器人加入你所在的語音頻道")
    async def join(self, interaction: discord.Interaction):
        vc = await self.ensure_voice_connection(interaction)
        if vc:
            await interaction.response.send_message(f"✅ 機器人已加入語音頻道：{vc.channel.name}", ephemeral=True)

    @app_commands.command(name="leave", description="讓機器人離開語音頻道")
    async def leave(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("❌ 機器人不在語音頻道中。", ephemeral=True)
            return
        await vc.disconnect()
        guild_id = interaction.guild.id
        if guild_id in self.players:
            self.players.pop(guild_id)
        if guild_id in self.connection_retries:
            self.connection_retries.pop(guild_id)
        await interaction.response.send_message("👋 已離開語音頻道。", ephemeral=True)

    @app_commands.command(name="nowplaying", description="顯示目前正在播放的音樂")
    async def nowplaying(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_playing():
            await interaction.response.send_message("❌ 沒有正在播放的音樂。", ephemeral=True)
            return

        player = self.get_player(interaction.guild.id)
        song = player.current
        if not song:
            await interaction.response.send_message("❌ 找不到目前播放的音樂資訊。", ephemeral=True)
        else:
            embed = discord.Embed(title="🎶 現正播放", color=discord.Color.green())
            embed.add_field(name="歌曲", value=song['title'], inline=False)
            embed.add_field(name="音量", value=f"{int(player.volume * 100)}%", inline=True)
            embed.add_field(name="重複播放", value="開啟" if player.repeat else "關閉", inline=True)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="reset", description="重置音樂系統狀態（管理員限定）")
    @app_commands.checks.has_permissions(administrator=True)
    async def reset(self, interaction: discord.Interaction):
        """重置音樂系統狀態，清理快取和連接記錄"""
        guild_id = interaction.guild.id
        
        # 清理快取
        self.song_cache.cache.clear()
        self.song_cache.save_cache()
        
        # 清理連接重試記錄
        if guild_id in self.connection_retries:
            self.connection_retries.pop(guild_id)
        
        # 重置播放器
        if guild_id in self.players:
            player = self.players[guild_id]
            player.retry_count = 0
            player.clear_queue()
        
        await interaction.response.send_message("🔄 音樂系統狀態已重置，快取已清理。", ephemeral=True)

    @reset.error
    async def reset_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ 你沒有權限使用這個指令！", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ 重置失敗: {error}", ephemeral=True)

    @app_commands.command(name="status", description="顯示音樂系統狀態")
    async def status(self, interaction: discord.Interaction):
        """顯示音樂系統的詳細狀態"""
        guild_id = interaction.guild.id
        player = self.get_player(guild_id)
        vc = interaction.guild.voice_client
        
        embed = discord.Embed(title="🎵 音樂系統狀態", color=discord.Color.blue())
        
        # 連接狀態
        if vc and vc.is_connected():
            embed.add_field(name="🔗 語音連接", value=f"✅ 已連接至 {vc.channel.name}", inline=False)
        else:
            embed.add_field(name="🔗 語音連接", value="❌ 未連接", inline=False)
        
        # 播放狀態
        if vc and vc.is_playing():
            embed.add_field(name="▶️ 播放狀態", value="正在播放", inline=True)
        elif vc and vc.is_paused():
            embed.add_field(name="▶️ 播放狀態", value="已暫停", inline=True)
        else:
            embed.add_field(name="▶️ 播放狀態", value="未播放", inline=True)
        
        # 播放器資訊
        embed.add_field(name="📋 佇列長度", value=str(len(player.queue)), inline=True)
        embed.add_field(name="🔁 重複播放", value="開啟" if player.repeat else "關閉", inline=True)
        embed.add_field(name="🔄 重試次數", value=str(player.retry_count), inline=True)
        
        # 自動串流
        if player.autoplay:
            embed.add_field(name="🎵 自動串流", value=f"開啟 ({player.category})", inline=True)
        else:
            embed.add_field(name="🎵 自動串流", value="關閉", inline=True)
        
        # 快取狀態
        cache_size = len(self.song_cache.cache)
        embed.add_field(name="💾 快取大小", value=f"{cache_size} 首歌曲", inline=True)
        
        # 連接重試狀態
        retry_count = self.connection_retries.get(guild_id, 0)
        embed.add_field(name="🔄 連接重試", value=str(retry_count), inline=True)
        
        # FFmpeg 配置狀態
        ffmpeg_executable = self.ffmpeg_config.get('ffmpeg_path', 'ffmpeg')
        embed.add_field(name="🎬 FFmpeg", value=ffmpeg_executable, inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="reload_ffmpeg", description="重新載入 FFmpeg 配置（管理員限定）")
    @app_commands.checks.has_permissions(administrator=True)
    async def reload_ffmpeg(self, interaction: discord.Interaction):
        """重新載入 FFmpeg 配置檔案"""
        try:
            old_config = self.ffmpeg_config.copy()
            self.ffmpeg_config = self.load_ffmpeg_config()
            
            embed = discord.Embed(title="🔄 FFmpeg 配置已重新載入", color=discord.Color.green())
            embed.add_field(name="執行檔", value=self.ffmpeg_config.get('ffmpeg_path', 'ffmpeg'), inline=True)
            embed.add_field(name="選項", value=self.ffmpeg_config.get('ffmpeg_options', {}).get('before_options', '預設選項')[:50] + "...", inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ 重新載入 FFmpeg 配置失敗: {e}", ephemeral=True)

    @reload_ffmpeg.error
    async def reload_ffmpeg_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ 你沒有權限使用這個指令！", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ 重新載入失敗: {error}", ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """監聽語音狀態變化"""
        try:
            # 只處理 Bot 的語音狀態變化
            if member.id != self.bot.user.id:
                return
                
            guild_id = member.guild.id
            
            # Bot 被踢出或離開語音頻道
            if before.channel and not after.channel:
                logger.info(f"[on_voice_state_update] Bot 離開語音頻道: {before.channel.name}")
                
                # 清理播放器
                if guild_id in self.players:
                    player = self.players[guild_id]
                    player.queue.clear()
                    player.current = None
                    player.is_paused = False
                    player.repeat = False
                    
                # 重置重連計數
                self.reconnect_attempts[guild_id] = 0
                
            # Bot 加入語音頻道
            elif not before.channel and after.channel:
                logger.info(f"[on_voice_state_update] Bot 加入語音頻道: {after.channel.name}")
                
                # 重置重連計數
                self.reconnect_attempts[guild_id] = 0
                
            # Bot 移動到不同頻道
            elif before.channel and after.channel and before.channel != after.channel:
                logger.info(f"[on_voice_state_update] Bot 移動到頻道: {after.channel.name}")
                
        except Exception as e:
            logger.error(f"[on_voice_state_update] 處理語音狀態變化失敗: {e}")

    @commands.Cog.listener()
    async def on_voice_client_disconnect(self, voice_client):
        """處理語音客戶端斷線"""
        try:
            guild_id = voice_client.guild.id
            logger.warning(f"[on_voice_client_disconnect] 語音客戶端斷線: {voice_client.guild.name}")
            
            # 檢查是否需要重連
            if guild_id in self.reconnect_attempts:
                attempts = self.reconnect_attempts[guild_id]
                if attempts < self.max_reconnect_attempts:
                    self.reconnect_attempts[guild_id] = attempts + 1
                    logger.info(f"[on_voice_client_disconnect] 嘗試重連 {attempts + 1}/{self.max_reconnect_attempts}")
                    
                    # 延遲重連
                    await asyncio.sleep(self.reconnect_delay)
                    
                    try:
                        # 嘗試重新連接
                        if voice_client.channel:
                            await voice_client.connect(timeout=45.0, self_deaf=True)
                            logger.info(f"[on_voice_client_disconnect] 重連成功: {voice_client.guild.name}")
                            
                            # 重置重連計數
                            self.reconnect_attempts[guild_id] = 0
                            
                            # 恢復播放
                            if guild_id in self.players:
                                player = self.players[guild_id]
                                if player.current and not voice_client.is_playing():
                                    await self.play_next(voice_client, guild_id)
                                    
                    except Exception as e:
                        logger.error(f"[on_voice_client_disconnect] 重連失敗: {e}")
                        if attempts + 1 >= self.max_reconnect_attempts:
                            logger.error(f"[on_voice_client_disconnect] 重連次數已達上限，停止重連: {voice_client.guild.name}")
                            
                            # 清理播放器
                            if guild_id in self.players:
                                player = self.players[guild_id]
                                player.queue.clear()
                                player.current = None
                                
                            # 發送通知到伺服器
                            try:
                                # 尋找系統頻道或第一個文字頻道
                                system_channel = voice_client.guild.system_channel
                                if not system_channel:
                                    text_channels = [c for c in voice_client.guild.text_channels if c.permissions_for(voice_client.guild.me).send_messages]
                                    if text_channels:
                                        system_channel = text_channels[0]
                                
                                if system_channel:
                                    embed = discord.Embed(
                                        title="🔌 語音連線中斷",
                                        description="Bot 語音連線已中斷，無法自動重連",
                                        color=discord.Color.red()
                                    )
                                    embed.add_field(
                                        name="原因",
                                        value="• 網路連線不穩定\n• Discord服務問題\n• 重連次數已達上限",
                                        inline=False
                                    )
                                    embed.add_field(
                                        name="解決方法",
                                        value="請重新使用 `/join` 命令加入語音頻道",
                                        inline=False
                                    )
                                    await system_channel.send(embed=embed)
                                    
                            except Exception as notify_error:
                                logger.error(f"[on_voice_client_disconnect] 發送通知失敗: {notify_error}")
                                
        except Exception as e:
            logger.error(f"[on_voice_client_disconnect] 處理斷線失敗: {e}")

    async def periodic_cleanup(self):
        """定期清理任務"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分鐘執行一次
                
                # 清理無效的語音連線
                for guild in self.bot.guilds:
                    if guild.voice_client and not guild.voice_client.is_connected():
                        try:
                            await guild.voice_client.disconnect()
                            logger.info(f"[periodic_cleanup] 清理無效語音連線: {guild.name}")
                        except:
                            pass
                
                # 清理過期的重連計數（超過1小時沒有活動的伺服器）
                current_time = time.time()
                expired_guilds = []
                for guild_id in list(self.reconnect_attempts.keys()):
                    # 檢查伺服器是否還存在
                    if not any(guild.id == guild_id for guild in self.bot.guilds):
                        expired_guilds.append(guild_id)
                
                for guild_id in expired_guilds:
                    del self.reconnect_attempts[guild_id]
                    
            except Exception as e:
                logger.error(f"[periodic_cleanup] 定期清理失敗: {e}")
                await asyncio.sleep(60)  # 發生錯誤時等待1分鐘再試

    def save_ffmpeg_config(self, config=None):
        """保存 FFmpeg 配置"""
        if config is None:
            config = self.load_ffmpeg_config()
        try:
            with open('ffmpeg_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info("[Music] FFmpeg 配置保存成功")
        except Exception as e:
            logger.error(f"[Music] 保存 FFmpeg 配置失敗: {e}")

    def get_default_ffmpeg_config(self):
        """取得預設 FFmpeg 配置"""
        return {
            "ffmpeg_path": "ffmpeg",
            "ffmpeg_options": {
                "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                "options": "-vn -b:a 128k -bufsize 3072k"
            }
        }

    async def _start_cleanup_task(self):
        """啟動定期清理任務"""
        if not self._cleanup_task_started:
            self._cleanup_task_started = True
            # 直接創建任務，不需要訪問 loop
            asyncio.create_task(self.periodic_cleanup())
            logger.info("[Music] 定期清理任務已啟動")

async def setup(bot):
    cog = Music(bot)
    await bot.add_cog(cog)
    # 啟動定期清理任務
    await cog._start_cleanup_task()