import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import typing
from PIL import Image, ImageDraw, ImageFont
import aiohttp
from io import BytesIO
from dotenv import load_dotenv
import asyncio
import logging
import io

# 設定 logger
logger = logging.getLogger('Member')

load_dotenv()
APPLICATION_ID = int(os.getenv("APPLICATION_ID"))

class MemberCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings_path = 'setting.json'
        self.autorole_path = 'autorole_settings.json'
        self.channel_settings = self.load_settings()
        self.autorole_settings = self.load_autorole_settings()

    def load_settings(self):
        try:
            if not os.path.exists(self.settings_path):
                with open(self.settings_path, 'w', encoding='utf8') as f:
                    json.dump({}, f)
            with open(self.settings_path, 'r', encoding='utf8') as f:
                content = f.read().strip()
                return json.loads(content) if content else {}
        except json.JSONDecodeError as e:
            logger.error(f"[Member] 設定檔案格式錯誤: {e}")
            return {}
        except PermissionError:
            logger.error("[Member] 沒有權限讀取設定檔案")
            return {}
        except Exception as e:
            logger.error(f"[Member] 載入設定檔案失敗: {e}")
            return {}

    def load_autorole_settings(self):
        try:
            if not os.path.exists(self.autorole_path):
                with open(self.autorole_path, 'w', encoding='utf8') as f:
                    json.dump({}, f)
            with open(self.autorole_path, 'r', encoding='utf8') as f:
                content = f.read().strip()
                return json.loads(content) if content else {}
        except json.JSONDecodeError as e:
            logger.error(f"[Member] 自動角色設定檔案格式錯誤: {e}")
            return {}
        except PermissionError:
            logger.error("[Member] 沒有權限讀取自動角色設定檔案")
            return {}
        except Exception as e:
            logger.error(f"[Member] 載入自動角色設定檔案失敗: {e}")
            return {}

    def save_settings(self):
        try:
            with open(self.settings_path, 'w', encoding='utf8') as f:
                json.dump(self.channel_settings, f, ensure_ascii=False, indent=4)
        except PermissionError:
            logger.error("[Member] 沒有權限寫入設定檔案")
        except Exception as e:
            logger.error(f"[Member] 保存設定檔案失敗: {e}")

    def save_autorole_settings(self):
        try:
            with open(self.autorole_path, 'w', encoding='utf8') as f:
                json.dump(self.autorole_settings, f, ensure_ascii=False, indent=4)
        except PermissionError:
            logger.error("[Member] 沒有權限寫入自動角色設定檔案")
        except Exception as e:
            logger.error(f"[Member] 保存自動角色設定檔案失敗: {e}")

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        try:
            if isinstance(error, app_commands.errors.MissingPermissions):
                embed = discord.Embed(
                    title="❌ 權限不足",
                    description="您需要管理員權限才能使用此命令",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            elif isinstance(error, app_commands.errors.CommandInvokeError):
                logger.error(f"[Member] 命令執行錯誤: {error.original}")
                embed = discord.Embed(
                    title="❌ 執行錯誤",
                    description="執行命令時發生錯誤，請稍後再試",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                logger.error(f"[Member] 指令錯誤: {error}")
                embed = discord.Embed(
                    title="❌ 未知錯誤",
                    description="發生未知錯誤，請聯繫管理員",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"[Member] 錯誤處理失敗: {e}")

    @app_commands.command(name="setchannel", description="設定歡迎/離開頻道或管理頻道/身分組更新頻道")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(type="選擇頻道用途", channel="指定的頻道")
    @app_commands.choices(type=[
        app_commands.Choice(name="歡迎與離開頻道", value="welcome_leave"),
        app_commands.Choice(name="管理頻道", value="admin"),
        app_commands.Choice(name="身分組更新頻道", value="role_update")
    ])
    async def set_channel(self, interaction: discord.Interaction, type: app_commands.Choice[str], channel: discord.TextChannel):
        try:
            guild_id = str(interaction.guild.id)
            if guild_id not in self.channel_settings:
                self.channel_settings[guild_id] = {}
            self.channel_settings[guild_id][f"{type.value}_channel_id"] = channel.id
            self.save_settings()
            # 顯示正確的中文名稱
            type_display = {
                "welcome_leave": "歡迎與離開頻道",
                "admin": "管理頻道",
                "role_update": "身分組更新頻道"
            }.get(type.value, type.name)
            embed = discord.Embed(
                title="✅ 頻道設定成功",
                description=f"已設定 `{type_display}` 為 {channel.mention}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"[Member] 設定頻道失敗: {e}")
            embed = discord.Embed(
                title="❌ 設定失敗",
                description="設定頻道時發生錯誤，請稍後再試",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="setautorole", description="新增要自動分配的角色")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(role="要加入自動分配清單的角色")
    async def setautorole(self, interaction: discord.Interaction, role: discord.Role):
        try:
            guild_id = str(interaction.guild.id)
            if guild_id not in self.autorole_settings:
                self.autorole_settings[guild_id] = {}

            existing = self.autorole_settings[guild_id].get("autorole", {"enabled": True, "roles": []})
            if role.name not in existing["roles"]:
                existing["roles"].append(role.name)
            else:
                embed = discord.Embed(
                    title="⚠️ 角色已存在",
                    description=f"`{role.name}` 已在自動分配清單中",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            self.autorole_settings[guild_id]["autorole"] = existing
            self.save_autorole_settings()

            embed = discord.Embed(
                title="✅ 角色新增成功",
                description=f"已新增 `{role.name}` 到自動分配角色清單",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"[Member] 新增自動角色失敗: {e}")
            embed = discord.Embed(
                title="❌ 新增失敗",
                description="新增自動角色時發生錯誤，請稍後再試",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="removeautorole", description="從自動分配清單中移除角色")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(role="要移除的角色")
    async def removeautorole(self, interaction: discord.Interaction, role: discord.Role):
        try:
            guild_id = str(interaction.guild.id)
            if guild_id not in self.autorole_settings:
                embed = discord.Embed(
                    title="⚠️ 尚未設定",
                    description="此伺服器尚未設定自動分配角色",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            config = self.autorole_settings[guild_id].get("autorole", {"enabled": True, "roles": []})
            if role.name in config["roles"]:
                config["roles"].remove(role.name)
                self.autorole_settings[guild_id]["autorole"] = config
                self.save_autorole_settings()
                
                embed = discord.Embed(
                    title="✅ 角色移除成功",
                    description=f"已移除 `{role.name}` 從自動分配清單",
                    color=discord.Color.green()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(
                    title="⚠️ 角色不存在",
                    description=f"`{role.name}` 不在自動分配清單中",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"[Member] 移除自動角色失敗: {e}")
            embed = discord.Embed(
                title="❌ 移除失敗",
                description="移除自動角色時發生錯誤，請稍後再試",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="toggleautorole", description="啟用或停用自動分配角色")
    @app_commands.checks.has_permissions(administrator=True)
    async def toggleautorole(self, interaction: discord.Interaction):
        try:
            guild_id = str(interaction.guild.id)
            config = self.autorole_settings.get(guild_id, {}).get("autorole", {"enabled": False})
            config["enabled"] = not config["enabled"]
            if guild_id not in self.autorole_settings:
                self.autorole_settings[guild_id] = {}
            self.autorole_settings[guild_id]["autorole"] = config
            self.save_autorole_settings()
            
            status = "✅ 啟用" if config['enabled'] else "❌ 停用"
            embed = discord.Embed(
                title=f"{status}自動角色功能",
                description=f"自動分配角色功能已{'啟用' if config['enabled'] else '停用'}",
                color=discord.Color.green() if config['enabled'] else discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"[Member] 切換自動角色失敗: {e}")
            embed = discord.Embed(
                title="❌ 切換失敗",
                description="切換自動角色功能時發生錯誤，請稍後再試",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="listautorole", description="顯示目前自動分配的角色清單")
    @app_commands.checks.has_permissions(administrator=True)
    async def listautorole(self, interaction: discord.Interaction):
        try:
            guild_id = str(interaction.guild.id)
            roles = self.autorole_settings.get(guild_id, {}).get("autorole", {}).get("roles", [])

            if not roles:
                embed = discord.Embed(
                    title="📝 自動分配角色清單",
                    description="目前沒有設定自動分配的角色",
                    color=discord.Color.blue()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            role_list_str = "\n".join(f"- {name}" for name in roles)
            embed = discord.Embed(
                title="📝 自動分配角色清單",
                description=f"目前自動分配角色清單：\n{role_list_str}",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"[Member] 列出自動角色失敗: {e}")
            embed = discord.Embed(
                title="❌ 查詢失敗",
                description="查詢自動角色清單時發生錯誤，請稍後再試",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="togglewelcomecard", description="啟用或停用歡迎卡片")
    @app_commands.checks.has_permissions(administrator=True)
    async def togglewelcomecard(self, interaction: discord.Interaction):
        try:
            guild_id = str(interaction.guild.id)
            config = self.autorole_settings.get(guild_id, {}).get("welcomecard", {"enabled": True})
            config["enabled"] = not config["enabled"]
            if guild_id not in self.autorole_settings:
                self.autorole_settings[guild_id] = {}
            self.autorole_settings[guild_id]["welcomecard"] = config
            self.save_autorole_settings()
            
            status = "✅ 啟用" if config['enabled'] else "❌ 停用"
            embed = discord.Embed(
                title=f"{status}歡迎卡片功能",
                description=f"歡迎卡片功能已{'啟用' if config['enabled'] else '停用'}",
                color=discord.Color.green() if config['enabled'] else discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"[Member] 切換歡迎卡片失敗: {e}")
            embed = discord.Embed(
                title="❌ 切換失敗",
                description="切換歡迎卡片功能時發生錯誤，請稍後再試",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="setroleupdatepm", description="設定是否啟用身分組變動時的私訊通知（管理員限定）")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(enable="是否啟用私訊通知（true/false）")
    async def setroleupdatepm(self, interaction: discord.Interaction, enable: bool):
        try:
            guild_id = str(interaction.guild.id)
            if guild_id not in self.channel_settings:
                self.channel_settings[guild_id] = {}
            self.channel_settings[guild_id]['role_update_pm_enabled'] = enable
            self.save_settings()
            status = "✅ 已啟用" if enable else "❌ 已停用"
            embed = discord.Embed(
                title="身分組私訊通知設定",
                description=f"{status} 身分組變動時的私訊通知",
                color=discord.Color.green() if enable else discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"[Member] 設定身分組私訊通知失敗: {e}")
            embed = discord.Embed(
                title="❌ 設定失敗",
                description="設定身分組私訊通知時發生錯誤，請稍後再試",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """成員離開時的事件"""
        try:
            # 記錄離開日誌
            logger.info(f"成員 {member.name} (ID: {member.id}) 離開了伺服器 {member.guild.name}")
            
            guild_id = str(member.guild.id)
            channel_id = self.channel_settings.get(guild_id, {}).get("welcome_leave_channel_id")
            if channel_id:
                member_channel = self.bot.get_channel(channel_id)
                if member_channel:
                    await member_channel.send(f'**{member.display_name}** 離開了 因為他搞偷吃💢')
            
        except discord.Forbidden:
            logger.error(f"[Member] 沒有權限在離開頻道發送訊息: {member.guild.name}")
        except discord.NotFound:
            logger.error(f"[Member] 離開頻道不存在: {member.guild.name}")
        except Exception as e:
            logger.error(f"[Member] on_member_remove 發生錯誤: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """成員加入時的事件"""
        try:
            # 記錄加入日誌
            logger.info(f"成員 {member.name} (ID: {member.id}) 加入了伺服器 {member.guild.name}")
            
            guild_id = str(member.guild.id)
            config = self.channel_settings.get(guild_id)
            if not config:
                return

            welcome_channel_id = config.get("welcome_leave_channel_id")
            admin_channel_id = config.get("admin_channel_id")
            member_channel = self.bot.get_channel(welcome_channel_id) if welcome_channel_id else None
            admin_channel = self.bot.get_channel(admin_channel_id) if admin_channel_id else None

            if not welcome_channel_id and admin_channel:
                embed = discord.Embed(
                    title="⚠️ 設定提醒",
                    description="尚未設定歡迎頻道，請使用 `/setchannel` 指令進行設定！",
                    color=discord.Color.orange()
                )
                await admin_channel.send(embed=embed)
                return

            guild_config = self.autorole_settings.get(guild_id, {})

            # 歡迎卡片控制
            if guild_config.get("welcomecard", {}).get("enabled", True):
                try:
                    welcome_card = await self.create_welcome_card(member, member.guild.name)
                    if not welcome_card:
                        if admin_channel:
                            embed = discord.Embed(
                                title="⚠️ 歡迎卡片生成失敗",
                                description="生成歡迎卡片時發生錯誤，請檢查程式日誌！",
                                color=discord.Color.red()
                            )
                            await admin_channel.send(embed=embed)
                        return
                    if member_channel:
                        await member_channel.send(
                            content=f'歡迎 **{member.display_name}** 加進來伺服器! 我等不及了❤️',
                            file=discord.File(welcome_card, "welcome_card.png")
                        )
                except Exception as e:
                    logger.error(f"[Member] 生成歡迎卡片失敗: {e}")
                    if admin_channel:
                        embed = discord.Embed(
                            title="⚠️ 歡迎卡片生成失敗",
                            description=f"生成歡迎卡片時發生錯誤：{str(e)}",
                            color=discord.Color.red()
                        )
                        await admin_channel.send(embed=embed)
            
            # 自動分配角色
            autorole = guild_config.get("autorole", {})
            if not autorole.get("enabled", False):
                return

            role_names = autorole.get("roles", [])
            roles_to_add = []
            for role_name in role_names:
                role = discord.utils.get(member.guild.roles, name=role_name)
                if role:
                    roles_to_add.append(role)

            if roles_to_add:
                try:
                    await member.add_roles(*roles_to_add)
                    embed = discord.Embed(
                        title="角色已分配成功",
                        description=f"已為 **{member.display_name}** 分配以下角色：",
                        color=discord.Color.green()
                    )
                    for role in roles_to_add:
                        embed.add_field(name="角色名稱", value=role.name, inline=False)
                    if admin_channel:
                        await admin_channel.send(embed=embed)
                except discord.Forbidden:
                    if admin_channel:
                        await admin_channel.send(f"⚠️ 權限不足，無法為 {member.display_name} 分配角色")
                except discord.HTTPException as e:
                    if admin_channel:
                        await admin_channel.send(f"⚠️ 分配角色時發生錯誤：{e}")
            else:
                if admin_channel:
                    await admin_channel.send(f"⚠️ 找不到任何可分配的角色：\n{chr(10).join(role_names)}")

        except discord.Forbidden:
            logger.error(f"[Member] 沒有權限在歡迎頻道發送訊息: {member.guild.name}")
        except discord.NotFound:
            logger.error(f"[Member] 歡迎頻道不存在: {member.guild.name}")
        except Exception as e:
            logger.error(f"[Member] on_member_join 發生錯誤: {e}")

    def load_welcome_card_config(self):
        """載入歡迎卡片配置"""
        try:
            config_path = 'welcome_card_config.json'
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config
            return None
        except Exception as e:
            logger.error(f"載入歡迎卡片配置失敗: {e}")
            return None

    async def create_welcome_card(self, member, server_name):
        """生成歡迎卡片"""
        try:
            # 只用背景圖 '歡迎卡片範本.png'
            template_path = os.path.join(os.getcwd(), '歡迎卡片範本.png')
            if not os.path.exists(template_path):
                logger.error(f"❌ 找不到背景圖片: 歡迎卡片範本.png")
                return None

            base_image = Image.open(template_path).convert("RGBA")

            # 載入字型
            font_path = os.path.join(os.getcwd(), 'Arial_1_Bold.ttf')
            font_path_regular = os.path.join(os.getcwd(), 'Arial_1.ttf')
            font_hello = ImageFont.truetype(font_path, 117) if os.path.exists(font_path) else ImageFont.load_default()
            font_welcome = ImageFont.truetype(font_path, 124) if os.path.exists(font_path) else ImageFont.load_default()
            font_username = ImageFont.truetype(font_path, 92) if os.path.exists(font_path) else ImageFont.load_default()
            font_server = ImageFont.truetype(font_path_regular, 92) if os.path.exists(font_path_regular) else ImageFont.load_default()


            # 載入頭像
            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as resp:
                    avatar_bytes = await resp.read()
            avatar_size = int(556.7)
            avatar = Image.open(BytesIO(avatar_bytes)).resize((avatar_size, avatar_size)).convert("RGBA")

            # 圓形遮罩（無黑邊）
            mask = Image.new("L", (avatar_size, avatar_size), 0)
            draw_circle = ImageDraw.Draw(mask)
            draw_circle.ellipse((0, 0, avatar_size, avatar_size), fill=255)
            # 頭像位置依範本左上（約 x:110, y:120）
            base_image.paste(avatar, (110, 120), mask)


            draw = ImageDraw.Draw(base_image)

            # 文字描邊函數
            def draw_text_with_outline(draw, pos, text, font, fill, outline_color, outline_width):
                x, y = pos
                # 描邊
                for ox in range(-outline_width, outline_width+1):
                    for oy in range(-outline_width, outline_width+1):
                        if ox == 0 and oy == 0:
                            continue
                        draw.text((x+ox, y+oy), text, font=font, fill=outline_color)
                # 主文字
                draw.text((x, y), text, font=font, fill=fill)

            # Hello! 橘色，粗黑邊
            draw_text_with_outline(draw, (776.6, 180.8), "Hello!", font_hello, "#FF914D", "black", 6)
            # 歡迎...... 白色，粗黑邊
            draw_text_with_outline(draw, (776.6, 373.2), "歡迎......", font_welcome, "#FFFFFF", "black", 6)
            # 使用者名稱 黃色，粗黑邊
            draw_text_with_outline(draw, (47.9, 720.5), f"{member.display_name}", font_username, "#FFD600", "black", 6)
            # 進來伺服器名稱 黃色，粗體字型，粗黑邊
            draw_text_with_outline(draw, (47.9, 820.5), f"進來{server_name}!", font_username, "#FFD600", "black", 6)

            logger.info(f"[WelcomeCard] base_image mode: {base_image.mode}, size: {base_image.size}")
            # debug: 儲存一份到本地
            try:
                base_image.save("test_welcome_card.png")
            except Exception as file_err:
                logger.error(f"[WelcomeCard] 儲存本地 test_welcome_card.png 失敗: {file_err}")

            image_bytes = BytesIO()
            try:
                base_image.save(image_bytes, format='PNG')
                image_bytes.seek(0)
                return image_bytes
            except Exception as e:
                logger.error(f"[WelcomeCard] BytesIO 儲存失敗: {e}")
                return None
        except Exception as e:
            logger.error("生成歡迎卡時發生錯誤: %s", e)
            return None

# 註冊 Cog
async def setup(bot):
    await bot.add_cog(MemberCog(bot))
