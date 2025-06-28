import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os
from typing import Dict
import asyncio
import logging
from datetime import datetime, timedelta

# 設定 logger
logger = logging.getLogger('MiniGames')

LEADERBOARD_FILE = 'minigames_leaderboard.json'

class LeaderboardManager:
    def __init__(self, file_path=LEADERBOARD_FILE):
        self.file_path = file_path
        self.data = {
            'guess_number': {},  # user_id: win_count
            'rps': {},           # user_id: win_count
            'minesweeper': {},    # user_id: win_count
            'tictactoe': {}  # 新增
        }
        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception as e:
                logger.error(f"[Leaderboard] 載入失敗: {e}")
                self.data = {
                    'guess_number': {},
                    'rps': {},
                    'minesweeper': {},
                    'tictactoe': {}
                }

    def save(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"[Leaderboard] 儲存失敗: {e}")

    def add_win(self, game: str, user_id: int):
        game = game.lower()
        if game not in self.data:
            self.data[game] = {}
        uid = str(user_id)
        self.data[game][uid] = self.data[game].get(uid, 0) + 1
        self.save()

    def get_top(self, game: str, top_n=10) -> Dict[str, int]:
        game = game.lower()
        if game not in self.data:
            return {}
        return dict(sorted(self.data[game].items(), key=lambda x: x[1], reverse=True)[:top_n])

# 踩地雷邏輯類別
class MinesweeperGame:
    def __init__(self, size=5, bombs=5):
        self.size = size
        self.bombs = bombs
        self.board = [['⬜' for _ in range(size)] for _ in range(size)]
        self.visible = [[False for _ in range(size)] for _ in range(size)]
        self.bomb_locations = set()
        self._place_bombs()

    def _place_bombs(self):
        while len(self.bomb_locations) < self.bombs:
            x, y = random.randint(0, self.size - 1), random.randint(0, self.size - 1)
            self.bomb_locations.add((x, y))

    def is_bomb(self, x, y):
        return (x, y) in self.bomb_locations

    def reveal_cell(self, x, y):
        if self.visible[x][y]:
            return False
        self.visible[x][y] = True
        if self.is_bomb(x, y):
            self.board[x][y] = '💣'
            return True
        count = self._adjacent_bomb_count(x, y)
        self.board[x][y] = str(count) if count > 0 else '⬛'
        return False

    def _adjacent_bomb_count(self, x, y):
        count = 0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.size and 0 <= ny < self.size and (nx, ny) in self.bomb_locations:
                    count += 1
        return count

# 按鈕格子
class MinesweeperButton(discord.ui.Button):
    def __init__(self, x: int, y: int, game: MinesweeperGame, view: discord.ui.View):
        super().__init__(label="⬜", row=x, style=discord.ButtonStyle.secondary)
        self.x = x
        self.y = y
        self.game = game
        self.view = view

    async def callback(self, interaction: discord.Interaction):
        if self.view.game_over:
            await interaction.response.send_message("遊戲已經結束了喔～", ephemeral=True)
            return

        if self.game.reveal_cell(self.x, self.y):
            self.label = "💣"
            self.style = discord.ButtonStyle.danger
            self.view.game_over = True
            for item in self.view.children:
                if isinstance(item, MinesweeperButton):
                    cx, cy = item.x, item.y
                    if (cx, cy) in self.game.bomb_locations:
                        item.label = '💣'
                        item.style = discord.ButtonStyle.danger
                        item.disabled = True
            await interaction.response.edit_message(content="💥 你踩到地雷啦！遊戲結束！", view=self.view)
        else:
            count = self.game._adjacent_bomb_count(self.x, self.y)
            self.label = str(count) if count > 0 else '⬛'
            self.disabled = True
            self.style = discord.ButtonStyle.gray
            # 判斷是否破關
            if self._check_win():
                self.view.game_over = True
                # 記錄排行榜
                cog = interaction.client.get_cog("MiniGames")
                if cog and hasattr(cog, 'leaderboard_manager'):
                    cog.leaderboard_manager.add_win('minesweeper', interaction.user.id)
                await interaction.response.edit_message(content="🎉 恭喜你破關踩地雷！", view=self.view)
            else:
                await interaction.response.edit_message(view=self.view)

    def _check_win(self):
        # 沒有踩到地雷且所有非地雷格都被揭開
        for x in range(self.game.size):
            for y in range(self.game.size):
                if not self.game.is_bomb(x, y) and not self.game.visible[x][y]:
                    return False
        return True

