import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import logging
from typing import List, Optional
import re

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
            # 檢查具體的權限問題
            bot_member = guild.get_member(interaction.client.user.id)
            if not bot_member.guild_permissions.manage_roles:
                error_msg = "❌ 我沒有「管理身分組」權限，請聯繫管理員授予權限"
            elif self.role.position >= bot_member.top_role.position:
                error_msg = f"❌ 我無法管理身分組 **{self.role.name}**，因為它的權限等級比我高"
            else:
                error_msg = f"❌ 我沒有權限管理身分組 **{self.role.name}**，請聯繫管理員"
            
            await interaction.response.send_message(error_msg, ephemeral=True)
            
        except discord.HTTPException as e:
            if e.status == 429:
                await interaction.response.send_message("❌ 操作過於頻繁，請稍後再試", ephemeral=True)
            else:
                logger.error(f"HTTP錯誤 - 身分組操作失敗: {e}")
                await interaction.response.send_message(f"❌ 網路錯誤 ({e.status})，請稍後再試", ephemeral=True)
                
        except Exception as e:
            logger.error(f"身分組操作失敗: {e}")
            await interaction.response.send_message(f"❌ 操作失敗：{str(e)}", ephemeral=True)

class PublicRoleSelectionView(discord.ui.View):
    def __init__(self, roles: List[discord.Role], max_buttons_per_row: int = 3):
        super().__init__(timeout=None)  # 永久有效
        
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

    @app_commands.command(name="createidentify", description="創建公開的身分組選擇面板（管理員限定）")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.describe(
        roles="要設定的身分組（可多選，用逗號分隔，支援@身分組）",
        title="面板標題（可選）",
        description="面板描述（可選）"
    )
    async def create_identify_panel(self, interaction: discord.Interaction, roles: str = None, title: str = "🎭 身分組選擇", description: str = "點擊下方按鈕來選擇或移除身分組"):
        """創建公開的身分組選擇面板"""
        guild_id = str(interaction.guild.id)
        
        # 如果沒有提供身分組參數，顯示選擇器介面
        if roles is None:
            # 創建身分組選擇視圖
            view = RoleSelectionView(interaction.guild, title, description)
            
            embed = discord.Embed(
                title="🎭 身分組選擇器",
                description="請從下方選擇要加入面板的身分組，然後點擊「創建面板」按鈕\n\n或者您也可以直接使用 `/createidentify roles:@身分組1,@身分組2` 的方式",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"創建者: {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return
        
        # 解析身分組（支援@身分組和文字名稱）
        role_items = [item.strip() for item in roles.split(',')]
        found_roles = []
        not_found = []
        
        for role_item in role_items:
            # 處理可能包含多個@身分組的情況
            if '<@&' in role_item:
                # 提取所有身分組ID
                role_ids = re.findall(r'<@&(\d+)>', role_item)
                for role_id in role_ids:
                    role = interaction.guild.get_role(int(role_id))
                    if role:
                        found_roles.append(role)
                    else:
                        not_found.append(f'<@&{role_id}>')
                continue
            
            role = None
            
            # 檢查是否為@身分組格式（單個）
            if role_item.startswith('<@&') and role_item.endswith('>'):
                # 提取身分組ID
                role_id = role_item[3:-1]  # 移除 <@& 和 >
                role = interaction.guild.get_role(int(role_id))
            elif role_item.startswith('@'):
                # 移除@符號，按名稱查找
                role_name = role_item[1:]
                role = discord.utils.get(interaction.guild.roles, name=role_name)
            else:
                # 直接按名稱查找
                role = discord.utils.get(interaction.guild.roles, name=role_item)
            
            if role:
                found_roles.append(role)
            else:
                not_found.append(role_item)
        
        if not found_roles:
            embed = discord.Embed(
                title="❌ 創建失敗",
                description="找不到任何指定的身分組",
                color=discord.Color.red()
            )
            if not_found:
                embed.add_field(
                    name="⚠️ 未找到的身分組",
                    value=", ".join(not_found),
                    inline=False
                )
                embed.add_field(
                    name="💡 提示",
                    value="請確認身分組名稱是否正確，或使用 @身分組 的方式選擇",
                    inline=False
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            # 儲存設定
            if guild_id not in self.role_config:
                self.role_config[guild_id] = []
            
            # 添加新的身分組到配置中（避免重複）
            existing_role_ids = set(self.role_config[guild_id])
            for role in found_roles:
                if str(role.id) not in existing_role_ids:
                    self.role_config[guild_id].append(str(role.id))
            
            self.save_role_config()
            
            # 創建公開的身分組選擇視圖
            view = PublicRoleSelectionView(found_roles)
            
            # 創建公開的嵌入訊息
            embed = discord.Embed(
                title=title,
                description=description,
                color=discord.Color.blue()
            )
            
            # 添加身分組資訊
            for role in found_roles:
                member_count = len(role.members)
                embed.add_field(
                    name=f"{role.name}",
                    value=f"成員數: {member_count}\n顏色: {str(role.color)}",
                    inline=True
                )
            
            embed.set_footer(text=f"創建者: {interaction.user.display_name} | 點擊按鈕切換身分組")
            
            # 發送公開訊息
            await interaction.channel.send(embed=embed, view=view)
            
            # 回應管理員
            response_embed = discord.Embed(
                title="✅ 身分組面板已創建",
                description="公開的身分組選擇面板已成功創建！",
                color=discord.Color.green()
            )
            
            for role in found_roles:
                response_embed.add_field(name=role.name, value=f"ID: {role.id}", inline=True)
            
            if not_found:
                response_embed.add_field(
                    name="⚠️ 未找到的身分組",
                    value=", ".join(not_found),
                    inline=False
                )
            
            response_embed.set_footer(text=f"創建者: {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=response_embed, ephemeral=True)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ 創建失敗",
                description="我沒有權限在當前頻道發送訊息",
                color=discord.Color.red()
            )
            embed.add_field(
                name="💡 解決方法",
                value="請確認我有「發送訊息」權限，或選擇其他頻道",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except discord.HTTPException as e:
            if e.status == 429:
                await interaction.response.send_message("❌ 操作過於頻繁，請稍後再試", ephemeral=True)
            else:
                logger.error(f"HTTP錯誤 - 創建面板失敗: {e}")
                await interaction.response.send_message(f"❌ 網路錯誤 ({e.status})，請稍後再試", ephemeral=True)
                
        except Exception as e:
            logger.error(f"創建面板失敗: {e}")
            await interaction.response.send_message(f"❌ 創建失敗：{str(e)}", ephemeral=True)

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
            embed.add_field(
                name="💡 提示",
                value="使用 `/createidentify` 來創建身分組選擇面板",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
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
                embed.add_field(
                    name="💡 建議",
                    value="建議使用 `/clearidentify` 清空已刪除的身分組",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"列出身分組失敗: {e}")
            await interaction.response.send_message(f"❌ 列出失敗：{str(e)}", ephemeral=True)

    @app_commands.command(name="clearidentify", description="清空可選擇的身分組（管理員限定）")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def clear_identify_roles(self, interaction: discord.Interaction):
        """清空可選擇的身分組"""
        guild_id = str(interaction.guild.id)
        
        try:
            if guild_id in self.role_config:
                role_count = len(self.role_config[guild_id])
                del self.role_config[guild_id]
                self.save_role_config()
                
                embed = discord.Embed(
                    title="🗑️ 身分組已清空",
                    description=f"已清空 {role_count} 個可選擇的身分組",
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
            
        except Exception as e:
            logger.error(f"清空身分組失敗: {e}")
            await interaction.response.send_message(f"❌ 清空失敗：{str(e)}", ephemeral=True)

    @app_commands.command(name="removeidentify", description="移除自己的身分組")
    @app_commands.describe(role="要移除的身分組")
    async def remove_identify_role(self, interaction: discord.Interaction, role: discord.Role):
        """移除自己的身分組"""
        user = interaction.user
        guild_id = str(interaction.guild.id)
        
        # 檢查用戶是否有該身分組
        if role not in user.roles:
            embed = discord.Embed(
                title="❌ 移除失敗",
                description=f"您沒有身分組 **{role.name}**",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # 檢查該身分組是否在可選擇清單中
        if guild_id not in self.role_config:
            embed = discord.Embed(
                title="❌ 移除失敗",
                description="目前沒有設定任何可選擇的身分組",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        role_ids = self.role_config[guild_id]
        role_id_str = str(role.id)
        
        if role_id_str not in role_ids:
            embed = discord.Embed(
                title="❌ 移除失敗",
                description=f"**{role.name}** 不在可選擇清單中",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            # 移除身分組
            await user.remove_roles(role)
            
            embed = discord.Embed(
                title="✅ 身分組已移除",
                description=f"已移除身分組 **{role.name}**",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"用戶: {user.display_name}")
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ 移除失敗",
                description="我沒有權限移除該身分組，請聯繫管理員",
                color=discord.Color.red()
            )
            embed.add_field(
                name="💡 可能原因",
                value="• 我的權限等級比該身分組低\n• 我沒有「管理身分組」權限\n• 該身分組受到保護",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.HTTPException as e:
            if e.status == 429:
                await interaction.response.send_message("❌ 操作過於頻繁，請稍後再試", ephemeral=True)
            else:
                logger.error(f"HTTP錯誤 - 移除身分組失敗: {e}")
                await interaction.response.send_message(f"❌ 網路錯誤 ({e.status})，請稍後再試", ephemeral=True)
        except Exception as e:
            logger.error(f"移除身分組失敗: {e}")
            await interaction.response.send_message(f"❌ 移除失敗：{str(e)}", ephemeral=True)

class RoleSelectionView(discord.ui.View):
    def __init__(self, guild: discord.Guild, title: str, description: str):
        super().__init__(timeout=300)  # 5分鐘超時
        self.guild = guild
        self.title = title
        self.description = description
        self.selected_roles = []
        
        # 創建身分組選擇器
        self.role_select = RoleSelect(
            guild,
            placeholder="選擇身分組（可多選）",
            min_values=1,
            max_values=25,  # Discord 限制最多25個選項
            custom_id="role_select"
        )
        self.add_item(self.role_select)
        
        # 創建按鈕
        self.add_item(CreatePanelButton(self))

class RoleSelect(discord.ui.Select):
    def __init__(self, guild: discord.Guild, placeholder: str, min_values: int, max_values: int, custom_id: str):
        self.guild = guild
        # 獲取所有身分組作為選項
        options = []
        for role in guild.roles:
            if role.name != "@everyone" and not role.managed:  # 排除 @everyone 和機器人管理的身分組
                options.append(discord.SelectOption(
                    label=role.name,
                    value=str(role.id),
                    description=f"成員數: {len(role.members)}",
                    emoji="🎭"
                ))
        
        super().__init__(
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            options=options,
            custom_id=custom_id
        )

    async def callback(self, interaction: discord.Interaction):
        # 更新選中的身分組
        view = self.view
        view.selected_roles = []
        
        for role_id in self.values:
            role = interaction.guild.get_role(int(role_id))
            if role:
                view.selected_roles.append(role)
        
        # 更新嵌入訊息
        embed = discord.Embed(
            title="🎭 身分組選擇器",
            description=f"已選擇 {len(view.selected_roles)} 個身分組\n點擊「創建面板」按鈕來創建公開面板",
            color=discord.Color.green()
        )
        
        for role in view.selected_roles:
            member_count = len(role.members)
            embed.add_field(
                name=role.name,
                value=f"成員數: {member_count}",
                inline=True
            )
        
        embed.set_footer(text=f"創建者: {interaction.user.display_name}")
        
        await interaction.response.edit_message(embed=embed, view=view)

class CreatePanelButton(discord.ui.Button):
    def __init__(self, view: RoleSelectionView):
        super().__init__(
            label="創建面板",
            style=discord.ButtonStyle.success,
            emoji="✅"
        )
        self.view = view

    async def callback(self, interaction: discord.Interaction):
        if not self.view.selected_roles:
            await interaction.response.send_message("❌ 請先選擇至少一個身分組", ephemeral=True)
            return
        
        guild_id = str(interaction.guild.id)
        
        # 獲取cog實例
        cog = interaction.client.get_cog('RoleManager')
        if not cog:
            await interaction.response.send_message("❌ 系統錯誤：找不到身分組管理器", ephemeral=True)
            return
        
        try:
            # 儲存設定
            if guild_id not in cog.role_config:
                cog.role_config[guild_id] = []
            
            # 添加新的身分組到配置中（避免重複）
            existing_role_ids = set(cog.role_config[guild_id])
            for role in self.view.selected_roles:
                if str(role.id) not in existing_role_ids:
                    cog.role_config[guild_id].append(str(role.id))
            
            cog.save_role_config()
            
            # 創建公開的身分組選擇視圖
            public_view = PublicRoleSelectionView(self.view.selected_roles)
            
            # 創建公開的嵌入訊息
            embed = discord.Embed(
                title=self.view.title,
                description=self.view.description,
                color=discord.Color.blue()
            )
            
            # 添加身分組資訊
            for role in self.view.selected_roles:
                member_count = len(role.members)
                embed.add_field(
                    name=f"{role.name}",
                    value=f"成員數: {member_count}\n顏色: {str(role.color)}",
                    inline=True
                )
            
            embed.set_footer(text=f"創建者: {interaction.user.display_name} | 點擊按鈕切換身分組")
            
            # 發送公開訊息
            await interaction.channel.send(embed=embed, view=public_view)
            
            # 回應管理員
            response_embed = discord.Embed(
                title="✅ 身分組面板已創建",
                description="公開的身分組選擇面板已成功創建！",
                color=discord.Color.green()
            )
            
            for role in self.view.selected_roles:
                response_embed.add_field(name=role.name, value=f"ID: {role.id}", inline=True)
            
            response_embed.set_footer(text=f"創建者: {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=response_embed, ephemeral=True)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ 創建失敗",
                description="我沒有權限在當前頻道發送訊息",
                color=discord.Color.red()
            )
            embed.add_field(
                name="💡 解決方法",
                value="請確認我有「發送訊息」權限，或選擇其他頻道",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except discord.HTTPException as e:
            if e.status == 429:
                await interaction.response.send_message("❌ 操作過於頻繁，請稍後再試", ephemeral=True)
            else:
                logger.error(f"HTTP錯誤 - 創建面板失敗: {e}")
                await interaction.response.send_message(f"❌ 網路錯誤 ({e.status})，請稍後再試", ephemeral=True)
                
        except Exception as e:
            logger.error(f"創建面板失敗: {e}")
            await interaction.response.send_message(f"❌ 創建失敗：{str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RoleManager(bot)) 