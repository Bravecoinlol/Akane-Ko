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
import asyncio
import re
from discord import ui
import glob

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
                async with session.get(avatar_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        img = Image.open(io.BytesIO(data))
                        img = img.resize((size, size))
                        return img
                    else:
                        logger.error(f"獲取頭像失敗，HTTP狀態碼: {resp.status}")
        except asyncio.TimeoutError:
            logger.error(f"獲取頭像超時: {user.display_name}")
        except aiohttp.ClientError as e:
            logger.error(f"獲取頭像網路錯誤: {e}")
        except Exception as e:
            logger.error(f"獲取頭像失敗: {e}")
        return None

    @app_commands.command(name="頭像", description="顯示用戶的頭像")
    @app_commands.describe(user="要查看頭像的用戶")
    async def avatar(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        try:
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
            
        except Exception as e:
            logger.error(f"顯示頭像失敗: {e}")
            await interaction.response.send_message(f"❌ 顯示頭像失敗：{str(e)}", ephemeral=True)

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
            embed = discord.Embed(
                title="❌ 缺少參數",
                description="請選擇一個特效！",
                color=discord.Color.red()
            )
            embed.add_field(
                name="可用特效",
                value="• 模糊\n• 銳化\n• 黑白\n• 反轉\n• 邊框\n• 圓角",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer()
        
        try:
            target_user = user or interaction.user
            avatar_img = await self.get_avatar(target_user)
            
            if not avatar_img:
                await interaction.followup.send("❌ 無法獲取頭像，請稍後再試", ephemeral=True)
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
                
                await interaction.followup.send(embed=embed, file=file)
            else:
                await interaction.followup.send("❌ 處理圖片時發生錯誤，請稍後再試", ephemeral=True)
                
        except Exception as e:
            logger.error(f"頭像特效處理失敗: {e}")
            await interaction.followup.send(f"❌ 處理頭像特效失敗：{str(e)}", ephemeral=True)

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
            # 檢查文字長度
            if len(top_text) > 50 or len(bottom_text) > 50:
                await interaction.followup.send("❌ 文字太長，請輸入50字以內的文字", ephemeral=True)
                return
            # 獲取圖片
            if image_url:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                            if resp.status == 200:
                                img_data = await resp.read()
                                if len(img_data) > 10 * 1024 * 1024:  # 10MB限制
                                    await interaction.followup.send("❌ 圖片檔案太大，請選擇10MB以內的圖片", ephemeral=True)
                                    return
                                img = Image.open(io.BytesIO(img_data))
                            elif resp.status == 404:
                                await interaction.followup.send("❌ 找不到指定的圖片，請檢查圖片網址", ephemeral=True)
                                return
                            elif resp.status == 403:
                                await interaction.followup.send("❌ 無法存取該圖片，可能是權限問題", ephemeral=True)
                                return
                            else:
                                await interaction.followup.send(f"❌ 無法獲取圖片 (錯誤碼: {resp.status})", ephemeral=True)
                                return
                except asyncio.TimeoutError:
                    await interaction.followup.send("❌ 圖片下載超時，請稍後再試", ephemeral=True)
                    return
                except aiohttp.ClientError as e:
                    await interaction.followup.send(f"❌ 圖片下載失敗：{str(e)}", ephemeral=True)
                    return
            else:
                # 使用預設圖片或用戶頭像
                img = await self.get_avatar(interaction.user, 512)
                if not img:
                    await interaction.followup.send("❌ 無法獲取頭像，請提供圖片網址", ephemeral=True)
                    return

            # 在 meme_generator 取得 font_options 後，檢查 'NotoSansTC' 是否存在，不存在則自動 fallback
            font_options = self.get_font_options()
            if not font_options:
                await interaction.followup.send('❌ 找不到可用字體，請聯絡管理員', ephemeral=True)
                return
            # fallback 預設字體 key
            font_keys = [fo['key'] for fo in font_options]
            default_font = 'NotoSansTC' if 'NotoSansTC' in font_keys else font_keys[0]
            meme_params = {
                'top_text': top_text,
                'bottom_text': bottom_text,
                'font': default_font,
                'bold': False,
                'text_color': '#FFFFFF',
                'stroke_color': '#000000',
                'ratio': '16:9',
                'effect': 'none',
                'image': img
            }
            font_options = self.get_font_options()
            if not font_options:
                await interaction.followup.send('❌ 找不到可用字體，請聯絡管理員', ephemeral=True)
                return
            meme_img = self.create_meme(**meme_params, font_options=font_options)
            img_buffer = io.BytesIO()
            meme_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            embed = discord.Embed(
                title="🎭 迷因生成完成",
                description=f"上方文字: {top_text}\n下方文字: {bottom_text}",
                color=discord.Color.green()
            )
            file = discord.File(img_buffer, "meme.png")
            embed.set_image(url="attachment://meme.png")
            view = MemeEditView(self, interaction.user.id, meme_params, font_options)
            await interaction.followup.send(embed=embed, file=file, view=view)
        except Exception as e:
            logger.error(f"生成迷因失敗: {e}")
            await interaction.followup.send(f"❌ 生成迷因時發生錯誤：{str(e)}", ephemeral=True)

    def get_font_options(self):
        # 掃描字體資料夾，建立字體選單與粗體對應
        font_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '迷因生成字體'))
        font_files = glob.glob(os.path.join(font_dir, '*'))
        font_map = {}
        for f in font_files:
            name = os.path.basename(f)
            if 'NotoSansTC-Regular' in name:
                font_map.setdefault('NotoSansTC', {})['regular'] = f
            elif 'NotoSansTC-Bold' in name:
                font_map.setdefault('NotoSansTC', {})['bold'] = f
            elif 'SourceHanSans-Regular' in name:
                font_map.setdefault('SourceHanSans', {})['regular'] = f
            elif 'SourceHanSans-Bold' in name:
                font_map.setdefault('SourceHanSans', {})['bold'] = f
            elif '微軟正黑體' in name:
                font_map.setdefault('MicrosoftJhengHei', {})['regular'] = f
                font_map.setdefault('MicrosoftJhengHei', {})['bold'] = f
            elif 'jf-openhuninn' in name:
                font_map.setdefault('jfopenhuninn', {})['regular'] = f
                font_map.setdefault('jfopenhuninn', {})['bold'] = f
        font_options = [
            {'key': k, 'label': l, 'regular': v.get('regular'), 'bold': v.get('bold')}
            for k, v, l in [
                ('NotoSansTC', font_map.get('NotoSansTC', {}), 'Noto Sans TC'),
                ('SourceHanSans', font_map.get('SourceHanSans', {}), '思源黑體'),
                ('MicrosoftJhengHei', font_map.get('MicrosoftJhengHei', {}), '微軟正黑體'),
                ('jfopenhuninn', font_map.get('jfopenhuninn', {}), 'jf open 粉圓')
            ] if v.get('regular')
        ]
        return font_options

    def create_meme(self, top_text, bottom_text, font, bold, text_color, stroke_color, ratio, effect, image, font_options):
        """根據參數創建迷因圖片"""
        import logging
        logger = logging.getLogger('ImageTools')
        logger.info(f'create_meme: font={font}, font_options={[fo["key"] for fo in font_options]}')
        try:
            # 處理比例
            img = image.copy()
            target_size = self.get_target_size(ratio)
            # 先調整圖片位置與漸層
            if ratio == '16:9':
                # 圖片靠左，右側漸黑
                img = img.resize((target_size[1], target_size[1]))  # 先正方形
                bg = Image.new('RGB', target_size, (0,0,0))
                bg.paste(img, (0,0))
                # 右側漸層
                mask = Image.linear_gradient('L').resize((target_size[0]//2, target_size[1]))
                mask = mask.point(lambda x: int(x*0.8))
                black = Image.new('RGB', (target_size[0]//2, target_size[1]), (0,0,0))
                bg.paste(black, (target_size[0]//2,0), mask)
                img = bg
            elif ratio == '3:4':
                # 圖片靠上，下方漸黑
                img = img.resize((target_size[0], target_size[0]))
                bg = Image.new('RGB', target_size, (0,0,0))
                bg.paste(img, (0,0))
                mask = Image.linear_gradient('L').rotate(90).resize((target_size[0], target_size[1]//2))
                mask = mask.point(lambda x: int(x*0.8))
                black = Image.new('RGB', (target_size[0], target_size[1]//2), (0,0,0))
                bg.paste(black, (0,target_size[1]//2), mask)
                img = bg
            else:
                img = img.resize(target_size)
            # 圖片效果
            if effect == 'grayscale':
                img = img.convert('L').convert('RGB')
            draw = ImageDraw.Draw(img)
            # 字體檔案
            font_file = None
            for fo in font_options:
                if fo['key'] == font:
                    font_file = fo['bold'] if bold and fo.get('bold') else fo['regular']
                    break
            font_size = int(target_size[1] * 0.08)
            try:
                meme_font = ImageFont.truetype(font_file, font_size)
            except:
                meme_font = ImageFont.load_default()
            stroke_width = 3
            # 文字排版
            if ratio in ['3:4']:
                # 直排
                if top_text:
                    y = 20
                    for ch in top_text:
                        self.draw_text_with_stroke(draw, ch, meme_font, text_color, stroke_color, stroke_width, img.width//2, y, 'mm')
                        y += font_size + 5
                if bottom_text:
                    y = img.height - 60 - (len(bottom_text) * (font_size + 5))
                    for ch in bottom_text:
                        self.draw_text_with_stroke(draw, ch, meme_font, text_color, stroke_color, stroke_width, img.width//2, y, 'mm')
                        y += font_size + 5
            else:
                # 橫排
                if top_text:
                    self.draw_text_with_stroke(draw, top_text, meme_font, text_color, stroke_color, stroke_width, img.width//2, 20, 'mm')
                if bottom_text:
                    self.draw_text_with_stroke(draw, bottom_text, meme_font, text_color, stroke_color, stroke_width, img.width//2, img.height-60, 'mm')
            return img
        except Exception as e:
            logger.error(f"創建迷因失敗: {e}")
            return None

    def get_target_size(self, ratio):
        if ratio == '1:1':
            return (512, 512)
        elif ratio == '4:3':
            return (512, 384)
        elif ratio == '16:9':
            return (512, 288)
        elif ratio == '3:4':
            return (384, 512)
        else:
            return (512, 288)

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
            # 驗證URL格式
            if not image_url.startswith(('http://', 'https://')):
                await interaction.followup.send("❌ 請提供有效的圖片網址", ephemeral=True)
                return
            
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        img_data = await resp.read()
                        
                        # 檢查檔案大小
                        if len(img_data) > 25 * 1024 * 1024:  # 25MB限制
                            await interaction.followup.send("❌ 圖片檔案太大，無法處理", ephemeral=True)
                            return
                        
                        try:
                            img = Image.open(io.BytesIO(img_data))
                        except Exception as e:
                            await interaction.followup.send("❌ 無法識別圖片格式，請確認是有效的圖片檔案", ephemeral=True)
                            return
                        
                        embed = discord.Embed(
                            title="📊 圖片資訊",
                            color=discord.Color.blue()
                        )
                        
                        embed.add_field(name="尺寸", value=f"{img.width} x {img.height} 像素", inline=True)
                        embed.add_field(name="格式", value=img.format or "未知", inline=True)
                        embed.add_field(name="模式", value=img.mode, inline=True)
                        embed.add_field(name="檔案大小", value=f"{len(img_data) / 1024:.1f} KB", inline=True)
                        
                        embed.set_image(url=image_url)
                        
                        await interaction.followup.send(embed=embed)
                        
                    elif resp.status == 404:
                        await interaction.followup.send("❌ 找不到指定的圖片，請檢查圖片網址", ephemeral=True)
                    elif resp.status == 403:
                        await interaction.followup.send("❌ 無法存取該圖片，可能是權限問題", ephemeral=True)
                    elif resp.status == 400:
                        await interaction.followup.send("❌ 圖片網址格式錯誤", ephemeral=True)
                    else:
                        await interaction.followup.send(f"❌ 無法獲取圖片 (錯誤碼: {resp.status})", ephemeral=True)
                        
        except asyncio.TimeoutError:
            await interaction.followup.send("❌ 圖片下載超時，請稍後再試", ephemeral=True)
        except aiohttp.ClientError as e:
            await interaction.followup.send(f"❌ 圖片下載失敗：{str(e)}", ephemeral=True)
        except Exception as e:
            logger.error(f"獲取圖片資訊失敗: {e}")
            await interaction.followup.send(f"❌ 獲取圖片資訊時發生錯誤：{str(e)}", ephemeral=True)

class MemeEditView(ui.View):
    def __init__(self, cog, author_id, meme_params, font_options, timeout=300):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.author_id = author_id
        self.meme_params = meme_params  # dict: {font, bold, text_color, stroke_color, ratio, ...}
        self.font_options = font_options
        self.update_items()

    def update_items(self):
        self.clear_items()
        self.add_item(FontSelect(self.font_options, self.meme_params['font'], self.meme_params['bold']))
        self.add_item(BoldButton(self.meme_params['bold']))
        self.add_item(ColorSelect('文字顏色（修改字體顏色）', 'text_color', self.meme_params['text_color'], row=2))
        self.add_item(ColorSelect('描邊顏色（修改描邊顏色）', 'stroke_color', self.meme_params['stroke_color'], row=3))
        self.add_item(RatioSelect(self.meme_params['ratio'], row=4))
        self.add_item(ImageEffectSelect(self.meme_params.get('effect', 'none'), row=5))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message('❌ 只有發起人可以調整迷因參數', ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

class FontSelect(ui.Select):
    def __init__(self, font_options, current_font, is_bold):
        font_keys = [fo['key'] for fo in font_options]
        if current_font not in font_keys and font_options:
            current_font = font_options[0]['key']
        options = [
            discord.SelectOption(label=fo['label'], value=fo['key'], default=(fo['key']==current_font))
            for fo in font_options
        ]
        if not options:
            super().__init__(placeholder='找不到可用字體', options=[discord.SelectOption(label='無可用字體', value='none')], row=0, disabled=True)
        else:
            super().__init__(placeholder='選擇字體（修改字體）', options=options, row=0)
        self.font_options = font_options
        self.is_bold = is_bold
    async def callback(self, interaction: discord.Interaction):
        view: MemeEditView = self.view
        if not self.values:
            # fallback: 用現有 meme_params['font']，若不存在則用 font_options[0]['key']
            font_keys = [fo['key'] for fo in self.font_options]
            fallback_font = view.meme_params.get('font')
            if fallback_font not in font_keys and font_keys:
                fallback_font = font_keys[0]
            logger.warning(f'FontSelect callback: self.values 為空，自動 fallback 用 {fallback_font}')
            view.meme_params['font'] = fallback_font
            await interaction.response.send_message(f'未選擇任何字體，已自動套用 {fallback_font}', ephemeral=True)
            await update_meme_message(interaction, view)
            return
        view.meme_params['font'] = self.values[0]
        logger.info(f'FontSelect callback: 選擇字體 {self.values[0]}')
        await update_meme_message(interaction, view)

class BoldButton(ui.Button):
    def __init__(self, is_bold):
        label = '粗體' if not is_bold else '一般'
        style = discord.ButtonStyle.primary if not is_bold else discord.ButtonStyle.secondary
        super().__init__(label=label, style=style, row=1)

    async def callback(self, interaction: discord.Interaction):
        view: MemeEditView = self.view
        view.meme_params['bold'] = not view.meme_params['bold']
        await update_meme_message(interaction, view)

class ColorSelect(ui.Select):
    COLOR_PRESETS = [
        ('白色', '#FFFFFF'),
        ('黑色', '#000000'),
        ('紅色', '#FF0000'),
        ('黃色', '#FFFF00'),
        ('綠色', '#00FF00'),
        ('藍色', '#0000FF'),
        ('自訂', 'custom')
    ]
    def __init__(self, label, param_key, current_color, row=1):
        options = [
            discord.SelectOption(label=lbl, value=val, default=(val==current_color))
            for lbl, val in self.COLOR_PRESETS if val != 'custom'
        ]
        options.append(discord.SelectOption(label='自訂顏色（#RRGGBB）', value='custom', default=(not any(current_color==v for _,v in self.COLOR_PRESETS))))
        super().__init__(placeholder=label, options=options, row=row)
        self.param_key = param_key
        self.current_color = current_color

    async def callback(self, interaction: discord.Interaction):
        if not self.values:
            await interaction.response.send_message('未選擇任何顏色，參數未變更', ephemeral=True)
            return
        view: MemeEditView = self.view
        val = self.values[0]
        if val == 'custom':
            await interaction.response.send_modal(ColorInputModal(self.param_key, self.current_color))
        else:
            view.meme_params[self.param_key] = val
            await update_meme_message(interaction, view)

class ColorInputModal(ui.Modal, title='自訂顏色'):
    color = ui.TextInput(label='請輸入 #RRGGBB', placeholder='#FFFFFF', required=True)
    def __init__(self, param_key, current_color):
        super().__init__()
        self.param_key = param_key
        self.color.default = current_color
    async def on_submit(self, interaction: discord.Interaction):
        color_val = self.color.value.strip()
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color_val):
            await interaction.response.send_message('❌ 顏色格式錯誤，請輸入 #RRGGBB', ephemeral=True)
            return
        view: MemeEditView = self.parent
        view.meme_params[self.param_key] = color_val
        await update_meme_message(interaction, view)

class RatioSelect(ui.Select):
    RATIO_OPTIONS = [
        ('1:1', '1:1'),
        ('4:3', '4:3'),
        ('16:9', '16:9'),
        ('3:4', '3:4')
    ]
    def __init__(self, current_ratio, row=4):
        options = [
            discord.SelectOption(label=lbl, value=val, default=(val==current_ratio))
            for lbl, val in self.RATIO_OPTIONS
        ]
        super().__init__(placeholder='選擇圖片比例（修改圖片格式）', options=options, row=row)
    async def callback(self, interaction: discord.Interaction):
        if not self.values:
            await interaction.response.send_message('未選擇任何比例，參數未變更', ephemeral=True)
            return
        view: MemeEditView = self.view
        view.meme_params['ratio'] = self.values[0]
        await update_meme_message(interaction, view)

class ImageEffectSelect(ui.Select):
    EFFECT_OPTIONS = [
        ('原圖', 'none'),
        ('黑白', 'grayscale')
    ]
    def __init__(self, current_effect, row=5):
        options = [
            discord.SelectOption(label=lbl, value=val, default=(val==current_effect))
            for lbl, val in self.EFFECT_OPTIONS
        ]
        super().__init__(placeholder='選擇圖片效果（修改圖片顏色）', options=options, row=row)
    async def callback(self, interaction: discord.Interaction):
        if not self.values:
            await interaction.response.send_message('未選擇任何圖片效果，參數未變更', ephemeral=True)
            return
        view: MemeEditView = self.view
        view.meme_params['effect'] = self.values[0]
        await update_meme_message(interaction, view)

async def update_meme_message(interaction, view: MemeEditView):
    logger = logging.getLogger('ImageTools')
    logger.info(f'update_meme_message: params={view.meme_params}')
    await interaction.response.defer()
    meme_img = view.cog.create_meme(
        view.meme_params['top_text'], view.meme_params['bottom_text'], view.meme_params['font'], view.meme_params['bold'],
        view.meme_params['text_color'], view.meme_params['stroke_color'], view.meme_params['ratio'], view.meme_params['effect'], view.meme_params['image'], view.font_options
    )
    img_buffer = io.BytesIO()
    meme_img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    file = discord.File(img_buffer, 'meme.png')
    embed = discord.Embed(title='🎭 迷因生成', color=discord.Color.green())
    embed.set_image(url='attachment://meme.png')
    await interaction.message.edit(embed=embed, attachments=[file], view=view)

async def setup(bot):
    await bot.add_cog(ImageTools(bot)) 