import discord
from discord.ext import commands
import json
import os
from discord import app_commands
from io import BytesIO

CROSSCHAT_CONFIG = 'crosschat_channels.json'

def load_crosschat_channels():
    if not os.path.exists(CROSSCHAT_CONFIG):
        with open(CROSSCHAT_CONFIG, 'w', encoding='utf-8') as f:
            json.dump([], f)
    with open(CROSSCHAT_CONFIG, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_crosschat_channels(channels):
    with open(CROSSCHAT_CONFIG, 'w', encoding='utf-8') as f:
        json.dump(channels, f, ensure_ascii=False, indent=2)

class CrossChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channels = load_crosschat_channels()

    @app_commands.command(name="addcrosschat", description="新增跨群聊天頻道（管理員限定）")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(channel="要加入跨群聊天的頻道")
    async def add_crosschat(self, interaction: discord.Interaction, channel: discord.TextChannel):
        entry = {'guild_id': interaction.guild.id, 'channel_id': channel.id}
        if entry not in self.channels:
            self.channels.append(entry)
            save_crosschat_channels(self.channels)
            await interaction.response.send_message(f'✅ 已新增跨群聊天頻道: {channel.mention}', ephemeral=True)
        else:
            await interaction.response.send_message('此頻道已在跨群聊天清單中', ephemeral=True)

    @app_commands.command(name="removecrosschat", description="移除跨群聊天頻道（管理員限定）")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(channel="要移除的跨群聊天頻道")
    async def remove_crosschat(self, interaction: discord.Interaction, channel: discord.TextChannel):
        before = len(self.channels)
        self.channels = [c for c in self.channels if not (c['guild_id'] == interaction.guild.id and c['channel_id'] == channel.id)]
        save_crosschat_channels(self.channels)
        if len(self.channels) < before:
            await interaction.response.send_message(f'✅ 已移除跨群聊天頻道: {channel.mention}', ephemeral=True)
        else:
            await interaction.response.send_message('此頻道不在跨群聊天清單中', ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        # 檢查是否在跨群聊天頻道
        for entry in self.channels:
            if message.guild and message.channel.id == entry['channel_id'] and message.guild.id == entry['guild_id']:
                # 轉發到其他所有跨群頻道
                for target in self.channels:
                    if target['guild_id'] != message.guild.id or target['channel_id'] != message.channel.id:
                        target_guild = self.bot.get_guild(target['guild_id'])
                        if target_guild:
                            target_channel = target_guild.get_channel(target['channel_id'])
                            if target_channel:
                                # 組合訊息
                                content = f"[{message.guild.name}] {message.author.display_name}: {message.content}" if message.content else f"[{message.guild.name}] {message.author.display_name}: "
                                files = []
                                for attachment in message.attachments:
                                    try:
                                        fp = await attachment.read()
                                        discord_file = discord.File(fp=BytesIO(fp), filename=attachment.filename)
                                        files.append(discord_file)
                                    except Exception:
                                        pass
                                await target_channel.send(content, files=files if files else None)
                break

async def setup(bot):
    await bot.add_cog(CrossChat(bot))
