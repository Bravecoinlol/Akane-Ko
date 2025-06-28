import discord
from discord.ext import commands
from discord import app_commands
import json
import time
import asyncio
import logging
import re
from collections import defaultdict, deque

# 設定 logger
logger = logging.getLogger('AntiRaid')

class AntiRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = 'antiraid_config.json'
        self.config = self.load_config()
        self.user_joins = defaultdict(list)  # 用戶加入時間記錄
        self.message_history = defaultdict(lambda: deque(maxlen=50))  # 訊息歷史
        self.spam_detection = defaultdict(lambda: {'count': 0, 'last_reset': time.time()})
        self.profanity_cache = set()  # 快取髒話列表
        self.scam_patterns = [
            r'free.*nitro',
            r'steam.*gift',
            r'roblox.*robux',
            r'free.*robux',
            r'steam.*free',
            r'nitro.*free',
            r'gift.*card',
            r'click.*here',
            r'verify.*account',
            r'claim.*reward',
            r'free.*money',
            r'earn.*money',
            r'work.*from.*home',
            r'bitcoin.*mining',
            r'crypto.*mining',
            r'free.*v.*bucks',
            r'fortnite.*free',
            r'free.*skins',
            r'free.*coins',
            r'free.*gems'
        ]
        self.load_profanity_words()
        logger.info("[AntiRaid] 反惡意系統已啟動")

    def load_config(self):
        """載入配置檔案"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info("[AntiRaid] 配置檔案載入成功")
                return config
        except FileNotFoundError:
            logger.warning("[AntiRaid] 配置檔案不存在，使用預設配置")
            config = {
                "enabled": True,
                "raid_threshold": 5,  # 5秒內5人加入
                "raid_time_window": 5,
                "mute_duration": 300,  # 5分鐘
                "spam_threshold": 5,  # 5秒內5條訊息
                "spam_time_window": 5,
                "profanity_enabled": True,
                "profanity_mute_duration": 600,  # 10分鐘
                "scam_detection_enabled": True,
                "scam_mute_duration": 1800,  # 30分鐘
                "auto_delete_spam": True,
                "log_channel_id": None,
                "admin_role_id": None,
                "default_profanity_words": [
                    "fuck", "shit", "bitch", "asshole", "dick", "pussy", "cock", "cunt",
                    "motherfucker", "fucker", "bastard", "whore", "slut", "nigger", "nigga",
                    "faggot", "fag", "dyke", "retard", "idiot", "stupid", "dumb", "moron"
                ]
            }
            self.save_config(config)
            return config
        except Exception as e:
            logger.error(f"[AntiRaid] 載入配置檔案失敗: {e}")
            return self.get_default_config()

    def get_default_config(self):
        """取得預設配置"""
        return {
            "enabled": True,
            "raid_threshold": 5,
            "raid_time_window": 5,
            "mute_duration": 300,
            "spam_threshold": 5,
            "spam_time_window": 5,
            "profanity_enabled": True,
            "profanity_mute_duration": 600,
            "scam_detection_enabled": True,
            "scam_mute_duration": 1800,
            "auto_delete_spam": True,
            "log_channel_id": None,
            "admin_role_id": None,
            "default_profanity_words": [
                "fuck", "shit", "bitch", "asshole", "dick", "pussy", "cock", "cunt",
                "motherfucker", "fucker", "bastard", "whore", "slut", "nigger", "nigga",
                "faggot", "fag", "dyke", "retard", "idiot", "stupid", "dumb", "moron"
            ]
        }

    def save_config(self, config=None):
        """保存配置檔案"""
        if config is None:
            config = self.config
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info("[AntiRaid] 配置檔案保存成功")
        except Exception as e:
            logger.error(f"[AntiRaid] 保存配置檔案失敗: {e}")

    def load_profanity_words(self):
        """載入髒話列表"""
        try:
            self.profanity_cache = set(self.config.get('profanity_words', self.config.get('default_profanity_words', [])))
            logger.debug(f"[AntiRaid] 載入 {len(self.profanity_cache)} 個髒話詞彙")
        except Exception as e:
            logger.error(f"[AntiRaid] 載入髒話列表失敗: {e}")
            self.profanity_cache = set()

    async def log_action(self, action, user, reason, duration=None):
        """記錄反惡意行動"""
        if not self.config.get('log_channel_id'):
            return
        
        try:
            log_channel = self.bot.get_channel(self.config['log_channel_id'])
            if log_channel:
                embed = discord.Embed(
                    title="🛡️ 反惡意系統行動",
                    description=f"**行動**: {action}\n**用戶**: {user.mention} ({user.id})\n**原因**: {reason}",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                if duration:
                    embed.add_field(name="⏱️ 持續時間", value=f"{duration} 秒", inline=True)
                embed.set_footer(text=f"用戶: {user.name}")
                await log_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"[AntiRaid] 記錄行動失敗: {e}")

    def is_admin(self, member):
        """檢查是否為管理員"""
        if not self.config.get('admin_role_id'):
            return member.guild_permissions.administrator
        return member.guild_permissions.administrator or any(role.id == self.config['admin_role_id'] for role in member.roles)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """監聽成員加入事件"""
        if not self.config.get('enabled', True):
            return
        
        guild_id = member.guild.id
        current_time = time.time()
        
        # 記錄用戶加入時間
        self.user_joins[guild_id].append(current_time)
        
        # 清理舊記錄（超過時間窗口）
        window = self.config.get('raid_time_window', 5)
        self.user_joins[guild_id] = [t for t in self.user_joins[guild_id] if current_time - t <= window]
        
        # 檢查是否達到惡意加入閾值
        threshold = self.config.get('raid_threshold', 5)
        if len(self.user_joins[guild_id]) >= threshold:
            logger.warning(f"[AntiRaid] 檢測到惡意加入行為！{len(self.user_joins[guild_id])} 人在 {window} 秒內加入")
            
            # 暫時關閉邀請
            try:
                invites = await member.guild.invites()
                for invite in invites:
                    await invite.delete(reason="反惡意系統：檢測到惡意加入行為")
                logger.info("[AntiRaid] 已刪除所有邀請連結")
            except Exception as e:
                logger.error(f"[AntiRaid] 刪除邀請連結失敗: {e}")
            
            # 記錄行動
            await self.log_action("惡意加入防護", member, f"{len(self.user_joins[guild_id])} 人在 {window} 秒內加入")

    @commands.Cog.listener()
    async def on_message(self, message):
        """監聽訊息事件"""
        if not self.config.get('enabled', True) or message.author.bot:
            return
        
        # 檢查管理員權限
        if self.is_admin(message.author):
            return
        
        user_id = message.author.id
        current_time = time.time()
        
        # 垃圾訊息檢測
        if self.config.get('spam_threshold'):
            spam_data = self.spam_detection[user_id]
            
            # 重置計數器（如果超過時間窗口）
            window = self.config.get('spam_time_window', 5)
            if current_time - spam_data['last_reset'] > window:
                spam_data['count'] = 0
                spam_data['last_reset'] = current_time
            
            spam_data['count'] += 1
            threshold = self.config.get('spam_threshold', 5)
            
            if spam_data['count'] >= threshold:
                logger.warning(f"[AntiRaid] 檢測到垃圾訊息行為！用戶 {message.author.name} 在 {window} 秒內發送 {spam_data['count']} 條訊息")
                
                # 刪除訊息
                try:
                    await message.delete()
                except:
                    pass
                
                # 禁言用戶
                duration = self.config.get('mute_duration', 300)
                try:
                    await message.author.timeout(duration=discord.utils.utcnow() + discord.utils.utcnow().replace(second=duration), reason="反惡意系統：垃圾訊息")
                    await self.log_action("垃圾訊息禁言", message.author, f"在 {window} 秒內發送 {spam_data['count']} 條訊息", duration)
                except Exception as e:
                    logger.error(f"[AntiRaid] 禁言用戶失敗: {e}")
                
                spam_data['count'] = 0
        
        # 髒話檢測
        if self.config.get('profanity_enabled', True):
            content_lower = message.content.lower()
            found_profanity = []
            
            for word in self.profanity_cache:
                if word.lower() in content_lower:
                    found_profanity.append(word)
            
            if found_profanity:
                logger.warning(f"[AntiRaid] 檢測到髒話！用戶 {message.author.name} 使用了: {', '.join(found_profanity)}")
                
                # 刪除訊息
                try:
                    await message.delete()
                except:
                    pass
                
                # 禁言用戶（更長時間）
                duration = self.config.get('profanity_mute_duration', 600)
                try:
                    await message.author.timeout(duration=discord.utils.utcnow() + discord.utils.utcnow().replace(second=duration), reason="反惡意系統：使用髒話")
                    await self.log_action("髒話禁言", message.author, f"使用了髒話: {', '.join(found_profanity)}", duration)
                except Exception as e:
                    logger.error(f"[AntiRaid] 禁言用戶失敗: {e}")
        
        # 詐騙檢測
        if self.config.get('scam_detection_enabled', True):
            content_lower = message.content.lower()
            found_scam = []
            
            for pattern in self.scam_patterns:
                if re.search(pattern, content_lower):
                    found_scam.append(pattern)
            
            if found_scam:
                logger.warning(f"[AntiRaid] 檢測到詐騙訊息！用戶 {message.author.name} 觸發模式: {', '.join(found_scam)}")
                
                # 刪除訊息
                try:
                    await message.delete()
                except:
                    pass
                
                # 禁言用戶（最長時間）
                duration = self.config.get('scam_mute_duration', 1800)
                try:
                    await message.author.timeout(duration=discord.utils.utcnow() + discord.utils.utcnow().replace(second=duration), reason="反惡意系統：詐騙訊息")
                    await self.log_action("詐騙禁言", message.author, f"觸發詐騙模式: {', '.join(found_scam)}", duration)
                except Exception as e:
                    logger.error(f"[AntiRaid] 禁言用戶失敗: {e}")

    # 管理命令
    @app_commands.command(name="antiraid", description="管理反惡意系統")
    @app_commands.describe(
        action="操作類型",
        setting="設定值"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="狀態", value="status"),
        app_commands.Choice(name="開啟", value="enable"),
        app_commands.Choice(name="關閉", value="disable"),
        app_commands.Choice(name="設定閾值", value="threshold"),
        app_commands.Choice(name="設定禁言時間", value="mute_duration"),
        app_commands.Choice(name="設定記錄頻道", value="log_channel"),
        app_commands.Choice(name="設定管理員角色", value="admin_role"),
        app_commands.Choice(name="重載配置", value="reload")
    ])
    async def antiraid_command(self, interaction: discord.Interaction, action: str, setting: str = None):
        """反惡意系統管理命令"""
        # 檢查管理員權限
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ 您沒有權限使用此命令", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            if action == "status":
                embed = discord.Embed(
                    title="🛡️ 反惡意系統狀態",
                    color=discord.Color.blue()
                )
                embed.add_field(name="系統狀態", value="✅ 開啟" if self.config.get('enabled', True) else "❌ 關閉", inline=True)
                embed.add_field(name="惡意加入閾值", value=f"{self.config.get('raid_threshold', 5)} 人/{self.config.get('raid_time_window', 5)} 秒", inline=True)
                embed.add_field(name="垃圾訊息閾值", value=f"{self.config.get('spam_threshold', 5)} 條/{self.config.get('spam_time_window', 5)} 秒", inline=True)
                embed.add_field(name="禁言時間", value=f"{self.config.get('mute_duration', 300)} 秒", inline=True)
                embed.add_field(name="髒話檢測", value="✅ 開啟" if self.config.get('profanity_enabled', True) else "❌ 關閉", inline=True)
                embed.add_field(name="詐騙檢測", value="✅ 開啟" if self.config.get('scam_detection_enabled', True) else "❌ 關閉", inline=True)
                
                log_channel = self.bot.get_channel(self.config.get('log_channel_id')) if self.config.get('log_channel_id') else None
                embed.add_field(name="記錄頻道", value=log_channel.mention if log_channel else "未設定", inline=True)
                
                await interaction.followup.send(embed=embed)
                
            elif action == "enable":
                self.config['enabled'] = True
                self.save_config()
                logger.info("[AntiRaid] 反惡意系統已開啟")
                await interaction.followup.send("✅ 反惡意系統已開啟")
                
            elif action == "disable":
                self.config['enabled'] = False
                self.save_config()
                logger.info("[AntiRaid] 反惡意系統已關閉")
                await interaction.followup.send("❌ 反惡意系統已關閉")
                
            elif action == "threshold" and setting:
                try:
                    threshold = int(setting)
                    if threshold < 1:
                        await interaction.followup.send("❌ 閾值必須大於 0")
                        return
                    self.config['raid_threshold'] = threshold
                    self.save_config()
                    logger.info(f"[AntiRaid] 惡意加入閾值已設定為 {threshold}")
                    await interaction.followup.send(f"✅ 惡意加入閾值已設定為 {threshold}")
                except ValueError:
                    await interaction.followup.send("❌ 請輸入有效的數字")
                    
            elif action == "mute_duration" and setting:
                try:
                    duration = int(setting)
                    if duration < 1:
                        await interaction.followup.send("❌ 禁言時間必須大於 0")
                        return
                    self.config['mute_duration'] = duration
                    self.save_config()
                    logger.info(f"[AntiRaid] 禁言時間已設定為 {duration} 秒")
                    await interaction.followup.send(f"✅ 禁言時間已設定為 {duration} 秒")
                except ValueError:
                    await interaction.followup.send("❌ 請輸入有效的數字")
                    
            elif action == "log_channel":
                self.config['log_channel_id'] = interaction.channel.id
                self.save_config()
                logger.info(f"[AntiRaid] 記錄頻道已設定為 {interaction.channel.name}")
                await interaction.followup.send(f"✅ 記錄頻道已設定為 {interaction.channel.mention}")
                
            elif action == "admin_role" and setting:
                try:
                    role_id = int(setting)
                    role = interaction.guild.get_role(role_id)
                    if not role:
                        await interaction.followup.send("❌ 找不到指定的角色")
                        return
                    self.config['admin_role_id'] = role_id
                    self.save_config()
                    logger.info(f"[AntiRaid] 管理員角色已設定為 {role.name}")
                    await interaction.followup.send(f"✅ 管理員角色已設定為 {role.mention}")
                except ValueError:
                    await interaction.followup.send("❌ 請輸入有效的角色 ID")
                    
            elif action == "reload":
                self.config = self.load_config()
                self.load_profanity_words()
                logger.info("[AntiRaid] 配置已重新載入")
                await interaction.followup.send("✅ 配置已重新載入")
                
            else:
                await interaction.followup.send("❌ 無效的操作或缺少參數")
                
        except Exception as e:
            logger.error(f"[AntiRaid] 命令執行失敗: {e}")
            await interaction.followup.send(f"❌ 執行命令時發生錯誤: {e}")

    @app_commands.command(name="profanity", description="管理髒話列表")
    @app_commands.describe(
        action="操作類型",
        word="髒話詞彙"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="列表", value="list"),
        app_commands.Choice(name="新增", value="add"),
        app_commands.Choice(name="移除", value="remove"),
        app_commands.Choice(name="重設", value="reset")
    ])
    async def profanity_command(self, interaction: discord.Interaction, action: str, word: str = None):
        """髒話列表管理命令"""
        # 檢查管理員權限
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("❌ 您沒有權限使用此命令", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            if action == "list":
                words = list(self.profanity_cache)
                if not words:
                    await interaction.followup.send("📝 髒話列表為空")
                    return
                
                # 分頁顯示
                words_per_page = 20
                pages = [words[i:i + words_per_page] for i in range(0, len(words), words_per_page)]
                
                embed = discord.Embed(
                    title="📝 髒話列表",
                    description=f"共 {len(words)} 個詞彙",
                    color=discord.Color.blue()
                )
                
                current_page = pages[0]
                embed.add_field(name="詞彙列表", value="\n".join(current_page), inline=False)
                
                if len(pages) > 1:
                    embed.set_footer(text=f"第 1/{len(pages)} 頁")
                
                await interaction.followup.send(embed=embed)
                
            elif action == "add" and word:
                if word.lower() in self.profanity_cache:
                    await interaction.followup.send("❌ 該詞彙已存在於列表中")
                    return
                
                self.profanity_cache.add(word.lower())
                self.config['profanity_words'] = list(self.profanity_cache)
                self.save_config()
                logger.info(f"[AntiRaid] 新增髒話詞彙: {word}")
                await interaction.followup.send(f"✅ 已新增髒話詞彙: {word}")
                
            elif action == "remove" and word:
                if word.lower() not in self.profanity_cache:
                    await interaction.followup.send("❌ 該詞彙不存在於列表中")
                    return
                
                self.profanity_cache.discard(word.lower())
                self.config['profanity_words'] = list(self.profanity_cache)
                self.save_config()
                logger.info(f"[AntiRaid] 移除髒話詞彙: {word}")
                await interaction.followup.send(f"✅ 已移除髒話詞彙: {word}")
                
            elif action == "reset":
                self.profanity_cache = set(self.config.get('default_profanity_words', []))
                self.config['profanity_words'] = list(self.profanity_cache)
                self.save_config()
                logger.info("[AntiRaid] 髒話列表已重設為預設值")
                await interaction.followup.send("✅ 髒話列表已重設為預設值")
                
            else:
                await interaction.followup.send("❌ 無效的操作或缺少參數")
                
        except Exception as e:
            logger.error(f"[AntiRaid] 髒話命令執行失敗: {e}")
            await interaction.followup.send(f"❌ 執行命令時發生錯誤: {e}")

async def setup(bot):
    await bot.add_cog(AntiRaid(bot))
