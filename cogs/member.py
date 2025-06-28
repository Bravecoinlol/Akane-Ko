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
        if not os.path.exists(self.settings_path):
            with open(self.settings_path, 'w', encoding='utf8') as f:
                json.dump({}, f)
        with open(self.settings_path, 'r', encoding='utf8') as f:
            content = f.read().strip()
            return json.loads(content) if content else {}

    def load_autorole_settings(self):
        if not os.path.exists(self.autorole_path):
            with open(self.autorole_path, 'w', encoding='utf8') as f:
                json.dump({}, f)
        with open(self.autorole_path, 'r', encoding='utf8') as f:
            content = f.read().strip()
            return json.loads(content) if content else {}

    def save_settings(self):
        with open(self.settings_path, 'w', encoding='utf8') as f:
            json.dump(self.channel_settings, f, ensure_ascii=False, indent=4)

    def save_autorole_settings(self):
        with open(self.autorole_path, 'w', encoding='utf8') as f:
            json.dump(self.autorole_settings, f, ensure_ascii=False, indent=4)

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message("還想偷看管理員的東西啊？🤨", ephemeral=True)
        else:
            logger.error("指令錯誤: %s", error)

    @app_commands.command(name="setchannel", description="設定歡迎/離開頻道或管理頻道")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(type="選擇頻道用途", channel="指定的頻道")
    @app_commands.choices(type=[
        app_commands.Choice(name="歡迎與離開頻道", value="welcome_leave"),
        app_commands.Choice(name="管理頻道", value="admin")
    ])
    async def set_channel(self, interaction: discord.Interaction, type: app_commands.Choice[str], channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.channel_settings:
            self.channel_settings[guild_id] = {}

        self.channel_settings[guild_id][f"{type.value}_channel_id"] = channel.id
        self.save_settings()
        await interaction.response.send_message(f"✅ 已設定 `{type.name}` 為 {channel.mention}", ephemeral=True)

    @app_commands.command(name="setautorole", description="新增要自動分配的角色")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(role="要加入自動分配清單的角色")
    async def setautorole(self, interaction: discord.Interaction, role: discord.Role):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.autorole_settings:
            self.autorole_settings[guild_id] = {}

        existing = self.autorole_settings[guild_id].get("autorole", {"enabled": True, "roles": []})
        if role.name not in existing["roles"]:
            existing["roles"].append(role.name)

        self.autorole_settings[guild_id]["autorole"] = existing
        self.save_autorole_settings()

        await interaction.response.send_message(f"✅ 已新增 `{role.name}` 到自動分配角色清單", ephemeral=True)

    @app_commands.command(name="removeautorole", description="從自動分配清單中移除角色")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(role="要移除的角色")
    async def removeautorole(self, interaction: discord.Interaction, role: discord.Role):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.autorole_settings:
            await interaction.response.send_message("⚠️ 此伺服器尚未設定自動分配角色", ephemeral=True)
            return

        config = self.autorole_settings[guild_id].get("autorole", {"enabled": True, "roles": []})
        if role.name in config["roles"]:
            config["roles"].remove(role.name)
            self.autorole_settings[guild_id]["autorole"] = config
            self.save_autorole_settings()
            await interaction.response.send_message(f"✅ 已移除 `{role.name}` 從自動分配清單", ephemeral=True)
        else:
            await interaction.response.send_message(f"⚠️ `{role.name}` 不在自動分配清單中", ephemeral=True)

    @app_commands.command(name="toggleautorole", description="啟用或停用自動分配角色")
    @app_commands.checks.has_permissions(administrator=True)
    async def toggleautorole(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        config = self.autorole_settings.get(guild_id, {}).get("autorole", {"enabled": False})
        config["enabled"] = not config["enabled"]
        if guild_id not in self.autorole_settings:
            self.autorole_settings[guild_id] = {}
        self.autorole_settings[guild_id]["autorole"] = config
        self.save_autorole_settings()
        await interaction.response.send_message(f"{'✅ 啟用' if config['enabled'] else '❌ 停用'}自動角色功能", ephemeral=True)

    @app_commands.command(name="listautorole", description="顯示目前自動分配的角色清單")
    @app_commands.checks.has_permissions(administrator=True)
    async def listautorole(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        roles = self.autorole_settings.get(guild_id, {}).get("autorole", {}).get("roles", [])

        if not roles:
            await interaction.response.send_message("⚠️ 目前沒有設定自動分配的角色", ephemeral=True)
            return

        role_list_str = "\n".join(f"- {name}" for name in roles)
        await interaction.response.send_message(f"📝 目前自動分配角色清單：\n{role_list_str}", ephemeral=True)

    @app_commands.command(name="togglewelcomecard", description="啟用或停用歡迎卡片")
    @app_commands.checks.has_permissions(administrator=True)
    async def togglewelcomecard(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        config = self.autorole_settings.get(guild_id, {}).get("welcomecard", {"enabled": True})
        config["enabled"] = not config["enabled"]
        if guild_id not in self.autorole_settings:
            self.autorole_settings[guild_id] = {}
        self.autorole_settings[guild_id]["welcomecard"] = config
        self.save_autorole_settings()
        await interaction.response.send_message(f"{'✅ 啟用' if config['enabled'] else '❌ 停用'}歡迎卡片功能", ephemeral=True)
    
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
            
        except Exception as e:
            logger.error("on_member_remove 發生錯誤: %s", e)

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
                await admin_channel.send("⚠️ 尚未設定歡迎頻道，請使用 `/setchannel` 指令進行設定！")
                return

            guild_config = self.autorole_settings.get(guild_id, {})

            # 歡迎卡片控制
            if guild_config.get("welcomecard", {}).get("enabled", True):
                welcome_card = await self.create_welcome_card(member, member.guild.name)
                if not welcome_card:
                    if admin_channel:
                        await admin_channel.send("⚠️ 生成歡迎卡失敗，請檢查程式日誌！")
                    return
                if member_channel:
                    await member_channel.send(
                        content=f'歡迎 **{member.display_name}** 加進來伺服器! 我等不及了❤️',
                        file=discord.File(welcome_card, "welcome_card.png")
                    )

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

        except Exception as e:
            logger.error("on_member_join 發生錯誤: %s", e)

    async def create_welcome_card(self, member, server_name):
        """生成歡迎卡片"""
        try:
            template_path = os.path.join(os.getcwd(), "歡迎卡片範本.png")
            if not os.path.exists(template_path):
                logger.error("❌ 找不到歡迎卡片範本.png")
                return None

            base_image = Image.open(template_path).convert("RGBA").resize((1920, 1080))
            font_path = "Arial_1.ttf"
            font_path_bold = "Arial_1_Bold.ttf"
            font_large = ImageFont.truetype(font_path_bold, 120)
            font_medium = ImageFont.truetype(font_path_bold, 80)
            font_small = ImageFont.truetype(font_path, 60)

            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as resp:
                    avatar_bytes = await resp.read()
            avatar = Image.open(BytesIO(avatar_bytes)).resize((400, 400)).convert("RGBA")

            mask = Image.new("L", avatar.size, 0)
            draw_circle = ImageDraw.Draw(mask)
            draw_circle.ellipse((0, 0, 400, 400), fill=255)
            base_image.paste(avatar, (100, 340), mask)

            draw = ImageDraw.Draw(base_image)
            draw.text((550, 340), f"歡迎 {member.display_name}", font=font_large, fill="white")
            draw.text((550, 480), f"加入 {server_name}!", font=font_medium, fill="red")
            draw.text((550, 620), "希望您玩得愉快 :>", font=font_small, fill="white")

            image_bytes = BytesIO()
            base_image.save(image_bytes, format='PNG')
            image_bytes.seek(0)
            return image_bytes

        except Exception as e:
            logger.error("生成歡迎卡時發生錯誤: %s", e)
            return None

# 註冊 Cog
async def setup(bot):
    await bot.add_cog(MemberCog(bot))
