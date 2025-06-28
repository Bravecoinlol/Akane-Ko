import discord
from discord.ext import commands

class ping_number(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.command(name="ping") 
    async def ping_command(self, ctx):
        await ctx.send(f'{round(self.bot.latency * 1000)}[ms]')
    
async def setup(bot):
    await bot.add_cog(ping_number(bot))