import discord
from discord.ext import commands
from discord import app_commands
import random
import json
import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List

logger = logging.getLogger('AdvancedGames')

class AdvancedGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}
        self.economy_data = {}
        self.load_economy_data()

    def load_economy_data(self):
        try:
            with open('economy.json', 'r', encoding='utf-8') as f:
                self.economy_data = json.load(f)
        except FileNotFoundError:
            logger.info("[AdvancedGames] economy.json not found, creating new file")
            self.economy_data = {}
        except json.JSONDecodeError as e:
            logger.error(f"[AdvancedGames] economy.json format error: {e}")
            self.economy_data = {}
        except PermissionError:
            logger.error("[AdvancedGames] No permission to read economy.json")
            self.economy_data = {}
        except Exception as e:
            logger.error(f"[AdvancedGames] Error loading economy data: {e}")
            self.economy_data = {}

    def save_economy_data(self):
        try:
            with open('economy.json', 'w', encoding='utf-8') as f:
                json.dump(self.economy_data, f, ensure_ascii=False, indent=2)
        except PermissionError:
            logger.error("[AdvancedGames] No permission to write economy.json")
        except Exception as e:
            logger.error(f"[AdvancedGames] Error saving economy data: {e}")

    def get_user_balance(self, user_id: int) -> int:
        try:
            return self.economy_data.get(str(user_id), 0)
        except Exception as e:
            logger.error(f"[AdvancedGames] Error getting user balance: {e}")
            return 0

    def add_user_balance(self, user_id: int, amount: int):
        try:
            user_id_str = str(user_id)
            if user_id_str not in self.economy_data:
                self.economy_data[user_id_str] = 0
            self.economy_data[user_id_str] += amount
            self.save_economy_data()
        except Exception as e:
            logger.error(f"[AdvancedGames] Error adding user balance: {e}")

    @app_commands.command(name="每日簽到", description="每日簽到獲得金幣")
    async def daily(self, interaction: discord.Interaction):
        try:
            user_id = interaction.user.id
            user_id_str = str(user_id)
            
            # 檢查是否已經簽到
            last_daily = self.economy_data.get(f"{user_id_str}_last_daily")
            if last_daily:
                try:
                    last_daily_date = datetime.fromisoformat(last_daily)
                    if datetime.now() - last_daily_date < timedelta(days=1):
                        remaining = timedelta(days=1) - (datetime.now() - last_daily_date)
                        hours = int(remaining.total_seconds() // 3600)
                        minutes = int((remaining.total_seconds() % 3600) // 60)
                        
                        embed = discord.Embed(
                            title="⏰ 今日已簽到",
                            description=f"你今天已經簽到過了！還需要等待 **{hours}小時{minutes}分鐘**",
                            color=discord.Color.orange()
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                except ValueError as e:
                    logger.error(f"[AdvancedGames] Date parsing error: {e}")
                    # 如果日期格式錯誤，清除舊數據
                    self.economy_data.pop(f"{user_id_str}_last_daily", None)

            # 簽到獎勵
            reward = random.randint(50, 150)
            self.add_user_balance(user_id, reward)
            self.economy_data[f"{user_id_str}_last_daily"] = datetime.now().isoformat()
            self.save_economy_data()

            embed = discord.Embed(
                title="🎉 每日簽到成功！",
                description=f"你獲得了 **{reward}** 金幣！",
                color=discord.Color.green()
            )
            embed.add_field(name="當前餘額", value=f"💰 {self.get_user_balance(user_id)} 金幣")
            embed.set_footer(text=f"簽到者: {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"[AdvancedGames] daily command error: {e}")
            embed = discord.Embed(
                title="❌ 簽到失敗",
                description="簽到時發生錯誤，請稍後再試",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="餘額", description="查看你的金幣餘額")
    async def balance(self, interaction: discord.Interaction):
        try:
            balance = self.get_user_balance(interaction.user.id)
            embed = discord.Embed(
                title="💰 金幣餘額",
                description=f"**{interaction.user.display_name}** 的餘額",
                color=discord.Color.gold()
            )
            embed.add_field(name="當前餘額", value=f"💰 {balance} 金幣")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"[AdvancedGames] balance command error: {e}")
            embed = discord.Embed(
                title="❌ 查詢失敗",
                description="查詢餘額時發生錯誤，請稍後再試",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="轉帳", description="轉帳給其他用戶")
    @app_commands.describe(user="要轉帳的用戶", amount="轉帳金額")
    async def transfer(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        try:
            if amount <= 0:
                embed = discord.Embed(
                    title="❌ 金額錯誤",
                    description="轉帳金額必須大於 0",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            if user.bot:
                embed = discord.Embed(
                    title="❌ 無法轉帳",
                    description="不能轉帳給機器人",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            sender_balance = self.get_user_balance(interaction.user.id)
            if sender_balance < amount:
                embed = discord.Embed(
                    title="❌ 餘額不足",
                    description="你的餘額不足以完成此轉帳",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # 執行轉帳
            self.add_user_balance(interaction.user.id, -amount)
            self.add_user_balance(user.id, amount)

            embed = discord.Embed(
                title="💸 轉帳成功",
                description=f"**{interaction.user.display_name}** 轉帳給 **{user.display_name}**",
                color=discord.Color.green()
            )
            embed.add_field(name="轉帳金額", value=f"💰 {amount} 金幣")
            embed.add_field(name="你的餘額", value=f"💰 {self.get_user_balance(interaction.user.id)} 金幣")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"[AdvancedGames] transfer command error: {e}")
            embed = discord.Embed(
                title="❌ 轉帳失敗",
                description="轉帳時發生錯誤，請稍後再試",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="賭博", description="賭博遊戲 - 猜大小")
    @app_commands.describe(amount="賭注金額", choice="選擇大或小")
    @app_commands.choices(choice=[
        app_commands.Choice(name="大 (7-12)", value="big"),
        app_commands.Choice(name="小 (1-6)", value="small")
    ])
    async def gamble(self, interaction: discord.Interaction, amount: int, choice: app_commands.Choice[str]):
        try:
            if amount <= 0:
                embed = discord.Embed(
                    title="❌ 賭注錯誤",
                    description="賭注金額必須大於 0",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            user_balance = self.get_user_balance(interaction.user.id)
            if user_balance < amount:
                embed = discord.Embed(
                    title="❌ 餘額不足",
                    description="你的餘額不足以進行此賭注",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # 擲骰子
            dice1 = random.randint(1, 6)
            dice2 = random.randint(1, 6)
            total = dice1 + dice2
            
            # 判斷結果
            result = "big" if total >= 7 else "small"
            won = choice.value == result
            
            # 更新餘額
            if won:
                self.add_user_balance(interaction.user.id, amount)
                result_text = "🎉 恭喜你贏了！"
                color = discord.Color.green()
            else:
                self.add_user_balance(interaction.user.id, -amount)
                result_text = "😢 很遺憾，你輸了"
                color = discord.Color.red()

            embed = discord.Embed(
                title="🎲 賭博結果",
                description=result_text,
                color=color
            )
            embed.add_field(name="骰子", value=f"🎲 {dice1} + {dice2} = **{total}**")
            embed.add_field(name="你的選擇", value=f"你選擇了: **{choice.name}**")
            embed.add_field(name="結果", value=f"實際結果: **{'大' if result == 'big' else '小'}**")
            embed.add_field(name="餘額變化", value=f"💰 {self.get_user_balance(interaction.user.id)} 金幣")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"[AdvancedGames] gamble command error: {e}")
            embed = discord.Embed(
                title="❌ 賭博失敗",
                description="賭博時發生錯誤，請稍後再試",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="排行榜", description="查看金幣排行榜")
    async def leaderboard(self, interaction: discord.Interaction):
        try:
            # 排序用戶
            sorted_users = sorted(
                self.economy_data.items(),
                key=lambda x: x[1] if isinstance(x[1], int) else 0,
                reverse=True
            )[:10]

            embed = discord.Embed(
                title="🏆 金幣排行榜",
                description="伺服器最富有的用戶",
                color=discord.Color.gold()
            )

            if not sorted_users:
                embed.add_field(
                    name="📊 排行榜",
                    value="目前還沒有任何用戶有金幣記錄",
                    inline=False
                )
            else:
                for i, (user_id, balance) in enumerate(sorted_users, 1):
                    if isinstance(balance, int):  # 只顯示金幣餘額，不是其他數據
                        try:
                            user = self.bot.get_user(int(user_id))
                            username = user.display_name if user else f"用戶 {user_id}"
                            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                            embed.add_field(
                                name=f"{medal} {username}",
                                value=f"💰 {balance} 金幣",
                                inline=False
                            )
                        except (ValueError, KeyError):
                            continue

            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"[AdvancedGames] leaderboard command error: {e}")
            embed = discord.Embed(
                title="❌ 查詢失敗",
                description="查詢排行榜時發生錯誤，請稍後再試",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="工作", description="工作賺取金幣")
    async def work(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user_id_str = str(user_id)
        
        # 檢查工作冷卻時間
        last_work = self.economy_data.get(f"{user_id_str}_last_work")
        if last_work:
            last_work_time = datetime.fromisoformat(last_work)
            if datetime.now() - last_work_time < timedelta(minutes=5):
                remaining = timedelta(minutes=5) - (datetime.now() - last_work_time)
                minutes = int(remaining.total_seconds() // 60)
                await interaction.response.send_message(
                    f"⏰ 你還需要休息 {minutes} 分鐘才能再次工作",
                    ephemeral=True
                )
                return

        # 工作獎勵
        jobs = [
            ("👨‍💼 辦公室工作", 20, 40),
            ("👨‍🍳 餐廳服務", 15, 35),
            ("🚚 送貨員", 25, 45),
            ("👨‍🔧 維修工", 30, 50),
            ("🎨 藝術家", 35, 60),
            ("💻 程式設計師", 40, 70)
        ]
        
        job_name, min_pay, max_pay = random.choice(jobs)
        earnings = random.randint(min_pay, max_pay)
        
        self.add_user_balance(user_id, earnings)
        self.economy_data[f"{user_id_str}_last_work"] = datetime.now().isoformat()
        self.save_economy_data()

        embed = discord.Embed(
            title="💼 工作完成！",
            description=f"你完成了 **{job_name}**",
            color=discord.Color.blue()
        )
        embed.add_field(name="收入", value=f"💰 +{earnings} 金幣")
        embed.add_field(name="當前餘額", value=f"💰 {self.get_user_balance(user_id)} 金幣")
        embed.set_footer(text="5分鐘後可以再次工作")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(AdvancedGames(bot)) 