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
        if self.repeat and self.current:
            logger.debug(f"[Queue] 重複播放：{self.current['title']}")
            return self.current
        if self.queue:
            self.current = self.queue.popleft()
            logger.debug(f"[Queue] 取出下一首：{self.current['title']}")
            return self.current
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

    @discord.ui.button(label='🔉', style=discord.ButtonStyle.grey)
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

    @discord.ui.button(label='🔊', style=discord.ButtonStyle.grey)
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

    @discord.ui.button(label='🔁', style=discord.ButtonStyle.grey)
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
        self.connection_retries = {}  # 記錄每個伺服器的重連次數
        self.ffmpeg_config = self.load_ffmpeg_config()
        
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
            if os.path.exists('ffmpeg_config.json'):
                with open('ffmpeg_config.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning("[Music] ffmpeg_config.json 不存在，使用預設配置")
                return {
                    "ffmpeg_options": {
                        "primary": {
                            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -fflags +genpts+igndts -avoid_negative_ts make_zero",
                            "options": "-vn -loglevel error"
                        },
                        "backup": {
                            "before_options": "-reconnect 1 -reconnect_streamed 1",
                            "options": "-vn -loglevel error"
                        }
                    },
                    "executable": "ffmpeg",
                    "volume_default": 0.5,
                    "retry_settings": {
                        "max_retries": 3,
                        "retry_delay": 2,
                        "ffmpeg_fallback": True
                    }
                }
        except Exception as e:
            logger.error(f"[Music] 載入 FFmpeg 配置失敗: {e}，使用預設配置")
            return {
                "ffmpeg_options": {
                    "primary": {
                        "before_options": "-reconnect 1 -reconnect_streamed 1",
                        "options": "-vn -loglevel error"
                    },
                    "backup": {
                        "before_options": "-reconnect 1",
                        "options": "-vn -loglevel error"
                    }
                },
                "executable": "ffmpeg",
                "volume_default": 0.5,
                "retry_settings": {
                    "max_retries": 3,
                    "retry_delay": 2,
                    "ffmpeg_fallback": True
                }
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
        """確保語音連接，帶重試機制"""
        guild_id = interaction.guild.id
        vc = interaction.guild.voice_client
        
        if vc and vc.is_connected():
            return vc
            
        if not auto_join:
            return None
            
        if not interaction.user.voice or not interaction.user.voice.channel:
            return None
            
        channel = interaction.user.voice.channel
        retry_count = self.connection_retries.get(guild_id, 0)
        
        if retry_count >= 3:
            await interaction.followup.send("❌ 連接失敗次數過多，請稍後再試。")
            return None
            
        try:
            if vc:
                await vc.move_to(channel)
            else:
                vc = await channel.connect(timeout=20)
            
            self.connection_retries[guild_id] = 0  # 重置重試計數
            return vc
            
        except Exception as e:
            print(f"[ensure_voice_connection] 連接失敗: {e}")
            self.connection_retries[guild_id] = retry_count + 1
            await interaction.followup.send(f"❌ 連接語音頻道失敗: {e}")
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
        ffmpeg_config = self.ffmpeg_config['ffmpeg_options']
        executable = self.ffmpeg_config.get('executable', 'ffmpeg')
        
        try:
            # 嘗試使用主要 FFmpeg 選項
            try:
                source = discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(
                        song['url'],
                        before_options=ffmpeg_config['primary']['before_options'],
                        options=ffmpeg_config['primary']['options'],
                        executable=executable
                    ),
                    volume=player.volume
                )
            except Exception as ffmpeg_error:
                print(f"[play_next] 主要 FFmpeg 選項失敗，使用備用選項: {ffmpeg_error}")
                # 使用備用 FFmpeg 選項
                source = discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(
                        song['url'],
                        before_options=ffmpeg_config['backup']['before_options'],
                        options=ffmpeg_config['backup']['options'],
                        executable=executable
                    ),
                    volume=player.volume
                )
            
            vc.play(source, after=lambda error: asyncio.run_coroutine_threadsafe(
                self.after_playing(error, vc, guild_id), self.bot.loop
            ))
            
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
        await interaction.response.defer()

        try:
            # 檢查查詢字串
            if not query or len(query.strip()) == 0:
                await interaction.followup.send("❌ 請提供有效的連結或搜尋關鍵字", ephemeral=True)
                return
                
            if len(query) > 200:
                await interaction.followup.send("❌ 查詢字串太長，請縮短後再試", ephemeral=True)
                return

            # 確保語音連接
            vc = await self.ensure_voice_connection(interaction)
            if not vc:
                return

            player = self.get_player(interaction.guild.id)
            player.retry_count = 0  # 重置重試計數

            # 獲取歌曲資訊
            song_info = await self.fetch_song_with_retry(query)
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
                await self.play_next(vc, interaction.guild.id, interaction)
            else:
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
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"[play] 播放命令失敗: {e}")
            await interaction.followup.send(f"❌ 播放失敗：{str(e)}", ephemeral=True)

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
                color=discord.Color.green() if player.repeat else discord.Color.grey()
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
        song = await self.fetch_song_with_retry(keywords)
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
        ffmpeg_executable = self.ffmpeg_config.get('executable', 'ffmpeg')
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
            embed.add_field(name="執行檔", value=self.ffmpeg_config.get('executable', 'ffmpeg'), inline=True)
            embed.add_field(name="主要選項", value=self.ffmpeg_config['ffmpeg_options']['primary']['before_options'][:50] + "...", inline=False)
            embed.add_field(name="備用選項", value=self.ffmpeg_config['ffmpeg_options']['backup']['before_options'][:50] + "...", inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ 重新載入 FFmpeg 配置失敗: {e}", ephemeral=True)

    @reload_ffmpeg.error
    async def reload_ffmpeg_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ 你沒有權限使用這個指令！", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ 重新載入失敗: {error}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Music(bot))