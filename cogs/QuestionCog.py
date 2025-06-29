import discord
import json
import os
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import logging
from collections import deque

# 設定 logger
logger = logging.getLogger('QuestionCog')

class QuestionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.coins = {}
        self.questions = {}
        self.processed_messages = set()
        self.max_processed_messages = 1000  # 限制已處理訊息的最大數量
        self.load_coins()  # 加載金幣數據

    def load_coins(self):
        """載入金幣資料"""
        try:
            with open('coins.json', 'r', encoding='utf-8') as f:
                self.coins = json.load(f)
                logger.info("Loaded coins data: %s", self.coins)  # 顯示加載的金幣數據
        except FileNotFoundError:
            logger.info("coins.json not found, creating a new one.")
            self.coins = {}
        except json.JSONDecodeError as e:
            logger.warning(f"coins.json is corrupted: {e}, initializing new data.")
            self.coins = {}
        except PermissionError:
            logger.error("No permission to read coins.json")
            self.coins = {}
        except Exception as e:
            logger.error(f"Error loading coins.json: {e}")
            self.coins = {}

    def save_coins(self):
        """保存金幣資料"""
        try:
            logger.debug("Saving coins data to coins.json: %s", self.coins)  # 顯示即將保存的金幣數據
            with open('coins.json', 'w', encoding='utf-8') as f:
                json.dump(self.coins, f, indent=2, ensure_ascii=False)
            logger.info("Coins data saved successfully.")
        except PermissionError:
            logger.error("No permission to write coins.json")
        except Exception as e:
            logger.error(f"Error saving coins data: {e}")

    def save_coins_async(self):
        """異步保存金幣資料"""
        try:
            logger.debug("Saving coins data to coins.json: %s", self.coins)  # 顯示即將保存的金幣數據
            with open('coins.json', 'w', encoding='utf-8') as f:
                json.dump(self.coins, f, indent=2, ensure_ascii=False)
            logger.info("Coins data saved successfully.")
        except PermissionError:
            logger.error("No permission to write coins.json")
        except Exception as e:
            logger.error(f"Error saving coins data: {e}")

    def update_coins(self, user_id, amount):
        """更新用戶金幣"""
        try:
            user_id_str = str(user_id)
            logger.debug("正在更新金幣: 用戶 %s 獲得 %s 金幣", user_id_str, amount)  # Debugging line
            
            if user_id_str not in self.coins:
                self.coins[user_id_str] = 0
            
            self.coins[user_id_str] += amount
            
            # 限制處理過的訊息數量，避免記憶體過度增長
            if len(self.processed_messages) > 1000:
                # 保留最新的 500 個訊息 ID
                self.processed_messages = set(list(self.processed_messages)[-500:])
            
            logger.debug("金幣已更新: 用戶 %s 的金幣已增加", user_id_str)
        except Exception as e:
            logger.error(f"更新金幣失敗: {e}")

    def get_coins(self, user_id):
        """獲取用戶金幣"""
        try:
            user_id_str = str(user_id)
            logger.debug("Fetching coins for user_id: %s", user_id)  # Debug 用，確認抓取的 user_id
            coins = self.coins.get(user_id_str, 0)
            logger.debug("Coins data: %s", self.coins)  # Debug 用，確認 self.coins 資料是否完整
            logger.debug("User %s has %s coins", user_id, coins)  # Debug 用，確認對應金幣數量
            return coins
        except Exception as e:
            logger.error(f"獲取金幣失敗: {e}")
            return 0

    @app_commands.command(name="coin", description="查看自己的金幣餘額")
    async def coin(self, interaction: discord.Interaction):
        try:
            user_id = str(interaction.user.id)  # 確保 user_id 是字串
            print(f"Fetching coins for user_id: {user_id}")  # Debug 用，確認抓取的 user_id

            coins = self.coins.get(user_id, 0)  # 從 self.coins 獲取對應用戶的金幣數量
            print(f"Coins data: {self.coins}")  # Debug 用，確認 self.coins 資料是否完整
            print(f"User {user_id} has {coins} coins")  # Debug 用，確認對應金幣數量

            # 回傳用戶的金幣餘額
            embed = discord.Embed(
                title="💰 金幣餘額",
                description=f"{interaction.user.mention} 你的金幣數量是: **{coins}**",
                color=discord.Color.gold()
            )
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"[QuestionCog] coin命令執行失敗: {e}")
            embed = discord.Embed(
                title="❌ 查詢失敗",
                description="無法查詢金幣餘額，請稍後再試",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="question", description="設定一個問題並提供答案和獎勳金幣")
    async def question(self, interaction: discord.Interaction, question: str, answer: str, reward: int):
        try:
            if reward <= 0:
                embed = discord.Embed(
                    title="❌ 獎勵設定錯誤",
                    description="你太無情了，竟然敢用 0！所以我不給你提問😝",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            if len(question) > 1000:
                embed = discord.Embed(
                    title="❌ 問題過長",
                    description="問題長度不能超過1000個字符",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            if len(answer) > 200:
                embed = discord.Embed(
                    title="❌ 答案過長",
                    description="答案長度不能超過200個字符",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # 發布問題
            embed = discord.Embed(title="❓ 新問題！", description=question, color=discord.Color.blue())
            embed.add_field(name="回答方式", value="請直接在此訊息回覆答案！", inline=False)
            embed.set_footer(text=f"提供者: {interaction.user.display_name} | 獎勳金幣: {reward}")

            msg = await interaction.channel.send(embed=embed)
            self.questions[msg.id] = {
                "Question": question,
                "answer": answer.lower(),
                "reward": reward,
                "author": interaction.user.id
            }
            
            success_embed = discord.Embed(
                title="✅ 問題發布成功",
                description="問題已成功發布！",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"[QuestionCog] question命令執行失敗: {e}")
            embed = discord.Embed(
                title="❌ 發布失敗",
                description="發布問題時發生錯誤，請稍後再試",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        if message.id in self.processed_messages:
            return
        
        user_id = str(message.author.id)

        if message.reference:
            ref_message_id = message.reference.message_id
            if ref_message_id in self.questions:
                question_data = self.questions[ref_message_id]

                if message.content.lower() == question_data["answer"]:
                    reward = question_data["reward"]
                    await message.channel.send(f"{message.author.mention} 答對了！獲得 {reward} 金幣！ 🎉")
                    await self.update_coins(message.author.id, reward)  # 更新金幣
                    del self.questions[ref_message_id]
                else:
                    await message.channel.send(f"{message.author.mention} 答錯了，請再試一次！")

                # 標記該訊息為已處理
                self.processed_messages.add(message.id)
                
                # 如果已處理的訊息太多，清理舊的記錄
                if len(self.processed_messages) > self.max_processed_messages:
                    # 保留最新的 500 個記錄
                    self.processed_messages = set(list(self.processed_messages)[-500:])
        
        await self.bot.process_commands(message)

    @app_commands.command(name="give", description="將自己的金幣轉給其他人")
    async def give(self, interaction: discord.Interaction, recipient: discord.User, amount: int):
        try:
            if amount <= 0:
                embed = discord.Embed(
                    title="❌ 金額錯誤",
                    description="請輸入正確的金額！",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            if recipient.bot:
                embed = discord.Embed(
                    title="❌ 無法轉帳",
                    description="無法轉帳給機器人！",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            sender_id = str(interaction.user.id)
            recipient_id = str(recipient.id)

            # 確保發送者和接收者的金幣數據存在
            if sender_id not in self.coins:
                self.coins[sender_id] = 0
            if recipient_id not in self.coins:
                self.coins[recipient_id] = 0

            # 驗證發送者是否有足夠的金幣
            if self.coins[sender_id] < amount:
                embed = discord.Embed(
                    title="❌ 金幣不足",
                    description=f"{interaction.user.mention} 你的金幣不足！",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # 更新金幣數量
            self.coins[sender_id] -= amount
            self.coins[recipient_id] += amount

            await self.save_coins()  # 保存金幣資料到文件
            
            embed = discord.Embed(
                title="✅ 轉帳成功",
                description=f"{interaction.user.mention} 將 **{amount}** 金幣轉給了 {recipient.mention}！",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"[QuestionCog] give命令執行失敗: {e}")
            embed = discord.Embed(
                title="❌ 轉帳失敗",
                description="轉帳時發生錯誤，請稍後再試",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="clean_coin", description="清空金幣數量（管理員限定）")
    @app_commands.checks.has_permissions(administrator=True)
    async def clean_coin(self, interaction: discord.Interaction, target: discord.User):
        try:
            target_id = str(target.id)

            if target_id not in self.coins:
                embed = discord.Embed(
                    title="⚠️ 無金幣",
                    description=f"{target.mention} 目前沒有金幣！",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            self.coins[target_id] = 0
            await self.save_coins()  # 保存金幣資料
            
            embed = discord.Embed(
                title="✅ 清空成功",
                description=f"{interaction.user.mention} 已經清空 {target.mention} 的金幣數量。",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"[QuestionCog] clean_coin命令執行失敗: {e}")
            embed = discord.Embed(
                title="❌ 清空失敗",
                description="清空金幣時發生錯誤，請稍後再試",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @clean_coin.error
    async def clean_coin_error(self, interaction: discord.Interaction, error):
        try:
            if isinstance(error, app_commands.MissingPermissions):
                embed = discord.Embed(
                    title="❌ 權限不足",
                    description=f"{interaction.user.mention} 你沒有權限使用這個指令！",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                logger.error(f"[QuestionCog] clean_coin錯誤處理失敗: {error}")
                embed = discord.Embed(
                    title="❌ 執行錯誤",
                    description="執行命令時發生錯誤，請稍後再試",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"[QuestionCog] clean_coin錯誤處理失敗: {e}")

async def setup(bot):
    await bot.add_cog(QuestionCog(bot))  # 加載 Cog