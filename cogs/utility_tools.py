import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import json
import os
import logging
import re
from datetime import datetime, timedelta
from typing import Optional
import math
import random
import asyncio
import io

logger = logging.getLogger('UtilityTools')

class UtilityTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weather_cache = {}
        self.cache_duration = timedelta(minutes=10)

    @app_commands.command(name="translate", description="翻譯文字")
    @app_commands.describe(
        text="要翻譯的文字",
        target_lang="目標語言"
    )
    @app_commands.choices(target_lang=[
        app_commands.Choice(name="英文", value="en"),
        app_commands.Choice(name="日文", value="ja"),
        app_commands.Choice(name="韓文", value="ko"),
        app_commands.Choice(name="法文", value="fr"),
        app_commands.Choice(name="德文", value="de"),
        app_commands.Choice(name="西班牙文", value="es"),
        app_commands.Choice(name="中文", value="zh")
    ])
    async def translate(self, interaction: discord.Interaction, text: str, target_lang: app_commands.Choice[str]):
        await interaction.response.defer()
        
        try:
            # 檢查文字長度
            if len(text) > 500:
                await interaction.followup.send("❌ 文字太長，請輸入500字以內的文字", ephemeral=True)
                return
            
            # 使用免費的翻譯 API
            url = "https://api.mymemory.translated.net/get"
            params = {
                "q": text,
                "langpair": f"auto|{target_lang.value}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        translated_text = data.get("responseData", {}).get("translatedText", "")
                        
                        if not translated_text:
                            await interaction.followup.send("❌ 翻譯失敗，請檢查文字內容或稍後再試", ephemeral=True)
                            return
                        
                        embed = discord.Embed(
                            title="🌐 翻譯結果",
                            color=discord.Color.blue()
                        )
                        embed.add_field(name="原文", value=text, inline=False)
                        embed.add_field(name=f"翻譯 ({target_lang.name})", value=translated_text, inline=False)
                        
                        await interaction.followup.send(embed=embed)
                    elif resp.status == 429:
                        await interaction.followup.send("❌ 翻譯服務使用過於頻繁，請稍後再試", ephemeral=True)
                    else:
                        await interaction.followup.send(f"❌ 翻譯服務暫時無法使用 (錯誤碼: {resp.status})", ephemeral=True)
                        
        except asyncio.TimeoutError:
            await interaction.followup.send("❌ 翻譯服務回應超時，請稍後再試", ephemeral=True)
        except aiohttp.ClientError as e:
            logger.error(f"翻譯網路錯誤: {e}")
            await interaction.followup.send("❌ 網路連接錯誤，請檢查網路連線", ephemeral=True)
        except Exception as e:
            logger.error(f"翻譯失敗: {e}")
            await interaction.followup.send(f"❌ 翻譯時發生錯誤：{str(e)}", ephemeral=True)

    @app_commands.command(name="weather", description="查詢天氣資訊")
    @app_commands.describe(city="城市名稱")
    async def weather(self, interaction: discord.Interaction, city: str):
        await interaction.response.defer()
        
        # 檢查城市名稱長度
        if len(city) > 50:
            await interaction.followup.send("❌ 城市名稱太長，請輸入50字以內的名稱", ephemeral=True)
            return
        
        # 檢查快取
        cache_key = city.lower()
        if cache_key in self.weather_cache:
            cache_time, weather_data = self.weather_cache[cache_key]
            if datetime.now() - cache_time < self.cache_duration:
                await self.send_weather_embed(interaction, weather_data)
                return
        
        try:
            # 使用免費天氣 API
            api_key = os.getenv("OPENWEATHER_API_KEY", "")
            if not api_key:
                # 如果沒有 API key，使用模擬數據
                weather_data = self.get_mock_weather(city)
                self.weather_cache[cache_key] = (datetime.now(), weather_data)
                await self.send_weather_embed(interaction, weather_data)
                return
            
            url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city,
                "appid": api_key,
                "units": "metric",
                "lang": "zh_tw"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        weather_data = {
                            "city": data["name"],
                            "country": data["sys"]["country"],
                            "temp": data["main"]["temp"],
                            "feels_like": data["main"]["feels_like"],
                            "humidity": data["main"]["humidity"],
                            "description": data["weather"][0]["description"],
                            "icon": data["weather"][0]["icon"]
                        }
                        
                        self.weather_cache[cache_key] = (datetime.now(), weather_data)
                        await self.send_weather_embed(interaction, weather_data)
                    elif resp.status == 404:
                        await interaction.followup.send(f"❌ 找不到城市「{city}」的天氣資訊，請檢查城市名稱", ephemeral=True)
                    elif resp.status == 401:
                        await interaction.followup.send("❌ 天氣API金鑰無效，請聯繫管理員", ephemeral=True)
                    elif resp.status == 429:
                        await interaction.followup.send("❌ 天氣服務使用過於頻繁，請稍後再試", ephemeral=True)
                    else:
                        await interaction.followup.send(f"❌ 查詢天氣失敗 (錯誤碼: {resp.status})", ephemeral=True)
                        
        except asyncio.TimeoutError:
            await interaction.followup.send("❌ 天氣服務回應超時，請稍後再試", ephemeral=True)
        except aiohttp.ClientError as e:
            logger.error(f"查詢天氣網路錯誤: {e}")
            await interaction.followup.send("❌ 網路連接錯誤，請檢查網路連線", ephemeral=True)
        except Exception as e:
            logger.error(f"查詢天氣失敗: {e}")
            await interaction.followup.send(f"❌ 查詢天氣時發生錯誤：{str(e)}", ephemeral=True)

    def get_mock_weather(self, city: str) -> dict:
        """生成模擬天氣數據"""
        temps = [15, 18, 22, 25, 28, 30]
        descriptions = ["晴天", "多雲", "陰天", "小雨", "大雨", "霧"]
        
        return {
            "city": city,
            "country": "TW",
            "temp": random.choice(temps),
            "feels_like": random.choice(temps),
            "humidity": random.randint(40, 90),
            "description": random.choice(descriptions),
            "icon": "01d"
        }

    async def send_weather_embed(self, interaction, weather_data):
        """發送天氣嵌入訊息"""
        temp_emoji = "🌡️"
        humidity_emoji = "💧"
        weather_emoji = "🌤️"
        
        embed = discord.Embed(
            title=f"{weather_emoji} {weather_data['city']} 天氣",
            description=f"國家: {weather_data['country']}",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name=f"{temp_emoji} 溫度",
            value=f"{weather_data['temp']}°C (體感: {weather_data['feels_like']}°C)",
            inline=True
        )
        embed.add_field(
            name=f"{humidity_emoji} 濕度",
            value=f"{weather_data['humidity']}%",
            inline=True
        )
        embed.add_field(
            name="天氣狀況",
            value=weather_data['description'],
            inline=True
        )
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="calculator", description="簡單的數學計算")
    @app_commands.describe(expression="數學表達式 (例如: 2+3*4)")
    async def calculator(self, interaction: discord.Interaction, expression: str):
        try:
            # 檢查表達式長度
            if len(expression) > 100:
                await interaction.response.send_message("❌ 表達式太長，請輸入100字以內的數學表達式", ephemeral=True)
                return
            
            # 清理表達式，只允許安全的字符
            safe_expr = re.sub(r'[^0-9+\-*/().\s]', '', expression)
            
            if not safe_expr.strip():
                await interaction.response.send_message("❌ 表達式無效，請輸入有效的數學表達式", ephemeral=True)
                return
            
            # 檢查除零錯誤
            if '/' in safe_expr and re.search(r'/\s*0(?![.0-9])', safe_expr):
                await interaction.response.send_message("❌ 除零錯誤，請檢查表達式", ephemeral=True)
                return
            
            # 計算結果
            result = eval(safe_expr)
            
            # 檢查結果是否為無限大或NaN
            if not math.isfinite(result):
                await interaction.response.send_message("❌ 計算結果超出範圍", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="🧮 計算結果",
                color=discord.Color.green()
            )
            embed.add_field(name="表達式", value=f"`{expression}`", inline=False)
            embed.add_field(name="結果", value=f"`{result}`", inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except ZeroDivisionError:
            await interaction.response.send_message("❌ 除零錯誤，請檢查表達式", ephemeral=True)
        except SyntaxError:
            await interaction.response.send_message("❌ 表達式語法錯誤，請檢查數學表達式", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ 表達式包含無效的數值", ephemeral=True)
        except Exception as e:
            logger.error(f"計算器錯誤: {e}")
            await interaction.response.send_message(f"❌ 計算錯誤：{str(e)}", ephemeral=True)

    @app_commands.command(name="random", description="生成隨機數字")
    @app_commands.describe(min_num="最小值", max_num="最大值", count="數量")
    async def random_number(self, interaction: discord.Interaction, min_num: int, max_num: int, count: int = 1):
        try:
            # 檢查數值範圍
            if min_num < -1000000 or max_num > 1000000:
                await interaction.response.send_message("❌ 數值範圍過大，請使用 -1,000,000 到 1,000,000 之間的數字", ephemeral=True)
                return
            
            if count < 1 or count > 20:
                await interaction.response.send_message("❌ 數量必須在 1-20 之間", ephemeral=True)
                return
            
            # 自動調整大小順序
            if min_num > max_num:
                min_num, max_num = max_num, min_num
            
            # 檢查範圍大小
            if max_num - min_num > 1000000:
                await interaction.response.send_message("❌ 數值範圍過大，最大值與最小值差距不能超過1,000,000", ephemeral=True)
                return
            
            # 生成隨機數字
            numbers = []
            for _ in range(count):
                numbers.append(random.randint(min_num, max_num))
            
            # 去重並排序
            unique_numbers = sorted(list(set(numbers)))
            
            embed = discord.Embed(
                title="🎲 隨機數字",
                color=discord.Color.purple()
            )
            embed.add_field(name="範圍", value=f"{min_num} 到 {max_num}", inline=True)
            embed.add_field(name="數量", value=str(count), inline=True)
            embed.add_field(name="結果", value=", ".join(map(str, unique_numbers)), inline=False)
            
            if len(unique_numbers) < count:
                embed.add_field(name="💡 注意", value="結果已去重，實際數量可能少於請求數量", inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"隨機數字生成錯誤: {e}")
            await interaction.response.send_message(f"❌ 生成隨機數字失敗：{str(e)}", ephemeral=True)

    @app_commands.command(name="time", description="顯示當前時間")
    @app_commands.describe(timezone="時區 (例如: Asia/Taipei)")
    async def current_time(self, interaction: discord.Interaction, timezone: str = "Asia/Taipei"):
        try:
            from datetime import timezone as dt_timezone
            import pytz
            
            tz = pytz.timezone(timezone)
            current_time = datetime.now(tz)
            
            embed = discord.Embed(
                title="🕐 當前時間",
                color=discord.Color.blue()
            )
            embed.add_field(name="時區", value=timezone, inline=True)
            embed.add_field(name="時間", value=current_time.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
            embed.add_field(name="星期", value=current_time.strftime("%A"), inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message("❌ 時區錯誤，請檢查時區名稱", ephemeral=True)

    @app_commands.command(name="countdown", description="設定倒數計時器")
    @app_commands.describe(minutes="分鐘數")
    async def countdown(self, interaction: discord.Interaction, minutes: int):
        if minutes <= 0 or minutes > 60:
            await interaction.response.send_message("❌ 分鐘數必須在 1-60 之間", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="⏰ 倒數計時器已設定",
            description=f"**{minutes}** 分鐘後會提醒你",
            color=discord.Color.orange()
        )
        embed.add_field(name="開始時間", value=datetime.now().strftime("%H:%M:%S"), inline=True)
        embed.add_field(name="結束時間", value=(datetime.now() + timedelta(minutes=minutes)).strftime("%H:%M:%S"), inline=True)
        
        await interaction.response.send_message(embed=embed)
        
        # 設定定時器
        await asyncio.sleep(minutes * 60)
        
        reminder_embed = discord.Embed(
            title="⏰ 時間到！",
            description=f"**{interaction.user.mention}** 你的 {minutes} 分鐘倒數計時結束了！",
            color=discord.Color.red()
        )
        
        try:
            await interaction.followup.send(embed=reminder_embed)
        except:
            # 如果原始訊息無法回覆，嘗試發送新訊息
            await interaction.channel.send(embed=reminder_embed)

    @app_commands.command(name="qrcode", description="生成 QR 碼")
    @app_commands.describe(text="要編碼的文字或網址")
    async def qr_code(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()
        
        try:
            import qrcode
            
            # 生成 QR 碼
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(text)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 轉換為 bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            embed = discord.Embed(
                title="📱 QR 碼",
                description=f"內容: {text}",
                color=discord.Color.blue()
            )
            
            file = discord.File(img_buffer, "qr_code.png")
            embed.set_image(url="attachment://qr_code.png")
            
            await interaction.followup.send(embed=embed, file=file)
            
        except ImportError:
            await interaction.followup.send("❌ 需要安裝 qrcode 套件: `pip install qrcode[pil]`", ephemeral=True)
        except Exception as e:
            logger.error(f"生成 QR 碼失敗: {e}")
            await interaction.followup.send("❌ 生成 QR 碼時發生錯誤", ephemeral=True)

    @app_commands.command(name="password", description="生成隨機密碼")
    @app_commands.describe(
        length="密碼長度",
        include_symbols="包含特殊符號",
        include_numbers="包含數字",
        include_uppercase="包含大寫字母"
    )
    async def generate_password(
        self, 
        interaction: discord.Interaction, 
        length: int = 12,
        include_symbols: bool = True,
        include_numbers: bool = True,
        include_uppercase: bool = True
    ):
        if length < 4 or length > 50:
            await interaction.response.send_message("❌ 密碼長度必須在 4-50 之間", ephemeral=True)
            return
        
        # 字符集
        chars = "abcdefghijklmnopqrstuvwxyz"
        if include_uppercase:
            chars += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if include_numbers:
            chars += "0123456789"
        if include_symbols:
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        # 生成密碼
        password = ''.join(random.choice(chars) for _ in range(length))
        
        embed = discord.Embed(
            title="🔐 隨機密碼",
            color=discord.Color.green()
        )
        embed.add_field(name="密碼", value=f"`{password}`", inline=False)
        embed.add_field(name="長度", value=str(length), inline=True)
        embed.add_field(name="包含符號", value="是" if include_symbols else "否", inline=True)
        embed.add_field(name="包含數字", value="是" if include_numbers else "否", inline=True)
        embed.add_field(name="包含大寫", value="是" if include_uppercase else "否", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(UtilityTools(bot)) 