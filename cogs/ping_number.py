import discord
from discord.ext import commands
import logging

logger = logging.getLogger('PingNumber')

class ping_number(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.command(name="ping") 
    async def ping_command(self, ctx):
        try:
            latency = round(self.bot.latency * 1000)
            
            # 根據延遲設定顏色
            if latency < 100:
                color = discord.Color.green()
                status = "🟢 優秀"
            elif latency < 200:
                color = discord.Color.yellow()
                status = "🟡 良好"
            elif latency < 500:
                color = discord.Color.orange()
                status = "🟠 一般"
            else:
                color = discord.Color.red()
                status = "🔴 較差"
            
            embed = discord.Embed(
                title="🏓 Pong!",
                description=f"延遲: **{latency}ms**\n狀態: {status}",
                color=color
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"[PingNumber] ping命令執行失敗: {e}")
            embed = discord.Embed(
                title="❌ 執行錯誤",
                description="無法獲取延遲資訊，請稍後再試",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
async def setup(bot):
    await bot.add_cog(ping_number(bot))