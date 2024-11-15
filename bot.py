# 導入Discord.py模組
from ast import Not
import discord
import random
import json
from discord.ext import commands
from random import sample

# client是跟discord連接，intents是要求機器人的權限
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.members = True
intents.guilds = True
client = discord.Client(intents = intents)
text_channel_id = 1142381405456834570

# 調用event函式庫
@client.event
# 當機器人完成啟動
async def on_ready():
    print(f"目前登入身份 --> {client.user}")

@client.event
# 當頻道有新訊息
async def on_member_join(member):
    text_channel = client.get_channel(text_channel_id)
    if text_channel:
        await text_channel.send(f'歡迎 **{member.display_name}** 加進來伺服器! 我等不及了❤️')

@client.event
async def on_member_remove(member):
    text_channel = client.get_channel(text_channel_id)
    if text_channel:
        await text_channel.send(f' **{member.display_name}** 離開了 因為他搞偷吃💢')

@client.event
async def on_message(message):
    # 排除機器人本身的訊息，避免無限循環
    if message.author == client.user:
        return
    if message.author.bot:
        return
    # 新訊息包含Hello，回覆Hello, world!
    if message.content == "Hello":
        await message.channel.send("Hello~ 我是一個日本女高中生 今年17 請多多指教❤️")
    if message.content == "機器人是Gay":
        await message.channel.send("閉嘴啦 Gay佬")
    if message.content == "成功了 We Did It":
        await message.channel.send("成功了 Ya")
    if message.content == "我愛妳":
        await message.channel.send("我也愛你❤️")
    if message.content == "我討厭妳":
        await message.channel.send("謝謝你的討厭 祝你找到更討厭的人")
    if message.content == "跨沙小 我要Shampoo":
        await message.channel.send("Yea then you got kicked out(Yea然後你就被踢出去了)")
    if message.content == "www":
        await message.channel.send("wwwww")
    if message.content == "我or他選一個":
        sample = random.choice(['4','3','2','1','0'])
        if sample == "1":
            await message.channel.send("當然是妳啊 老公❤️")
        else:
            await message.channel.send("還是他比較好 你算了吧")
    if message.content == "我快死了":
        await message.channel.send("要幫你按摩一下嗎❤️")
    if message.content == "當我老婆":
        sample = random.choice(['1','0'])
        if sample == "0":
            await message.channel.send("好❤️")
        else:
            await message.channel.send("不要 噁男")
    if message.content == "妳願意嫁給我嗎":
        sample = random.choice(['1','0'])
        if sample == "1":
            await message.channel.send("好 我願意❤️")
        else:
            await message.channel.send("(遞給你一張好人卡 表示拒絕)")
    if client.user in message.mentions:
        sample = random.choice(['0' , '1' , '2' , '3' , '4'])
        if sample == "0":
            await message.channel.send(f"請問有什麼事嗎 老公❤️")
        else:
            if sample == "1":
                await message.channel.send(f"幹你娘勒 Ping我從三小")
            else:
                if sample == "2":
                    await message.channel.send(f'?')
                else:
                    if sample == "3":
                        await message.channel.send(f'哈....哈.....找我有什麼事嗎❤️❤️❤️❤️')
                    else:
                        await message.channel.send(f'マスター、私に何があったのですか❤️？')
    
            


client.run('')