import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from typing import List, Optional
import logging

ROLE_PANEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'role_panel.json')

logger = logging.getLogger('RoleManager')

def load_role_panels():
    if not os.path.exists(ROLE_PANEL_PATH):
        with open(ROLE_PANEL_PATH, 'w', encoding='utf-8') as f:
            json.dump([], f)
    with open(ROLE_PANEL_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_role_panels(panels):
    with open(ROLE_PANEL_PATH, 'w', encoding='utf-8') as f:
        json.dump(panels, f, ensure_ascii=False, indent=2)

class RoleManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.role_panels = load_role_panels()
        # 設置按鈕監聽器
        bot.add_listener(self.handle_role_button, "on_interaction")
        
    async def handle_role_button(self, interaction: discord.Interaction):
        if not interaction.data or not interaction.data.get("custom_id", "").startswith("rolepanel_"):
            return
            
        role_id = int(interaction.data["custom_id"].split("_")[1])
        # 確認這個身分組是否屬於任何面板
        panel = None
        for p in self.role_panels:
            if (p["guild_id"] == interaction.guild_id and 
                p["message_id"] == interaction.message.id and
                role_id in p["role_ids"]):
                panel = p
                break
                
        if not panel:
            await interaction.response.send_message("❌ 此面板已失效，請重新建立。", ephemeral=True)
            return
            
        # 檢查身分組是否還存在
        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.response.send_message("❌ 此身分組已不存在。", ephemeral=True)
            return
        
        # 切換身分組
        try:
            if role in interaction.user.roles:
                await interaction.user.remove_roles(role)
                await interaction.response.send_message(f"✅ 已移除 {role.mention} 身分組", ephemeral=True)
            else:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(f"✅ 已加入 {role.mention} 身分組", ephemeral=True)
        except discord.HTTPException:
            await interaction.response.send_message("❌ 無法切換身分組，請確認機器人權限。", ephemeral=True)
    @app_commands.command(name="listpanel", description="列出目前伺服器的所有身分組面板")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def list_panels(self, interaction: discord.Interaction):
        # 找出該伺服器的所有面板
        server_panels = [p for p in self.role_panels if p["guild_id"] == interaction.guild.id]
        if not server_panels:
            await interaction.response.send_message("❌ 此伺服器目前沒有任何身分組面板。", ephemeral=True)
            return

        # 建立嵌入訊息
        embed = discord.Embed(title="📋 身分組面板列表", color=discord.Color.blue())
        for panel in server_panels:
            # 取得面板中的身分組
            roles = [interaction.guild.get_role(rid) for rid in panel["role_ids"]]
            valid_roles = [role.mention for role in roles if role]
            
            # 加入面板資訊
            value = f"標題: {panel['title']}\n"
            value += f"頻道: <#{panel['channel_id']}>\n"
            value += f"身分組: {' '.join(valid_roles) if valid_roles else '無可用身分組'}"
            embed.add_field(
                name=f"面板 ID: {panel['message_id']}", 
                value=value,
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="deletepanel", description="刪除指定的身分組面板")
    @app_commands.describe(message_id="要刪除的面板訊息ID")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def delete_panel(self, interaction: discord.Interaction, message_id: str):
        # 尋找面板
        panel_index = None
        for i, p in enumerate(self.role_panels):
            if str(p["message_id"]) == message_id and p["guild_id"] == interaction.guild.id:
                panel_index = i
                break

        if panel_index is None:
            await interaction.response.send_message("❌ 找不到指定的面板。", ephemeral=True)
            return

        try:
            # 嘗試刪除原始訊息
            channel = interaction.guild.get_channel(self.role_panels[panel_index]["channel_id"])
            if channel:
                try:
                    message = await channel.fetch_message(int(message_id))
                    await message.delete()
                except (discord.NotFound, discord.Forbidden):
                    pass  # 如果訊息已經被刪除或沒有權限，就忽略

            # 從記錄中移除面板
            self.role_panels.pop(panel_index)
            save_role_panels(self.role_panels)
            await interaction.response.send_message(f"✅ 已成功刪除面板 (ID: {message_id})。", ephemeral=True)

        except Exception as e:
            logger.error(f"刪除面板時發生錯誤: {str(e)}")
            await interaction.response.send_message("❌ 刪除面板時發生錯誤。", ephemeral=True)

    @app_commands.command(name="createpanel", description="建立公開身分組面板（管理員限定）")
    @app_commands.describe(
        roles="要新增的身分組（可用空格分隔多個）",
        title="面板標題（可選）",
        description="面板描述（可選）"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def create_panel(
        self,
        interaction: discord.Interaction,
        roles: str,
        title: Optional[str] = None,
        description: Optional[str] = None
    ):
        # 解析身分組ID
        role_ids = [rid.strip('<@&>') for rid in roles.split()]
        valid_roles = []
        
        # 檢查每個身分組
        for role_id in role_ids:
            try:
                role = interaction.guild.get_role(int(role_id))
                if not role or role.is_bot_managed() or role.is_integration() or role.is_premium_subscriber() or role >= interaction.guild.me.top_role or role.managed or role.name == "@everyone":
                    await interaction.response.send_message(f"❌ 無效的身分組: {role_id}", ephemeral=True)
                    return
                valid_roles.append(role)
            except ValueError:
                await interaction.response.send_message(f"❌ 無效的身分組格式: {role_id}", ephemeral=True)
                return
        
        if not valid_roles:
            await interaction.response.send_message("❌ 請至少提供一個有效的身分組。", ephemeral=True)
            return
        title = title or "🎭 身分組選擇"
        description = description or "請點擊下方按鈕來選擇或移除身分組"
        
        # 建立面板
        view = RolePanelView(valid_roles)
        embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
        
        # 添加所有身分組資訊
        for role in valid_roles:
            embed.add_field(name=role.name, value=f"ID: {role.id}\n成員數: {len(role.members)}", inline=True)
            
        embed.set_footer(text=f"創建者: {interaction.user.display_name} | 點擊按鈕切換身分組")
        panel_message = await interaction.channel.send(embed=embed, view=view)
        
        # 記錄面板
        panel = {
            "guild_id": interaction.guild.id,
            "channel_id": interaction.channel.id,
            "message_id": panel_message.id,
            "role_ids": [role.id for role in valid_roles],
            "title": title,
            "description": description
        }
        self.role_panels.append(panel)
        save_role_panels(self.role_panels)
        await interaction.response.send_message(
            f"✅ 已建立包含 {len(valid_roles)} 個身分組的面板 (訊息ID: {panel_message.id})", 
            ephemeral=True
        )
class RolePanelView(discord.ui.View):
    def __init__(self, roles: List[discord.Role]):
        super().__init__(timeout=None)
        for role in roles:
            self.add_item(RolePanelButton(role))

class RolePanelButton(discord.ui.Button):
    def __init__(self, role: discord.Role):
        super().__init__(
            label=role.name,
            style=discord.ButtonStyle.primary,
            custom_id=f"rolepanel_{role.id}",
            row=None  # 自動排列按鈕
        )

async def setup(bot):
    await bot.add_cog(RoleManager(bot))
