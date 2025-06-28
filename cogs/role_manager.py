import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import logging
from typing import List, Optional

logger = logging.getLogger('RoleManager')

class RoleButton(discord.ui.Button):
    def __init__(self, role: discord.Role, label: str, emoji: str = None, style: discord.ButtonStyle = discord.ButtonStyle.primary):
        super().__init__(
            label=label,
            emoji=emoji,
            style=style,
            custom_id=f"role_{role.id}"
        )
        self.role = role

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        guild = interaction.guild
        
        try:
            # 檢查用戶是否已有該身分組
            if self.role in user.roles:
                # 移除身分組
                await user.remove_roles(self.role)
                embed = discord.Embed(
                    title="❌ 身分組已移除",
                    description=f"已移除身分組 **{self.role.name}**",
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"用戶: {user.display_name}")
            else:
                # 添加身分組
                await user.add_roles(self.role)
                embed = discord.Embed(
                    title="✅ 身分組已分配",
                    description=f"已分配身分組 **{self.role.name}**",
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"用戶: {user.display_name}")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ 我沒有權限管理身分組", ephemeral=True)
        except Exception as e:
            logger.error(f"身分組操作失敗: {e}")
            await interaction.response.send_message("❌ 操作失敗，請聯繫管理員", ephemeral=True)

class RoleSelectionView(discord.ui.View):
    def __init__(self, roles: List[discord.Role], max_buttons_per_row: int = 3):
        super().__init__(timeout=300)  # 5分鐘超時
        
        # 為每個身分組創建按鈕
        for i, role in enumerate(roles):
            # 計算按鈕樣式和表情符號
            style = discord.ButtonStyle.primary
            emoji = "🎭"  # 預設表情符號
            
            # 根據身分組顏色設定按鈕樣式
            if role.color.value != 0:
                if role.color.value < 0x800000:  # 深色
                    style = discord.ButtonStyle.secondary
                elif role.color.value > 0xFFFF00:  # 亮色
                    style = discord.ButtonStyle.success
            
            # 創建按鈕
            button = RoleButton(role, role.name, emoji, style)
            button.row = i // max_buttons_per_row  # 每行最多3個按鈕
            self.add_item(button)

class RoleManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.role_config_path = 'role_config.json'
        self.role_config = self.load_role_config()

    def load_role_config(self):
        """載入身分組配置"""
        try:
            with open(self.role_config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_role_config(self):
        """儲存身分組配置"""
        with open(self.role_config_path, 'w', encoding='utf-8') as f:
            json.dump(self.role_config, f, ensure_ascii=False, indent=2)

    @app_commands.command(name="identify", description="選擇你的身分組")
    async def identify(self, interaction: discord.Interaction):
        """身分組選擇指令"""
        guild_id = str(interaction.guild.id)
        
        # 檢查是否有設定身分組
        if guild_id not in self.role_config or not self.role_config[guild_id]:
            embed = discord.Embed(
                title="❌ 尚未設定身分組",
                description="管理員尚未設定可選擇的身分組\n請聯繫管理員使用 `/setidentify` 設定",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # 獲取可選擇的身分組
        role_ids = self.role_config[guild_id]
        roles = []
        
        for role_id in role_ids:
            role = interaction.guild.get_role(int(role_id))
            if role:
                roles.append(role)

        if not roles:
            embed = discord.Embed(
                title="❌ 身分組設定錯誤",
                description="設定的身分組不存在或已被刪除",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # 創建身分組選擇視圖
        view = RoleSelectionView(roles)
        
        embed = discord.Embed(
            title="🎭 身分組選擇",
            description="點擊下方按鈕來選擇或移除身分組\n\n**可選擇的身分組：**",
            color=discord.Color.blue()
        )
        
        for role in roles:
            status = "✅ 已擁有" if role in interaction.user.roles else "❌ 未擁有"
            embed.add_field(
                name=f"{role.name}",
                value=f"狀態: {status}\n顏色: {str(role.color)}",
                inline=True
            )
        
        embed.set_footer(text=f"用戶: {interaction.user.display_name} | 點擊按鈕切換身分組")
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="setidentify", description="設定可選擇的身分組（管理員限定）")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.describe(roles="要設定的身分組（可多選，用逗號分隔）")
    async def set_identify_roles(self, interaction: discord.Interaction, roles: str):
        """設定可選擇的身分組"""
        guild_id = str(interaction.guild.id)
        
        # 解析身分組名稱
        role_names = [name.strip() for name in roles.split(',')]
        found_roles = []
        not_found = []
        
        for role_name in role_names:
            role = discord.utils.get(interaction.guild.roles, name=role_name)
            if role:
                found_roles.append(role)
            else:
                not_found.append(role_name)
        
        if not found_roles:
            embed = discord.Embed(
                title="❌ 設定失敗",
                description="找不到任何指定的身分組",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # 儲存設定
        if guild_id not in self.role_config:
            self.role_config[guild_id] = []
        
        self.role_config[guild_id] = [str(role.id) for role in found_roles]
        self.save_role_config()
        
        # 創建回應嵌入
        embed = discord.Embed(
            title="✅ 身分組設定完成",
            description="以下身分組已設定為可選擇：",
            color=discord.Color.green()
        )
        
        for role in found_roles:
            embed.add_field(name=role.name, value=f"ID: {role.id}", inline=True)
        
        if not_found:
            embed.add_field(
                name="⚠️ 未找到的身分組",
                value=", ".join(not_found),
                inline=False
            )
        
        embed.set_footer(text=f"設定者: {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="listidentify", description="查看目前可選擇的身分組（管理員限定）")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def list_identify_roles(self, interaction: discord.Interaction):
        """列出可選擇的身分組"""
        guild_id = str(interaction.guild.id)
        
        if guild_id not in self.role_config or not self.role_config[guild_id]:
            embed = discord.Embed(
                title="📋 可選擇身分組列表",
                description="目前沒有設定任何可選擇的身分組",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        role_ids = self.role_config[guild_id]
        roles = []
        not_found = []
        
        for role_id in role_ids:
            role = interaction.guild.get_role(int(role_id))
            if role:
                roles.append(role)
            else:
                not_found.append(role_id)
        
        embed = discord.Embed(
            title="📋 可選擇身分組列表",
            description=f"共 {len(roles)} 個身分組",
            color=discord.Color.blue()
        )
        
        for role in roles:
            member_count = len(role.members)
            embed.add_field(
                name=role.name,
                value=f"成員數: {member_count}\n顏色: {str(role.color)}",
                inline=True
            )
        
        if not_found:
            embed.add_field(
                name="⚠️ 已刪除的身分組",
                value=", ".join(not_found),
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="clearidentify", description="清空可選擇的身分組（管理員限定）")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def clear_identify_roles(self, interaction: discord.Interaction):
        """清空可選擇的身分組"""
        guild_id = str(interaction.guild.id)
        
        if guild_id in self.role_config:
            del self.role_config[guild_id]
            self.save_role_config()
            
            embed = discord.Embed(
                title="🗑️ 身分組已清空",
                description="所有可選擇的身分組已被清空",
                color=discord.Color.orange()
            )
        else:
            embed = discord.Embed(
                title="ℹ️ 無需清空",
                description="本來就沒有設定任何身分組",
                color=discord.Color.blue()
            )
        
        embed.set_footer(text=f"操作者: {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="removeidentify", description="移除特定身分組（管理員限定）")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.describe(role="要移除的身分組")
    async def remove_identify_role(self, interaction: discord.Interaction, role: discord.Role):
        """移除特定身分組"""
        guild_id = str(interaction.guild.id)
        
        if guild_id not in self.role_config:
            embed = discord.Embed(
                title="❌ 移除失敗",
                description="目前沒有設定任何身分組",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        role_ids = self.role_config[guild_id]
        role_id_str = str(role.id)
        
        if role_id_str in role_ids:
            role_ids.remove(role_id_str)
            self.save_role_config()
            
            embed = discord.Embed(
                title="✅ 身分組已移除",
                description=f"已從可選擇清單中移除 **{role.name}**",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ 移除失敗",
                description=f"**{role.name}** 不在可選擇清單中",
                color=discord.Color.red()
            )
        
        embed.set_footer(text=f"操作者: {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(RoleManager(bot)) 