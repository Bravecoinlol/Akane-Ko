import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import logging
from datetime import datetime, timedelta
from collections import defaultdict, Counter

logger = logging.getLogger('Analytics')

class Analytics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.analytics_data = {}
        self.load_analytics_data()

    def load_analytics_data(self):
        """載入分析數據"""
        try:
            with open('analytics.json', 'r', encoding='utf-8') as f:
                self.analytics_data = json.load(f)
        except FileNotFoundError:
            self.analytics_data = {
                'message_counts': {},
                'user_activity': {},
                'channel_activity': {},
                'command_usage': {},
                'join_dates': {}
            }

    def save_analytics_data(self):
        """儲存分析數據"""
        with open('analytics.json', 'w', encoding='utf-8') as f:
            json.dump(self.analytics_data, f, ensure_ascii=False, indent=2)

    def record_message(self, guild_id: str, user_id: str, channel_id: str):
        """記錄訊息"""
        guild_id_str = str(guild_id)
        user_id_str = str(user_id)
        channel_id_str = str(channel_id)
        date_str = datetime.now().strftime('%Y-%m-%d')

        # 初始化數據結構
        if guild_id_str not in self.analytics_data['message_counts']:
            self.analytics_data['message_counts'][guild_id_str] = {}
        if guild_id_str not in self.analytics_data['user_activity']:
            self.analytics_data['user_activity'][guild_id_str] = {}
        if guild_id_str not in self.analytics_data['channel_activity']:
            self.analytics_data['channel_activity'][guild_id_str] = {}

        # 記錄訊息數量
        if date_str not in self.analytics_data['message_counts'][guild_id_str]:
            self.analytics_data['message_counts'][guild_id_str][date_str] = 0
        self.analytics_data['message_counts'][guild_id_str][date_str] += 1

        # 記錄用戶活動
        if user_id_str not in self.analytics_data['user_activity'][guild_id_str]:
            self.analytics_data['user_activity'][guild_id_str][user_id_str] = {
                'message_count': 0,
                'last_active': None,
                'channels': {}
            }
        
        user_data = self.analytics_data['user_activity'][guild_id_str][user_id_str]
        user_data['message_count'] += 1
        user_data['last_active'] = datetime.now().isoformat()
        
        if channel_id_str not in user_data['channels']:
            user_data['channels'][channel_id_str] = 0
        user_data['channels'][channel_id_str] += 1

        # 記錄頻道活動
        if channel_id_str not in self.analytics_data['channel_activity'][guild_id_str]:
            self.analytics_data['channel_activity'][guild_id_str][channel_id_str] = 0
        self.analytics_data['channel_activity'][guild_id_str][channel_id_str] += 1

        self.save_analytics_data()

    def record_command(self, guild_id: str, user_id: str, command_name: str):
        """記錄指令使用"""
        guild_id_str = str(guild_id)
        user_id_str = str(user_id)

        if guild_id_str not in self.analytics_data['command_usage']:
            self.analytics_data['command_usage'][guild_id_str] = {}

        if command_name not in self.analytics_data['command_usage'][guild_id_str]:
            self.analytics_data['command_usage'][guild_id_str][command_name] = {
                'total_uses': 0,
                'users': {}
            }

        cmd_data = self.analytics_data['command_usage'][guild_id_str][command_name]
        cmd_data['total_uses'] += 1

        if user_id_str not in cmd_data['users']:
            cmd_data['users'][user_id_str] = 0
        cmd_data['users'][user_id_str] += 1

        self.save_analytics_data()

    @commands.Cog.listener()
    async def on_message(self, message):
        """監聽訊息事件"""
        if message.author.bot:
            return

        self.record_message(
            message.guild.id if message.guild else 0,
            message.author.id,
            message.channel.id
        )
        await self.bot.process_commands(message)

    @commands.Cog.listener()
    async def on_app_command(self, interaction: discord.Interaction):
        """監聽斜線指令事件"""
        if interaction.guild:
            self.record_command(
                interaction.guild.id,
                interaction.user.id,
                interaction.command.name
            )

    @app_commands.command(name="伺服器統計", description="顯示伺服器統計資訊")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def server_stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            guild = interaction.guild
            guild_id_str = str(guild.id)
            
            # 獲取基本統計
            total_members = guild.member_count
            online_members = len([m for m in guild.members if m.status != discord.Status.offline])
            total_channels = len(guild.channels)
            total_roles = len(guild.roles)
            
            # 獲取訊息統計
            message_data = self.analytics_data.get('message_counts', {}).get(guild_id_str, {})
            total_messages = sum(message_data.values())
            
            # 獲取活躍用戶
            user_data = self.analytics_data.get('user_activity', {}).get(guild_id_str, {})
            active_users = len(user_data)

            # 純文字統計
            embed = discord.Embed(
                title=f"📊 {guild.name} 統計報告",
                color=discord.Color.blue()
            )
            embed.add_field(name="👥 成員", value=f"總數: {total_members}\n線上: {online_members}", inline=True)
            embed.add_field(name="📝 訊息", value=f"總數: {total_messages}\n活躍用戶: {active_users}", inline=True)
            embed.add_field(name="📊 頻道與角色", value=f"頻道: {total_channels}\n角色: {total_roles}", inline=True)

            # 近7天訊息趨勢
            dates = sorted(message_data.keys())[-7:]
            message_counts = [message_data.get(date, 0) for date in dates]
            if dates:
                trend = "\n".join([f"{date}: {count}" for date, count in zip(dates, message_counts)])
                embed.add_field(name="🗓️ 最近7天訊息趨勢", value=trend, inline=False)
            else:
                embed.add_field(name="🗓️ 最近7天訊息趨勢", value="無數據", inline=False)

            # 活躍用戶排行
            top_users = sorted(user_data.items(), key=lambda x: x[1]['message_count'], reverse=True)[:5]
            if top_users:
                leaderboard = []
                for i, (user_id, data) in enumerate(top_users, 1):
                    user = guild.get_member(int(user_id))
                    name = user.display_name if user else f"用戶{user_id}"
                    leaderboard.append(f"{i}. {name}: {data['message_count']} 訊息")
                embed.add_field(name="🏆 最活躍用戶", value="\n".join(leaderboard), inline=False)
            else:
                embed.add_field(name="🏆 最活躍用戶", value="無數據", inline=False)

            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"[server_stats] 伺服器統計失敗: {e}")
            await interaction.followup.send(f"❌ 生成統計報告失敗：{str(e)}", ephemeral=True)

    @app_commands.command(name="用戶分析", description="分析特定用戶的活動")
    @app_commands.describe(user="要分析的用戶")
    async def user_analysis(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer()
        
        guild_id_str = str(interaction.guild.id)
        user_id_str = str(user.id)
        
        user_data = self.analytics_data.get('user_activity', {}).get(guild_id_str, {}).get(user_id_str, {})
        
        if not user_data:
            await interaction.followup.send("❌ 沒有找到該用戶的活動數據", ephemeral=True)
            return
        
        # 獲取用戶統計
        message_count = user_data.get('message_count', 0)
        last_active = user_data.get('last_active')
        channels = user_data.get('channels', {})
        
        # 計算活躍度
        if last_active:
            last_active_dt = datetime.fromisoformat(last_active)
            days_since_active = (datetime.now() - last_active_dt).days
        else:
            days_since_active = "未知"
        
        # 最常使用的頻道
        top_channels = sorted(channels.items(), key=lambda x: x[1], reverse=True)[:3]
        channel_names = []
        for channel_id, count in top_channels:
            channel = interaction.guild.get_channel(int(channel_id))
            channel_names.append(f"{channel.name if channel else '未知頻道'}: {count} 訊息")
        
        # 純文字用戶分析
        embed = discord.Embed(
            title=f"👤 {user.display_name} 活動分析",
            color=discord.Color.green()
        )
        embed.add_field(name="📝 訊息統計", value=f"總訊息數: {message_count}", inline=True)
        embed.add_field(name="🕐 最後活躍", value=f"{days_since_active} 天前" if isinstance(days_since_active, int) else "未知", inline=True)
        embed.add_field(name="📺 使用頻道數", value=str(len(channels)), inline=True)
        if channel_names:
            embed.add_field(name="�� 最常使用頻道", value="\n".join(channel_names), inline=False)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="指令統計", description="顯示指令使用統計")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def command_stats(self, interaction: discord.Interaction):
        guild_id_str = str(interaction.guild.id)
        command_data = self.analytics_data.get('command_usage', {}).get(guild_id_str, {})
        
        if not command_data:
            await interaction.response.send_message("❌ 沒有指令使用數據", ephemeral=True)
            return
        
        # 排序指令
        sorted_commands = sorted(command_data.items(), key=lambda x: x[1]['total_uses'], reverse=True)
        
        embed = discord.Embed(
            title="📊 指令使用統計",
            description=f"伺服器: {interaction.guild.name}",
            color=discord.Color.purple()
        )
        
        for i, (command_name, data) in enumerate(sorted_commands[:10], 1):
            total_uses = data['total_uses']
            unique_users = len(data['users'])
            
            embed.add_field(
                name=f"{i}. /{command_name}",
                value=f"使用次數: {total_uses}\n使用用戶: {unique_users}",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="活躍度排行", description="顯示最活躍的用戶排行")
    async def activity_leaderboard(self, interaction: discord.Interaction):
        guild_id_str = str(interaction.guild.id)
        user_data = self.analytics_data.get('user_activity', {}).get(guild_id_str, {})
        
        if not user_data:
            await interaction.response.send_message("❌ 沒有用戶活動數據", ephemeral=True)
            return
        
        # 排序用戶
        sorted_users = sorted(user_data.items(), key=lambda x: x[1]['message_count'], reverse=True)
        
        embed = discord.Embed(
            title="🏆 活躍度排行榜",
            description=f"伺服器: {interaction.guild.name}",
            color=discord.Color.gold()
        )
        
        for i, (user_id, data) in enumerate(sorted_users[:10], 1):
            user = interaction.guild.get_member(int(user_id))
            username = user.display_name if user else f"用戶{user_id}"
            message_count = data['message_count']
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
            embed.add_field(
                name=f"{medal} {username}",
                value=f"📝 {message_count} 訊息",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Analytics(bot)) 