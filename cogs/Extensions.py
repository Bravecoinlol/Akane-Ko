from discord.ext import commands

class ExtensionManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command()
    async def load(self, ctx, extension):
        if f"cogs.{extension}" in self.bot.extensions:
            await ctx.send(f"{extension} 已經 loaded 了，無法再加載。")
            return
        try:
            await self.bot.load_extension(f"cogs.{extension}")
            await ctx.send(f"Loaded {extension} done.")
        except Exception as e:
            await ctx.send(f"Failed to load {extension}: {e}")

    @commands.is_owner()
    @commands.command()
    async def unload(self, ctx, extension):
        if f"cogs.{extension}" not in self.bot.extensions:
            await ctx.send(f"{extension} 尚未 loaded，無法卸載。")
            return
        try:
            await self.bot.unload_extension(f"cogs.{extension}")
            await ctx.send(f"Unloaded {extension} done.")
        except Exception as e:
            await ctx.send(f"Failed to unload {extension}: {e}")

    @commands.is_owner()
    @commands.command()
    async def reload(self, ctx, extension):
        try:
            await self.bot.unload_extension(f"cogs.{extension}")
            await self.bot.load_extension(f"cogs.{extension}")
            await ctx.send(f"Reloaded {extension} done.")
        except Exception as e:
            await ctx.send(f"Failed to reload {extension}: {e}")

async def setup(bot):
    # 防止重複註冊
    for name in ["load", "unload", "reload"]:
        if bot.get_command(name):
            bot.remove_command(name)
    await bot.add_cog(ExtensionManager(bot))
