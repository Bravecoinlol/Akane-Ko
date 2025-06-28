import discord
import random
import json
import os
import asyncio
from discord.ext import commands
from random import sample
from discord import app_commands
from discord import Interaction


class HelpView(discord.ui.View):
    def __init__(self, pages, author: discord.User):
        super().__init__(timeout=60)
        self.pages = pages
        self.page = 0
        self.author = author
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        self.add_item(self.PrevButton(self))
        self.add_item(self.NextButton(self))

    class PrevButton(discord.ui.Button):
        def __init__(self, view):
            super().__init__(style=discord.ButtonStyle.primary, label="上一頁", row=0)
            self.view_ref = view
        async def callback(self, interaction: discord.Interaction):
            if interaction.user != self.view_ref.author:
                await interaction.response.send_message("只能由發起者操作分頁！", ephemeral=True)
                return
            self.view_ref.page = (self.view_ref.page - 1) % len(self.view_ref.pages)
            await interaction.response.edit_message(embed=self.view_ref.pages[self.view_ref.page], view=self.view_ref)

    class NextButton(discord.ui.Button):
        def __init__(self, view):
            super().__init__(style=discord.ButtonStyle.primary, label="下一頁", row=0)
            self.view_ref = view
        async def callback(self, interaction: discord.Interaction):
            if interaction.user != self.view_ref.author:
                await interaction.response.send_message("只能由發起者操作分頁！", ephemeral=True)
                return
            self.view_ref.page = (self.view_ref.page + 1) % len(self.view_ref.pages)
            await interaction.response.edit_message(embed=self.view_ref.pages[self.view_ref.page], view=self.view_ref)