class MinesweeperGameView(discord.ui.View):
    def __init__(self, game: MinesweeperGame):
        super().__init__(timeout=180)
        self.game = game
        self.game_over = False
        for x in range(game.size):
            for y in range(game.size):
                self.add_item(MinesweeperButton(x, y, game, self))

# 主小遊戲 Cog
class MiniGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guess_numbers = {}
        self.leaderboard_manager = LeaderboardManager()
        self.tictactoe_games = {}

    @app_commands.command(name="猜數字", description="開始一場猜數字遊戲")
    async def guess_number(self, interaction: discord.Interaction):
        number = random.randint(1, 100)
        self.guess_numbers[interaction.user.id] = number
        await interaction.response.send_message(f"{interaction.user.mention} 選好一個 1～100 的數字了，請直接輸入 `/猜 <數字>` 來猜喔！")

    @app_commands.command(name="猜", description="猜一個數字")
    @app_commands.describe(guess="你猜的數字")
    async def make_guess(self, interaction: discord.Interaction, guess: int):
        number = self.guess_numbers.get(interaction.user.id)
        if number is None:
            await interaction.response.send_message("你還沒開始猜數字遊戲喔！請先輸入 `/猜數字`。", ephemeral=True)
            return
        if guess == number:
            await interaction.response.send_message("🎉 恭喜你猜對了！")
            del self.guess_numbers[interaction.user.id]
            self.leaderboard_manager.add_win('guess_number', interaction.user.id)
        elif guess < number:
            await interaction.response.send_message("太小了！")
        else:
            await interaction.response.send_message("太大了！")

    @app_commands.command(name="剪刀石頭布", description="來場剪刀石頭布吧！")
    async def rps(self, interaction: discord.Interaction):
        view = RPSView()
        await interaction.response.send_message("請選擇你要出的：", view=view, ephemeral=True)

    @app_commands.command(name="圈圈叉叉", description="開始一場圈圈叉叉")
    @app_commands.describe(opponent="你要對戰的對手")
    async def tictactoe(self, interaction: discord.Interaction, opponent: discord.Member):
        if opponent.bot or opponent == interaction.user:
            await interaction.response.send_message("請選擇一個真實的對手（不能是你自己或機器人）！", ephemeral=True)
            return
        view = TicTacToeRequestView(interaction.user, opponent, self)
        await interaction.response.send_message(f"{opponent.mention}，{interaction.user.mention} 想和你來場圈圈叉叉，是否接受？", view=view)

    @app_commands.command(name="踩地雷", description="開始踩地雷遊戲（單人或對戰）")
    async def minesweeper_mode(self, interaction: discord.Interaction):
        view = MinesweeperModeView()
        await interaction.response.send_message("請選擇遊戲模式：", view=view, ephemeral=True)

    @app_commands.command(name="猜數字排行", description="猜數字排行榜（前10名）")
    async def guess_number_leaderboard(self, interaction: discord.Interaction):
        top = self.leaderboard_manager.get_top('guess_number')
        if not top:
            await interaction.response.send_message("目前還沒有任何猜數字紀錄！", ephemeral=True)
            return
        embed = discord.Embed(title="猜數字排行榜（前10名）", color=discord.Color.gold())
        for idx, (uid, count) in enumerate(top.items(), 1):
            user = await self.bot.fetch_user(int(uid))
            embed.add_field(name=f"#{idx} {user.display_name}", value=f"勝場：{count}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="剪刀石頭布排行", description="剪刀石頭布排行榜（前10名）")
    async def rps_leaderboard(self, interaction: discord.Interaction):
        top = self.leaderboard_manager.get_top('rps')
        if not top:
            await interaction.response.send_message("目前還沒有任何剪刀石頭布紀錄！", ephemeral=True)
            return
        embed = discord.Embed(title="剪刀石頭布排行榜（前10名）", color=discord.Color.blue())
        for idx, (uid, count) in enumerate(top.items(), 1):
            user = await self.bot.fetch_user(int(uid))
            embed.add_field(name=f"#{idx} {user.display_name}", value=f"勝場：{count}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="踩地雷排行", description="踩地雷排行榜（前10名）")
    async def minesweeper_leaderboard(self, interaction: discord.Interaction):
        top = self.leaderboard_manager.get_top('minesweeper')
        if not top:
            await interaction.response.send_message("目前還沒有任何踩地雷紀錄！", ephemeral=True)
            return
        embed = discord.Embed(title="踩地雷排行榜（前10名）", color=discord.Color.green())
        for idx, (uid, count) in enumerate(top.items(), 1):
            user = await self.bot.fetch_user(int(uid))
            embed.add_field(name=f"#{idx} {user.display_name}", value=f"破關次數：{count}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class RPSView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=15)

    @discord.ui.button(label="剪刀", emoji="✂️", style=discord.ButtonStyle.primary)
    async def scissor(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.resolve(interaction, "剪刀")

    @discord.ui.button(label="石頭", emoji="✊", style=discord.ButtonStyle.success)
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.resolve(interaction, "石頭")

    @discord.ui.button(label="布", emoji="✋", style=discord.ButtonStyle.danger)
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.resolve(interaction, "布")

    async def resolve(self, interaction: discord.Interaction, user_choice: str):
        choices = ["剪刀", "石頭", "布"]
        bot_choice = random.choice(choices)
        result = get_rps_result(user_choice, bot_choice)
        if result == "你贏了！":
            cog = interaction.client.get_cog("MiniGames")
            if cog and hasattr(cog, 'leaderboard_manager'):
                cog.leaderboard_manager.add_win('rps', interaction.user.id)
        await interaction.response.edit_message(content=f"你出的是：{user_choice}，我出的是：{bot_choice}，結果：{result}", view=None)

class TicTacToeRequestView(discord.ui.View):
    def __init__(self, challenger: discord.User, opponent: discord.User, cog):
        super().__init__(timeout=30)
        self.challenger = challenger
        self.opponent = opponent
        self.cog = cog
        self.message = None

    async def on_timeout(self):
        if self.message:
            for child in self.children:
                child.disabled = True
            await self.message.edit(content="⌛ 挑戰逾時未回應，取消對戰！", view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True

    @discord.ui.button(label="接受挑戰", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.opponent:
            await interaction.response.send_message("這不是你要接受的挑戰喔～", ephemeral=True)
            return
        
        # 先回應互動，避免交互失敗
        await interaction.response.defer()
        
        # 禁用所有按鈕
        for child in self.children:
            child.disabled = True
        
        # 啟動 TicTacToeGameView
        view = TicTacToeGameView(self.challenger, self.opponent, self.cog)
        
        try:
            # 嘗試編輯原始訊息
            await interaction.message.edit(content=f"比賽開始！{self.challenger.mention} (⭕) 對上 {self.opponent.mention} (❌)\n請 {self.challenger.mention} 先下棋！", view=view)
            view.message = interaction.message
        except Exception as e:
            # 如果編輯失敗，發送新訊息
            logger.error(f"[TicTacToe] 編輯訊息失敗: {e}")
            new_msg = await interaction.followup.send(content=f"比賽開始！{self.challenger.mention} (⭕) 對上 {self.opponent.mention} (❌)\n請 {self.challenger.mention} 先下棋！", view=view)
            view.message = new_msg
        
        # 記錄遊戲
        key = tuple(sorted([self.challenger.id, self.opponent.id]))
        self.cog.tictactoe_games[key] = view

    @discord.ui.button(label="拒絕挑戰", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.opponent:
            await interaction.response.send_message("這不是你要拒絕的挑戰喔～", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content=f"{self.opponent.mention} 拒絕了 {self.challenger.mention} 的挑戰。", view=self)

class MinesweeperModeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        self.message = None

    async def on_timeout(self):
        if self.message:
            for child in self.children:
                child.disabled = True
            await self.message.edit(content="⏱️ 沒有選擇模式，已取消遊戲。", view=self)

    @discord.ui.button(label="單人模式", style=discord.ButtonStyle.primary)
    async def single_mode(self, interaction: discord.Interaction, button: discord.ui.Button):
        game = MinesweeperGame(size=5, bombs=5)
        view = MinesweeperGameView(game)

        # 使用 original_response() 取得訊息並編輯
        if self.message is None:
            self.message = await interaction.original_response()
        await self.message.edit(content="💣 開始遊戲！點擊格子揭曉內容：", view=view)

    @discord.ui.button(label="對戰模式", style=discord.ButtonStyle.success)
    async def versus_mode(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="⚔️ 對戰踩地雷模式尚未實作！", view=None)

class TicTacToeGameView(discord.ui.View):
    def __init__(self, player1, player2, cog):
        super().__init__(timeout=180)
        self.player1 = player1
        self.player2 = player2
        self.cog = cog
        self.board = [[None for _ in range(3)] for _ in range(3)]
        self.current = player1  # 先手
        self.message = None
        self.game_over = False
        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y, self))

    async def on_timeout(self):
        if self.message:
            try:
                for child in self.children:
                    child.disabled = True
                await self.message.edit(content="⌛ 對戰逾時未完成，遊戲結束！", view=self)
            except Exception as e:
                logger.error(f"[TicTacToe] 逾時處理失敗: {e}")
            self._cleanup()

    def _cleanup(self):
        key = tuple(sorted([self.player1.id, self.player2.id]))
        if key in self.cog.tictactoe_games:
            del self.cog.tictactoe_games[key]

    def check_win(self, symbol):
        # 橫、直、斜線判斷
        for i in range(3):
            if all(self.board[i][j] == symbol for j in range(3)):
                return True
            if all(self.board[j][i] == symbol for j in range(3)):
                return True
        if all(self.board[i][i] == symbol for i in range(3)):
            return True
        if all(self.board[i][2-i] == symbol for i in range(3)):
            return True
        return False

    def check_draw(self):
        return all(self.board[x][y] is not None for x in range(3) for y in range(3))

class TicTacToeButton(discord.ui.Button):
    def __init__(self, x, y, view):
        super().__init__(label=" ", row=x, style=discord.ButtonStyle.secondary)
        self.x = x
        self.y = y
        self.view = view

    async def callback(self, interaction: discord.Interaction):
        if self.view.game_over:
            await interaction.response.send_message("遊戲已經結束了喔～", ephemeral=True)
            return
        if interaction.user != self.view.current:
            await interaction.response.send_message("現在不是你的回合喔！", ephemeral=True)
            return
        
        symbol = "⭕" if self.view.current == self.view.player1 else "❌"
        self.label = symbol
        self.disabled = True
        self.style = discord.ButtonStyle.success if symbol == "⭕" else discord.ButtonStyle.danger
        self.view.board[self.x][self.y] = symbol
        
        # 勝負判斷
        if self.view.check_win(symbol):
            self.view.game_over = True
            for child in self.view.children:
                child.disabled = True
            # 記錄勝場
            winner = self.view.current
            if hasattr(self.view.cog, 'leaderboard_manager'):
                self.view.cog.leaderboard_manager.add_win('tictactoe', winner.id)
            
            try:
                await interaction.response.edit_message(content=f"🎉 {winner.mention} ({symbol}) 獲勝！", view=self.view)
            except Exception as e:
                logger.error(f"[TicTacToe] 獲勝訊息編輯失敗: {e}")
                await interaction.response.send_message(f"🎉 {winner.mention} ({symbol}) 獲勝！", ephemeral=True)
            
            self.view._cleanup()
        elif self.view.check_draw():
            self.view.game_over = True
            for child in self.view.children:
                child.disabled = True
            
            try:
                await interaction.response.edit_message(content="🤝 平手！", view=self.view)
            except Exception as e:
                logger.error(f"[TicTacToe] 平手訊息編輯失敗: {e}")
                await interaction.response.send_message("🤝 平手！", ephemeral=True)
            
            self.view._cleanup()
        else:
            # 換人
            self.view.current = self.view.player2 if self.view.current == self.view.player1 else self.view.player1
            
            try:
                await interaction.response.edit_message(content=f"請 {self.view.current.mention} 下棋！", view=self.view)
            except Exception as e:
                logger.error(f"[TicTacToe] 換人訊息編輯失敗: {e}")
                await interaction.response.send_message(f"請 {self.view.current.mention} 下棋！", ephemeral=True)

def get_rps_result(user, bot):
    if user == bot:
        return "平手"
    if (user, bot) in [("剪刀", "布"), ("布", "石頭"), ("石頭", "剪刀")]:
        return "你贏了！"
    return "你輸了～"

async def setup(bot):
    await bot.add_cog(MiniGames(bot))
