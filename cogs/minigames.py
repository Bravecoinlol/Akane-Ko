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
        try:
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
        except Exception as e:
            logger.error(f"[MinesweeperButton] 回調處理失敗: {e}")
            try:
                await interaction.response.send_message("❌ 處理踩地雷時發生錯誤，請重試", ephemeral=True)
            except:
                pass

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

    async def on_timeout(self):
        try:
            for child in self.children:
                child.disabled = True
            logger.info(f"[MinesweeperGameView] 遊戲超時，已結束")
        except Exception as e:
            logger.error(f"[MinesweeperGameView] 超時處理失敗: {e}")

# 主小遊戲 Cog
class MiniGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guess_numbers = {}  # 存儲用戶的數字
        self.custom_numbers = {}  # 存儲自定義數字遊戲
        self.leaderboard_manager = LeaderboardManager()
        self.tictactoe_games = {}

    @app_commands.command(name="猜數字", description="開始一場猜數字遊戲")
    @app_commands.describe(mode="選擇遊戲模式")
    @app_commands.choices(mode=[
        app_commands.Choice(name="隨機數字 (1-100)", value="random"),
        app_commands.Choice(name="自定義數字", value="custom")
    ])
    async def guess_number(self, interaction: discord.Interaction, mode: app_commands.Choice[str] = None):
        try:
            if mode is None or mode.value == "random":
                # 隨機數字模式
                number = random.randint(1, 100)
                self.guess_numbers[interaction.user.id] = number
                
                embed = discord.Embed(
                    title="🎲 猜數字遊戲開始！",
                    description="我已經想好了一個 1-100 之間的數字",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="遊戲規則",
                    value="• 回覆這則訊息並輸入你猜的數字\n• 我會告訴你猜的數字是太大還是太小\n• 猜對就贏了！",
                    inline=False
                )
                embed.add_field(
                    name="開始猜測",
                    value="請回覆這則訊息並輸入你的猜測數字",
                    inline=False
                )
                embed.set_footer(text="遊戲會持續到猜對為止")
                
                await interaction.response.send_message(embed=embed)
                
            elif mode.value == "custom":
                # 自定義數字模式
                if interaction.channel.id in self.custom_numbers:
                    await interaction.response.send_message("❌ 此頻道已有進行中的自定義猜數字遊戲！", ephemeral=True)
                    return
                
                view = CustomNumberView(interaction.user, self)
                embed = discord.Embed(
                    title="🎯 自定義猜數字遊戲",
                    description="請選擇數字範圍，然後設定正確答案",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="遊戲設定",
                    value="• 選擇數字範圍\n• 設定正確答案\n• 其他玩家可以猜測",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                
        except Exception as e:
            logger.error(f"[guess_number] 開始猜數字遊戲失敗: {e}")
            try:
                embed = discord.Embed(
                    title="❌ 遊戲啟動失敗",
                    description="開始猜數字遊戲時發生錯誤",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="錯誤詳情",
                    value=str(e)[:100] + "..." if len(str(e)) > 100 else str(e),
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                logger.error(f"[guess_number] 無法發送錯誤訊息: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """監聽訊息來處理猜數字遊戲"""
        logger.info(f"[on_message] 收到訊息: {message.content}, author: {message.author}, reference: {message.reference}")
        try:
            # 忽略 Bot 訊息
            if message.author.bot:
                logger.info("[on_message] 忽略 bot 訊息")
                return
            # 檢查是否為回覆訊息
            if not message.reference:
                logger.info("[on_message] 非回覆訊息，忽略")
                return
            # 獲取被回覆的訊息
            try:
                replied_message = await message.channel.fetch_message(message.reference.message_id)
            except Exception as e:
                logger.info(f"[on_message] 無法取得被回覆訊息: {e}")
                return
            # 檢查被回覆的訊息是否為 Bot 的猜數字遊戲訊息
            if replied_message.author.id != self.bot.user.id:
                logger.info("[on_message] 被回覆訊息不是 bot 發的，忽略")
                return
            # 嘗試解析數字
            try:
                guess = int(message.content.strip())
            except ValueError:
                logger.info("[on_message] 輸入不是有效數字")
                embed = discord.Embed(
                    title="❌ 無效輸入",
                    description="請輸入一個有效的數字",
                    color=discord.Color.red()
                )
                await message.reply(embed=embed, mention_author=False)
                return
            # 處理猜數字邏輯
            logger.info(f"[on_message] 進入猜數字邏輯，guess={guess}")
            await self.process_guess(message, guess, replied_message)
        except Exception as e:
            logger.error(f"[on_message] 處理猜數字回覆失敗: {e}")
            try:
                embed = discord.Embed(
                    title="❌ 處理失敗",
                    description="處理猜數字時發生錯誤",
                    color=discord.Color.red()
                )
                await message.reply(embed=embed, mention_author=False)
            except:
                pass
        await self.bot.process_commands(message)

    async def process_guess(self, message, guess, game_message):
        """處理猜數字邏輯"""
        try:
            # 檢查是否在自定義數字遊戲中
            custom_game = self.custom_numbers.get(message.channel.id)
            if custom_game:
                number = custom_game['number']
                if guess == number:
                    embed = discord.Embed(
                        title="🎉 恭喜猜對了！",
                        description=f"**{message.author.mention}** 猜對了！正確答案是：**{number}**",
                        color=discord.Color.green()
                    )
                    embed.add_field(
                        name="遊戲結束",
                        value="自定義猜數字遊戲已結束",
                        inline=False
                    )
                    embed.set_footer(text=f"獲勝者: {message.author.display_name}")
                    del self.custom_numbers[message.channel.id]
                    await message.reply(embed=embed, mention_author=False)
                    return
                elif guess < number:
                    embed = discord.Embed(
                        title="📈 太小了！",
                        description=f"**{message.author.mention}** 猜的 **{guess}** 太小了",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="提示",
                        value="試試更大的數字",
                        inline=False
                    )
                    await message.reply(embed=embed, mention_author=False)
                    return
                else:
                    embed = discord.Embed(
                        title="📉 太大了！",
                        description=f"**{message.author.mention}** 猜的 **{guess}** 太大了",
                        color=discord.Color.orange()
                    )
                    embed.add_field(
                        name="提示",
                        value="試試更小的數字",
                        inline=False
                    )
                    await message.reply(embed=embed, mention_author=False)
                    return

            # 檢查是否在個人隨機數字遊戲中
            if message.author.id not in self.guess_numbers:
                embed = discord.Embed(
                    title="❌ 沒有進行中的遊戲",
                    description="請先使用 `/猜數字` 開始遊戲",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="如何開始",
                    value="使用 `/猜數字` 命令開始新的遊戲",
                    inline=False
                )
                await message.reply(embed=embed, mention_author=False)
                return

            number = self.guess_numbers[message.author.id]
            
            # 檢查猜測範圍
            if guess < 1 or guess > 100:
                embed = discord.Embed(
                    title="❌ 數字範圍錯誤",
                    description="請猜測 1-100 之間的數字",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="正確範圍",
                    value="1 到 100 之間的整數",
                    inline=False
                )
                await message.reply(embed=embed, mention_author=False)
                return
        
            if guess == number:
                embed = discord.Embed(
                    title="🎉 恭喜你猜對了！",
                    description=f"**{message.author.mention}** 猜對了！正確答案是：**{number}**",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="遊戲結束",
                    value="猜數字遊戲已結束",
                    inline=False
                )
                embed.set_footer(text=f"獲勝者: {message.author.display_name}")
                del self.guess_numbers[message.author.id]
                self.leaderboard_manager.add_win('guess_number', message.author.id)
                await message.reply(embed=embed, mention_author=False)
            elif guess < number:
                embed = discord.Embed(
                    title="📈 太小了！",
                    description=f"**{message.author.mention}** 猜的 **{guess}** 太小了",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="提示",
                    value="試試更大的數字",
                    inline=False
                )
                await message.reply(embed=embed, mention_author=False)
            else:
                embed = discord.Embed(
                    title="📉 太大了！",
                    description=f"**{message.author.mention}** 猜的 **{guess}** 太大了",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="提示",
                    value="試試更小的數字",
                    inline=False
                )
                await message.reply(embed=embed, mention_author=False)
                
        except Exception as e:
            logger.error(f"[process_guess] 處理猜數字失敗: {e}")
            try:
                embed = discord.Embed(
                    title="❌ 處理失敗",
                    description="處理猜數字時發生錯誤",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="錯誤詳情",
                    value=str(e)[:100] + "..." if len(str(e)) > 100 else str(e),
                    inline=False
                )
                await message.reply(embed=embed, mention_author=False)
            except:
                pass

    @app_commands.command(name="結束猜數字", description="結束當前的自定義猜數字遊戲")
    async def end_guess_number(self, interaction: discord.Interaction):
        custom_game = self.custom_numbers.get(interaction.channel.id)
        if not custom_game:
            await interaction.response.send_message("目前沒有進行中的自定義猜數字遊戲！", ephemeral=True)
            return
        
        if custom_game['host'] != interaction.user.id:
            await interaction.response.send_message("只有遊戲主持人才能結束遊戲！", ephemeral=True)
            return
        
        number = custom_game['number']
        del self.custom_numbers[interaction.channel.id]
        await interaction.response.send_message(f"遊戲已結束！正確答案是：{number}")

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
        try:
            top = self.leaderboard_manager.get_top('guess_number')
            if not top:
                embed = discord.Embed(
                    title="📊 猜數字排行榜",
                    description="目前還沒有任何猜數字紀錄！",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="💡 提示",
                    value="開始玩猜數字遊戲來獲得紀錄吧！",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(title="📊 猜數字排行榜（前10名）", color=discord.Color.gold())
            for idx, (uid, count) in enumerate(top.items(), 1):
                try:
                    user = await self.bot.fetch_user(int(uid))
                    embed.add_field(name=f"#{idx} {user.display_name}", value=f"勝場：{count}", inline=False)
                except discord.NotFound:
                    embed.add_field(name=f"#{idx} 未知用戶", value=f"勝場：{count} (用戶已刪除)", inline=False)
                except Exception as e:
                    logger.error(f"獲取用戶資訊失敗: {e}")
                    embed.add_field(name=f"#{idx} 載入失敗", value=f"勝場：{count}", inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"顯示猜數字排行榜失敗: {e}")
            await interaction.response.send_message(f"❌ 載入排行榜失敗：{str(e)}", ephemeral=True)

    @app_commands.command(name="剪刀石頭布排行", description="剪刀石頭布排行榜（前10名）")
    async def rps_leaderboard(self, interaction: discord.Interaction):
        try:
            top = self.leaderboard_manager.get_top('rps')
            if not top:
                embed = discord.Embed(
                    title="📊 剪刀石頭布排行榜",
                    description="目前還沒有任何剪刀石頭布紀錄！",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="💡 提示",
                    value="開始玩剪刀石頭布來獲得紀錄吧！",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(title="📊 剪刀石頭布排行榜（前10名）", color=discord.Color.blue())
            for idx, (uid, count) in enumerate(top.items(), 1):
                try:
                    user = await self.bot.fetch_user(int(uid))
                    embed.add_field(name=f"#{idx} {user.display_name}", value=f"勝場：{count}", inline=False)
                except discord.NotFound:
                    embed.add_field(name=f"#{idx} 未知用戶", value=f"勝場：{count} (用戶已刪除)", inline=False)
                except Exception as e:
                    logger.error(f"獲取用戶資訊失敗: {e}")
                    embed.add_field(name=f"#{idx} 載入失敗", value=f"勝場：{count}", inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"顯示剪刀石頭布排行榜失敗: {e}")
            await interaction.response.send_message(f"❌ 載入排行榜失敗：{str(e)}", ephemeral=True)

    @app_commands.command(name="踩地雷排行", description="踩地雷排行榜（前10名）")
    async def minesweeper_leaderboard(self, interaction: discord.Interaction):
        try:
            top = self.leaderboard_manager.get_top('minesweeper')
            if not top:
                embed = discord.Embed(
                    title="📊 踩地雷排行榜",
                    description="目前還沒有任何踩地雷紀錄！",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="💡 提示",
                    value="開始玩踩地雷來獲得紀錄吧！",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(title="📊 踩地雷排行榜（前10名）", color=discord.Color.green())
            for idx, (uid, count) in enumerate(top.items(), 1):
                try:
                    user = await self.bot.fetch_user(int(uid))
                    embed.add_field(name=f"#{idx} {user.display_name}", value=f"破關次數：{count}", inline=False)
                except discord.NotFound:
                    embed.add_field(name=f"#{idx} 未知用戶", value=f"破關次數：{count} (用戶已刪除)", inline=False)
                except Exception as e:
                    logger.error(f"獲取用戶資訊失敗: {e}")
                    embed.add_field(name=f"#{idx} 載入失敗", value=f"破關次數：{count}", inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"顯示踩地雷排行榜失敗: {e}")
            await interaction.response.send_message(f"❌ 載入排行榜失敗：{str(e)}", ephemeral=True)

class RPSView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=15)

    @discord.ui.button(label="剪刀", emoji="✂️", style=discord.ButtonStyle.primary)
    async def scissor(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.resolve(interaction, "剪刀")
        except Exception as e:
            logger.error(f"[RPSView] 剪刀選擇失敗: {e}")
            try:
                await interaction.response.send_message("❌ 選擇剪刀時發生錯誤，請重試", ephemeral=True)
            except:
                pass

    @discord.ui.button(label="石頭", emoji="✊", style=discord.ButtonStyle.success)
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.resolve(interaction, "石頭")
        except Exception as e:
            logger.error(f"[RPSView] 石頭選擇失敗: {e}")
            try:
                await interaction.response.send_message("❌ 選擇石頭時發生錯誤，請重試", ephemeral=True)
            except:
                pass

    @discord.ui.button(label="布", emoji="✋", style=discord.ButtonStyle.danger)
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.resolve(interaction, "布")
        except Exception as e:
            logger.error(f"[RPSView] 布選擇失敗: {e}")
            try:
                await interaction.response.send_message("❌ 選擇布時發生錯誤，請重試", ephemeral=True)
            except:
                pass

    async def resolve(self, interaction: discord.Interaction, user_choice: str):
        try:
            choices = ["剪刀", "石頭", "布"]
            bot_choice = random.choice(choices)
            result = get_rps_result(user_choice, bot_choice)
            if result == "你贏了！":
                cog = interaction.client.get_cog("MiniGames")
                if cog and hasattr(cog, 'leaderboard_manager'):
                    cog.leaderboard_manager.add_win('rps', interaction.user.id)
            await interaction.response.edit_message(content=f"你出的是：{user_choice}，我出的是：{bot_choice}，結果：{result}", view=None)
        except Exception as e:
            logger.error(f"[RPSView] 處理剪刀石頭布失敗: {e}")
            try:
                await interaction.response.send_message("❌ 處理剪刀石頭布時發生錯誤，請重試", ephemeral=True)
            except:
                pass

class TicTacToeRequestView(discord.ui.View):
    def __init__(self, challenger: discord.User, opponent: discord.User, cog):
        super().__init__(timeout=30)
        self.challenger = challenger
        self.opponent = opponent
        self.cog = cog

    async def on_timeout(self):
        try:
            for child in self.children:
                child.disabled = True
            logger.info(f"[TicTacToeRequestView] 挑戰逾時未回應，取消對戰")
        except Exception as e:
            logger.error(f"[TicTacToeRequestView] 超時處理失敗: {e}")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True

    @discord.ui.button(label="接受挑戰", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.opponent:
            await interaction.response.send_message("❌ 這不是你要接受的挑戰喔～", ephemeral=True)
            return
        
        try:
            # 先回應互動，避免交互失敗
            await interaction.response.defer()
            
            # 禁用所有按鈕
            for child in self.children:
                child.disabled = True
            
            # 啟動 TicTacToeGameView
            view = TicTacToeGameView(self.challenger, self.opponent, self.cog)
            
            try:
                # 嘗試編輯原始訊息
                await interaction.message.edit(content=f"🎮 比賽開始！{self.challenger.mention} (⭕) 對上 {self.opponent.mention} (❌)\n請 {self.challenger.mention} 先下棋！", view=view)
            except discord.Forbidden:
                # 如果沒有編輯權限，發送新訊息
                logger.warning(f"[TicTacToe] 沒有編輯訊息權限")
                await interaction.followup.send(content=f"🎮 比賽開始！{self.challenger.mention} (⭕) 對上 {self.opponent.mention} (❌)\n請 {self.challenger.mention} 先下棋！", view=view)
            except discord.HTTPException as e:
                # 如果編輯失敗，發送新訊息
                logger.error(f"[TicTacToe] 編輯訊息失敗: {e}")
                try:
                    await interaction.followup.send(content=f"🎮 比賽開始！{self.challenger.mention} (⭕) 對上 {self.opponent.mention} (❌)\n請 {self.challenger.mention} 先下棋！", view=view)
                except:
                    pass
            except Exception as e:
                logger.error(f"[TicTacToe] 未知錯誤: {e}")
                try:
                    await interaction.followup.send("❌ 啟動遊戲時發生錯誤，請重試", ephemeral=True)
                except:
                    pass
                return
            
            # 記錄遊戲
            key = tuple(sorted([self.challenger.id, self.opponent.id]))
            self.cog.tictactoe_games[key] = view
            
        except Exception as e:
            logger.error(f"[TicTacToe] 接受挑戰失敗: {e}")
            try:
                await interaction.followup.send(f"❌ 接受挑戰失敗：{str(e)}", ephemeral=True)
            except:
                pass

    @discord.ui.button(label="拒絕挑戰", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.opponent:
            await interaction.response.send_message("❌ 這不是你要拒絕的挑戰喔～", ephemeral=True)
            return
        
        try:
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(content=f"❌ {self.opponent.mention} 拒絕了 {self.challenger.mention} 的挑戰。", view=self)
        except Exception as e:
            logger.error(f"[TicTacToe] 拒絕挑戰失敗: {e}")
            try:
                await interaction.response.send_message(f"❌ 拒絕挑戰失敗：{str(e)}", ephemeral=True)
            except:
                pass

class MinesweeperModeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)

    async def on_timeout(self):
        try:
            for child in self.children:
                child.disabled = True
            logger.info(f"[MinesweeperModeView] 沒有選擇模式，已取消遊戲")
        except Exception as e:
            logger.error(f"[MinesweeperModeView] 超時處理失敗: {e}")

    @discord.ui.button(label="單人模式", style=discord.ButtonStyle.primary)
    async def single_mode(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            game = MinesweeperGame(size=5, bombs=5)
            view = MinesweeperGameView(game)
            await interaction.response.edit_message(content="💣 踩地雷遊戲開始！點擊格子來揭開，小心不要踩到地雷喔！", view=view)
        except Exception as e:
            logger.error(f"[Minesweeper] 啟動單人模式失敗: {e}")
            try:
                await interaction.response.send_message(f"❌ 啟動遊戲失敗：{str(e)}", ephemeral=True)
            except:
                pass

    @discord.ui.button(label="對戰模式", style=discord.ButtonStyle.success)
    async def versus_mode(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.send_message("💣 對戰模式功能正在開發中，敬請期待！", ephemeral=True)
        except Exception as e:
            logger.error(f"[Minesweeper] 對戰模式失敗: {e}")
            try:
                await interaction.response.send_message(f"❌ 啟動對戰模式失敗：{str(e)}", ephemeral=True)
            except:
                pass

class TicTacToeGameView(discord.ui.View):
    def __init__(self, player1, player2, cog):
        super().__init__(timeout=180)
        self.player1 = player1
        self.player2 = player2
        self.cog = cog
        self.board = [[None for _ in range(3)] for _ in range(3)]
        self.current = player1  # 先手
        self.game_over = False
        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y, self))

    async def on_timeout(self):
        try:
            for child in self.children:
                child.disabled = True
            logger.info(f"[TicTacToeGameView] 對戰逾時未完成，遊戲結束")
        except Exception as e:
            logger.error(f"[TicTacToeGameView] 逾時處理失敗: {e}")
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
        try:
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
        except Exception as e:
            logger.error(f"[TicTacToeButton] 回調處理失敗: {e}")
            try:
                await interaction.response.send_message("❌ 處理下棋時發生錯誤，請重試", ephemeral=True)
            except:
                pass

def get_rps_result(user, bot):
    if user == bot:
        return "平手"
    if (user, bot) in [("剪刀", "布"), ("布", "石頭"), ("石頭", "剪刀")]:
        return "你贏了！"
    return "你輸了～"

# 自定義數字選擇視圖
class CustomNumberView(discord.ui.View):
    def __init__(self, user: discord.User, cog):
        super().__init__(timeout=60)
        self.user = user
        self.cog = cog

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    async def on_timeout(self):
        # 超時處理
        try:
            for child in self.children:
                child.disabled = True
            logger.info(f"[CustomNumberView] 設定超時，自定義猜數字遊戲已取消")
        except Exception as e:
            logger.error(f"[CustomNumberView] 超時處理失敗: {e}")

    @discord.ui.button(label="1-20", style=discord.ButtonStyle.primary, row=0)
    async def range_1_20(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.show_number_selector(interaction, 1, 20)
        except Exception as e:
            logger.error(f"[CustomNumberView] 1-20 範圍選擇失敗: {e}")
            try:
                await interaction.response.send_message("❌ 選擇範圍時發生錯誤，請重試", ephemeral=True)
            except:
                pass

    @discord.ui.button(label="21-40", style=discord.ButtonStyle.primary, row=0)
    async def range_21_40(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.show_number_selector(interaction, 21, 40)
        except Exception as e:
            logger.error(f"[CustomNumberView] 21-40 範圍選擇失敗: {e}")
            try:
                await interaction.response.send_message("❌ 選擇範圍時發生錯誤，請重試", ephemeral=True)
            except:
                pass

    @discord.ui.button(label="41-60", style=discord.ButtonStyle.primary, row=0)
    async def range_41_60(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.show_number_selector(interaction, 41, 60)
        except Exception as e:
            logger.error(f"[CustomNumberView] 41-60 範圍選擇失敗: {e}")
            try:
                await interaction.response.send_message("❌ 選擇範圍時發生錯誤，請重試", ephemeral=True)
            except:
                pass

    @discord.ui.button(label="61-80", style=discord.ButtonStyle.primary, row=1)
    async def range_61_80(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.show_number_selector(interaction, 61, 80)
        except Exception as e:
            logger.error(f"[CustomNumberView] 61-80 範圍選擇失敗: {e}")
            try:
                await interaction.response.send_message("❌ 選擇範圍時發生錯誤，請重試", ephemeral=True)
            except:
                pass

    @discord.ui.button(label="81-100", style=discord.ButtonStyle.primary, row=1)
    async def range_81_100(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.show_number_selector(interaction, 81, 100)
        except Exception as e:
            logger.error(f"[CustomNumberView] 81-100 範圍選擇失敗: {e}")
            try:
                await interaction.response.send_message("❌ 選擇範圍時發生錯誤，請重試", ephemeral=True)
            except:
                pass

    async def show_number_selector(self, interaction: discord.Interaction, start: int, end: int):
        try:
            # 創建數字選擇器
            view = NumberSelectorView(self.user, self.cog, start, end)
            embed = discord.Embed(
                title=f"🎯 選擇數字 ({start}-{end})",
                description=f"請選擇 {start} 到 {end} 之間的數字作為正確答案",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="遊戲說明",
                value="設定完成後，其他玩家可以回覆遊戲訊息來猜測數字",
                inline=False
            )
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            logger.error(f"[CustomNumberView] 顯示數字選擇器失敗: {e}")
            try:
                await interaction.response.send_message("❌ 顯示數字選擇器時發生錯誤，請重試", ephemeral=True)
            except:
                pass

class NumberSelectorView(discord.ui.View):
    def __init__(self, user: discord.User, cog, start: int, end: int):
        super().__init__(timeout=60)
        self.user = user
        self.cog = cog
        self.start = start
        self.end = end
        self.create_buttons()

    def create_buttons(self):
        # 清除現有按鈕
        self.clear_items()
        
        # 創建數字按鈕 (每行5個)
        numbers_per_row = 5
        for i in range(self.start, self.end + 1):
            row = (i - self.start) // numbers_per_row
            button = discord.ui.Button(
                label=str(i),
                style=discord.ButtonStyle.secondary,
                row=row
            )
            button.callback = self.create_callback(i)
            self.add_item(button)

    def create_callback(self, number: int):
        async def callback(interaction: discord.Interaction):
            try:
                # 設定自定義數字
                self.cog.custom_numbers[interaction.channel.id] = {
                    'number': number,
                    'host': self.user.id
                }
                
                embed = discord.Embed(
                    title="🎯 自定義猜數字遊戲已設定！",
                    description=f"**{self.user.mention}** 已設定正確答案",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="遊戲規則",
                    value="• 回覆這則訊息並輸入你猜的數字\n• 我會告訴你猜的數字是太大還是太小\n• 猜對就贏了！",
                    inline=False
                )
                embed.add_field(
                    name="開始猜測",
                    value="請回覆這則訊息並輸入你的猜測數字",
                    inline=False
                )
                embed.set_footer(text=f"主持人: {self.user.display_name}")
                
                # 禁用所有按鈕
                for child in self.children:
                    child.disabled = True
                
                await interaction.response.edit_message(embed=embed, view=self)
                
            except Exception as e:
                logger.error(f"[NumberSelectorView] 設定數字失敗: {e}")
            try:
                await interaction.response.send_message(f"❌ 設定數字失敗：{str(e)}", ephemeral=True)
            except:
                pass
        
        return callback

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    async def on_timeout(self):
        # 超時處理
        try:
            for child in self.children:
                child.disabled = True
            logger.info(f"[NumberSelectorView] 選擇超時，自定義猜數字遊戲已取消")
        except Exception as e:
            logger.error(f"[NumberSelectorView] 超時處理失敗: {e}")

async def setup(bot):
    await bot.add_cog(MiniGames(bot))