class slash(commands.Cog):
    def __init__(self,bot:commands.bot):
        self.bot = bot
    
    @app_commands.command(name = "hello_mtfk", description = "來罵機器人髒話吧!!!!")
    async def hello_mtfk(self, interaction: discord.Interaction):
        await interaction.response.send_message("X 你有毛病吧?")

    @app_commands.command(name = "how_to_start",description = "指令好多 該先從什麼開始?")
    async def How_To_Start(self, interaction: discord.Interaction):
        await interaction.response.send_message("你可以先跟我打招呼❤️")

    # 分頁內容
    def get_help_pages(self):
        pages = []
        # ========== 常用指令 ==========
        embed = discord.Embed(title="📚 幫助指令列表 - 常用指令", color=discord.Color.blue())
        embed.add_field(name="/help", value="顯示此幫助訊息", inline=False)
        embed.add_field(name="/hello_mtfk", value="你可以罵機器人髒話 然後他就會罵回去", inline=False)
        embed.add_field(name="/how_to_start", value="不知道怎麼開始用?可以用這個指令!", inline=False)
        pages.append(embed)
        
        # ========== 進階遊戲系統 ==========
        embed = discord.Embed(title="📚 幫助指令列表 - 進階遊戲系統", color=discord.Color.green())
        embed.add_field(name="/每日簽到", value="每日簽到獲得金幣", inline=False)
        embed.add_field(name="/餘額", value="查看你的金幣餘額", inline=False)
        embed.add_field(name="/轉帳", value="轉帳給其他用戶", inline=False)
        embed.add_field(name="/賭博", value="賭博遊戲 - 猜大小", inline=False)
        embed.add_field(name="/排行榜", value="查看金幣排行榜", inline=False)
        embed.add_field(name="/工作", value="工作賺取金幣", inline=False)
        pages.append(embed)
        
        # ========== 圖片工具 ==========
        embed = discord.Embed(title="📚 幫助指令列表 - 圖片工具", color=discord.Color.purple())
        embed.add_field(name="/頭像", value="顯示用戶的頭像", inline=False)
        embed.add_field(name="/頭像效果", value="為頭像添加特效（模糊、銳化、黑白等）", inline=False)
        embed.add_field(name="/迷因生成", value="生成迷因圖片", inline=False)
        embed.add_field(name="/圖片資訊", value="顯示圖片的基本資訊", inline=False)
        pages.append(embed)
        
        # ========== 實用工具 ==========
        embed = discord.Embed(title="📚 幫助指令列表 - 實用工具", color=discord.Color.orange())
        embed.add_field(name="/translate", value="翻譯文字（支援多種語言）", inline=False)
        embed.add_field(name="/weather", value="查詢天氣資訊", inline=False)
        embed.add_field(name="/calculator", value="簡單的數學計算", inline=False)
        embed.add_field(name="/random", value="生成隨機數字", inline=False)
        embed.add_field(name="/time", value="顯示當前時間", inline=False)
        embed.add_field(name="/countdown", value="設定倒數計時器", inline=False)
        embed.add_field(name="/qrcode", value="生成 QR 碼", inline=False)
        embed.add_field(name="/password", value="生成隨機密碼", inline=False)
        pages.append(embed)
        
        # ========== 基礎遊戲/互動 ==========
        embed = discord.Embed(title="📚 幫助指令列表 - 基礎遊戲/互動", color=discord.Color.teal())
        embed.add_field(name="/猜數字", value="開始一場猜數字遊戲", inline=False)
        embed.add_field(name="/猜", value="猜一個數字", inline=False)
        embed.add_field(name="/剪刀石頭布", value="來場剪刀石頭布吧！", inline=False)
        embed.add_field(name="/圈圈叉叉", value="開始一場圈圈叉叉", inline=False)
        embed.add_field(name="/踩地雷", value="開始踩地雷遊戲（單人或對戰）", inline=False)
        pages.append(embed)
        
        # ========== 排行榜 ==========
        embed = discord.Embed(title="📚 幫助指令列表 - 排行榜", color=discord.Color.gold())
        embed.add_field(name="/猜數字排行", value="猜數字排行榜（前10名）", inline=False)
        embed.add_field(name="/剪刀石頭布排行", value="剪刀石頭布排行榜（前10名）", inline=False)
        embed.add_field(name="/踩地雷排行", value="踩地雷排行榜（前10名）", inline=False)
        pages.append(embed)
        
        # ========== 金幣/問題 ==========
        embed = discord.Embed(title="📚 幫助指令列表 - 金幣/問題", color=discord.Color.dark_gold())
        embed.add_field(name="/coin", value="查看自己的金幣餘額", inline=False)
        embed.add_field(name="/question", value="設定一個問題並提供答案和獎勳金幣", inline=False)
        embed.add_field(name="/give", value="將自己的金幣轉給其他人", inline=False)
        embed.add_field(name="/clean_coin", value="清空金幣數量（管理員限定）", inline=False)
        pages.append(embed)
        
        # ========== 音樂 ==========
        embed = discord.Embed(title="📚 幫助指令列表 - 音樂", color=discord.Color.dark_purple())
        embed.add_field(name="/play", value="播放音樂 (支援連結與關鍵字)", inline=False)
        embed.add_field(name="/volume", value="設定音量 (1-100)", inline=False)
        embed.add_field(name="/pause", value="暫停播放", inline=False)
        embed.add_field(name="/resume", value="繼續播放", inline=False)
        embed.add_field(name="/skip", value="跳到下一首", inline=False)
        embed.add_field(name="/repeat", value="切換重複播放", inline=False)
        embed.add_field(name="/queue", value="顯示播放隊列", inline=False)
        embed.add_field(name="/clear", value="清空播放隊列", inline=False)
        embed.add_field(name="/autoplay", value="設定自動串流類別並立即加入歌曲", inline=False)
        embed.add_field(name="/join", value="讓機器人加入你所在的語音頻道", inline=False)
        embed.add_field(name="/leave", value="讓機器人離開語音頻道", inline=False)
        embed.add_field(name="/nowplaying", value="顯示目前正在播放的音樂", inline=False)
        embed.add_field(name="/reset", value="重置音樂系統狀態（管理員限定）", inline=False)
        embed.add_field(name="/status", value="顯示音樂系統狀態", inline=False)
        embed.add_field(name="/reload_ffmpeg", value="重新載入 FFmpeg 配置（管理員限定）", inline=False)
        pages.append(embed)
        
        # ========== 防護/管理 ==========
        embed = discord.Embed(title="📚 幫助指令列表 - 防護/管理", color=discord.Color.red())
        embed.add_field(name="/antiraid", value="防炸群系統控制（管理員限定）", inline=False)
        embed.add_field(name="/add_profanity", value="新增不雅字詞（管理員限定）", inline=False)
        embed.add_field(name="/remove_profanity", value="移除不雅字詞（管理員限定）", inline=False)
        embed.add_field(name="/list_profanity", value="列出所有不雅字詞（管理員限定）", inline=False)
        embed.add_field(name="/reset_warnings", value="重置用戶警告次數（管理員限定）", inline=False)
        embed.add_field(name="/setchannel", value="設定歡迎/離開頻道或管理頻道（管理員限定）", inline=False)
        embed.add_field(name="/setautorole", value="新增要自動分配的角色（管理員限定）", inline=False)
        embed.add_field(name="/removeautorole", value="從自動分配清單中移除角色（管理員限定）", inline=False)
        embed.add_field(name="/toggleautorole", value="啟用或停用自動分配角色（管理員限定）", inline=False)
        embed.add_field(name="/listautorole", value="顯示目前自動分配的角色清單（管理員限定）", inline=False)
        embed.add_field(name="/togglewelcomecard", value="啟用或停用歡迎卡片（管理員限定）", inline=False)
        pages.append(embed)
        
        # ========== 無前綴指令回復 ==========
        embed = discord.Embed(title="📚 幫助指令列表 - 無前綴指令回復", color=discord.Color.dark_teal())
        embed.add_field(name="hello", value="Hello~ 我是一個日本女高中生 今年17 請多多指教❤️", inline=False)
        embed.add_field(name="機器人是gay", value="閉嘴啦 Gay佬", inline=False)
        embed.add_field(name="成功了 we did it", value="成功了 Ya", inline=False)
        embed.add_field(name="跨沙小 我要shampoo", value="Yea then you got kicked out(Yea然後你就被踢出去了)", inline=False)
        embed.add_field(name="www(w要3個以上)", value="wwwww", inline=False)
        embed.add_field(name="我愛妳", value="我也愛你", inline=False)
        embed.add_field(name="我討厭妳", value="謝謝你的討厭 祝你找到更討厭的人", inline=False)
        embed.add_field(name="我or他選一個", value="[隨機取數(1/5機率)] \n1.:當然是妳啊 老公❤️ \n2.:還是他比較好 你算了吧", inline=False)
        embed.add_field(name="當我老婆", value="[隨機取數(1/2機率)] \n1.:好❤️ \n2.:不要 噁男", inline=False)
        embed.add_field(name="你願意嫁給我嗎", value="[隨機取數(1/2機率)] \n1.:好 我願意❤️ \n2.:(遞給你一張好人卡 表示拒絕)", inline=False)
        embed.add_field(name="(當你Ping機器人時)", value="[隨機取數(5中擇1)] \n1.:請問有什麼事嗎 老公❤️ \n2.:幹你娘勒 Ping我衝三小 \n3. :? \n4. :哈....哈.....找我有什麼事嗎❤️❤️❤️❤️ \n5. :マスター、私に何があったのですか？(主人，您找我有什麼事嗎?)", inline=False)
        embed.add_field(name="跨沙小 我要Shampoo", value="Yea then you got kicked out(Yea然後你就被踢出去了)", inline=False)
        embed.set_footer(text="感謝您使用本機器人！希望您會喜歡! **Made By BruhLu**")
        pages.append(embed)
        return pages

    @discord.app_commands.command(name="help", description="顯示所有可以用的指令")
    async def help_command(self, interaction: discord.Interaction):
        pages = self.get_help_pages()
        view = HelpView(pages, interaction.user)
        await interaction.response.send_message(embed=pages[0], view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(slash(bot))