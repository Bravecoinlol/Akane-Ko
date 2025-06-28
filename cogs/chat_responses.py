import discord
from discord.ext import commands
from discord import app_commands
import json
import aiohttp
import asyncio
import logging
import os
from dotenv import load_dotenv
import requests

# 設定 logger
logger = logging.getLogger('ChatResponses')

load_dotenv()
API2D_KEY = os.getenv("API2D_API_KEY")

class ChatResponses(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.question_cog = None

    @commands.Cog.listener()
    async def on_ready(self):
        if self.question_cog is None:
            self.question_cog = self.bot.get_cog("QuestionCog")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        if not self.question_cog:
            self.question_cog = self.bot.get_cog("QuestionCog")
            if not self.question_cog:
                return

        if message.reference or message.id in getattr(self.question_cog, "processed_messages", set()):
            return

        content = message.content.strip().lower()

        keyword_responses = {
            "hello": "Hello~ 我是一個日本女高中生 今年17 請多多指教❤️",
            "機器人是gay": "閉嘴啦 Gay佬",
            "成功了 we did it": "成功了 Ya",
            "我愛妳": "我也愛你❤️",
            "我討厭妳": "謝謝你的討厭 祝你找到更討厭的人",
            "跨沙小 我要shampoo": "Yea then you got kicked out(Yea然後你就被踢出去了)",
            "www": "wwwww",
            "我快死了": "要幫你按摩一下嗎❤️",
        }

        if content in keyword_responses:
            await message.channel.send(keyword_responses[content])
            return

        if content == "我or他選一個":
            await message.channel.send("當然是妳啊 老公❤️" if random.choice(["4", "3", "2", "1", "0"]) == "1" else "還是他比較好 你算了吧")
            return
        if content == "當我老婆":
            await message.channel.send("好❤️" if random.choice(["1", "0"]) == "0" else "不要 噁男")
            return
        if content == "妳願意嫁給我嗎":
            await message.channel.send("好 我願意❤️" if random.choice(["1", "0"]) == "1" else "(遞給你一張好人卡 表示拒絕)")
            return

        # 只有被 @ 才觸發 GPT 回應
        if self.bot.user in message.mentions:
            try:
                headers = {
                    "Authorization": f"Bearer {API2D_KEY}",
                    "Content-Type": "application/json",
                }
                data = {
                    "model": "gpt-4-turbo",
                    "messages": [
                        {"role": "system", "content": "你是一個可愛的Discord女高中生聊天機器人。"},
                        {"role": "user", "content": content},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 150,
                }
                async with aiohttp.ClientSession() as session:
                    async with session.post("https://api.api2d.net/v1/chat/completions", headers=headers, json=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            reply = result.get('choices', [{}])[0].get('message', {}).get('content', '抱歉，我無法回應。')
                            await message.channel.send(reply)
                        else:
                            logger.error("API2D Error: %s", response.status)
                            await message.channel.send(f"API 錯誤: {response.status}")
            except Exception as e:
                logger.error("API2D Error: %s", e)
                await message.channel.send("連接錯誤: " + str(e))

        await self.bot.process_commands(message)

async def setup(bot):
    logger.info("Loading ChatResponses Cog...")
    await bot.add_cog(ChatResponses(bot))
