import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import io
import json
import os
import logging
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import random
from typing import Optional

logger = logging.getLogger('ImageTools')

class ImageTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.font_path = None
        self.setup_font()

    def setup_font(self):
        """設定字體路徑"""
        # 嘗試找到系統字體
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Arial.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "arial.ttf"
        ]
        
        for path in font_paths:
            if os.path.exists(path):
                self.font_path = path
                break
        
        if not self.font_path:
            logger.warning("找不到字體檔案，將使用預設字體")

    async def get_avatar(self, user: discord.User, size: int = 256) -> Optional[Image.Image]:
        """獲取用戶頭像"""
        try:
            avatar_url = user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        img = Image.open(io.BytesIO(data))
                        img = img.resize((size, size))
                        return img
        except Exception as e:
            logger.error(f"獲取頭像失敗: {e}")
        return None

    @app_commands.command(name="頭像", description="顯示用戶的頭像")
    @app_commands.describe(user="要查看頭像的用戶")
    async def avatar(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        target_user = user or interaction.user
        
        embed = discord.Embed(
            title=f"🖼️ {target_user.display_name} 的頭像",
            color=discord.Color.blue()
        )
        
        # 添加不同尺寸的頭像
        embed.set_image(url=target_user.display_avatar.url)
        embed.add_field(
            name="下載連結",
            value=f"[原始尺寸]({target_user.display_avatar.url})",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="頭像效果", description="為頭像添加特效")
    @app_commands.describe(
        user="要處理的用戶",
        effect="選擇特效"
    )
    @app_commands.choices(effect=[
        app_commands.Choice(name="模糊", value="blur"),
        app_commands.Choice(name="銳化", value="sharpen"),
        app_commands.Choice(name="黑白", value="grayscale"),
        app_commands.Choice(name="反轉", value="invert"),
        app_commands.Choice(name="邊框", value="border"),
        app_commands.Choice(name="圓角", value="rounded")
    ])
    async def avatar_effect(self, interaction: discord.Interaction, user: Optional[discord.User] = None, effect: app_commands.Choice[str] = None):
        if not effect:
            await interaction.response.send_message("請選擇一個特效！", ephemeral=True)
            return

        target_user = user or interaction.user
        avatar_img = await self.get_avatar(target_user)
        
        if not avatar_img:
            await interaction.response.send_message("無法獲取頭像！", ephemeral=True)
            return

        # 應用特效
        processed_img = self.apply_effect(avatar_img, effect.value)
        
        if processed_img:
            # 轉換為 bytes
            img_buffer = io.BytesIO()
            processed_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            embed = discord.Embed(
                title=f"🎨 {target_user.display_name} 的頭像特效",
                description=f"特效: {effect.name}",
                color=discord.Color.purple()
            )
            
            file = discord.File(img_buffer, f"avatar_{effect.value}.png")
            embed.set_image(url=f"attachment://avatar_{effect.value}.png")
            
            await interaction.response.send_message(embed=embed, file=file)
        else:
            await interaction.response.send_message("處理圖片時發生錯誤！", ephemeral=True)

    def apply_effect(self, img: Image.Image, effect: str) -> Optional[Image.Image]:
        """應用圖片特效"""
        try:
            if effect == "blur":
                return img.filter(ImageFilter.BLUR)
            elif effect == "sharpen":
                return img.filter(ImageFilter.SHARPEN)
            elif effect == "grayscale":
                return img.convert('L').convert('RGB')
            elif effect == "invert":
                return Image.eval(img, lambda x: 255 - x)
            elif effect == "border":
                # 添加邊框
                border_size = 10
                new_img = Image.new('RGB', (img.width + border_size*2, img.height + border_size*2), 'white')
                new_img.paste(img, (border_size, border_size))
                return new_img
            elif effect == "rounded":
                # 創建圓角效果
                mask = Image.new('L', img.size, 0)
                draw = ImageDraw.Draw(mask)
                draw.rounded_rectangle([0, 0, img.width, img.height], radius=50, fill=255)
                output = Image.new('RGBA', img.size, (0, 0, 0, 0))
                output.paste(img, (0, 0))
                output.putalpha(mask)
                return output
        except Exception as e:
            logger.error(f"應用特效失敗: {e}")
        return None

    @app_commands.command(name="迷因生成", description="生成迷因圖片")
    @app_commands.describe(
        top_text="上方文字",
        bottom_text="下方文字",
        image_url="圖片網址（可選）"
    )
    async def meme_generator(self, interaction: discord.Interaction, top_text: str, bottom_text: str, image_url: Optional[str] = None):
        await interaction.response.defer()
        
        try:
            # 獲取圖片
            if image_url:
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url) as resp:
                        if resp.status != 200:
                            await interaction.followup.send("無法獲取圖片！", ephemeral=True)
                            return
                        img_data = await resp.read()
                        img = Image.open(io.BytesIO(img_data))
            else:
                # 使用預設圖片或用戶頭像
                img = await self.get_avatar(interaction.user, 512)
                if not img:
                    await interaction.followup.send("無法獲取圖片！", ephemeral=True)
                    return

            # 調整圖片大小
            img = img.resize((512, 512))
            
            # 創建迷因
            meme_img = self.create_meme(img, top_text, bottom_text)
            
            if meme_img:
                # 轉換為 bytes
                img_buffer = io.BytesIO()
                meme_img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                file = discord.File(img_buffer, "meme.png")
                await interaction.followup.send(file=file)
            else:
                await interaction.followup.send("生成迷因失敗！", ephemeral=True)
                
        except Exception as e:
            logger.error(f"生成迷因失敗: {e}")
            await interaction.followup.send("生成迷因時發生錯誤！", ephemeral=True)

    def create_meme(self, img: Image.Image, top_text: str, bottom_text: str) -> Optional[Image.Image]:
        """創建迷因圖片"""
        try:
            # 創建繪圖物件
            draw = ImageDraw.Draw(img)
            
            # 設定字體
            font_size = 40
            if self.font_path:
                try:
                    font = ImageFont.truetype(self.font_path, font_size)
                except:
                    font = ImageFont.load_default()
            else:
                font = ImageFont.load_default()
            
            # 文字顏色和描邊
            text_color = 'white'
            stroke_color = 'black'
            stroke_width = 3
            
            # 繪製上方文字
            if top_text:
                self.draw_text_with_stroke(draw, top_text, font, text_color, stroke_color, stroke_width, img.width//2, 20, 'center')
            
            # 繪製下方文字
            if bottom_text:
                self.draw_text_with_stroke(draw, bottom_text, font, text_color, stroke_color, stroke_width, img.width//2, img.height-60, 'center')
            
            return img
            
        except Exception as e:
            logger.error(f"創建迷因失敗: {e}")
            return None

    def draw_text_with_stroke(self, draw, text, font, text_color, stroke_color, stroke_width, x, y, anchor):
        """繪製帶描邊的文字"""
        # 繪製描邊
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, font=font, fill=stroke_color, anchor=anchor)
        
        # 繪製主文字
        draw.text((x, y), text, font=font, fill=text_color, anchor=anchor)

    @app_commands.command(name="圖片資訊", description="顯示圖片的基本資訊")
    @app_commands.describe(image_url="圖片網址")
    async def image_info(self, interaction: discord.Interaction, image_url: str):
        await interaction.response.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("無法獲取圖片！", ephemeral=True)
                        return
                    
                    img_data = await resp.read()
                    img = Image.open(io.BytesIO(img_data))
                    
                    embed = discord.Embed(
                        title="📊 圖片資訊",
                        color=discord.Color.blue()
                    )
                    
                    embed.add_field(name="尺寸", value=f"{img.width} x {img.height} 像素", inline=True)
                    embed.add_field(name="格式", value=img.format, inline=True)
                    embed.add_field(name="模式", value=img.mode, inline=True)
                    embed.add_field(name="檔案大小", value=f"{len(img_data) / 1024:.1f} KB", inline=True)
                    
                    embed.set_image(url=image_url)
                    
                    await interaction.followup.send(embed=embed)
                    
        except Exception as e:
            logger.error(f"獲取圖片資訊失敗: {e}")
            await interaction.followup.send("獲取圖片資訊時發生錯誤！", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ImageTools(bot)) 