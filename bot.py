import discord
import json
import os
import asyncio
import aiohttp
import logging
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands
import logging.handlers
from datetime import datetime

# 載入 .env 檔案
load_dotenv()

# 設定 logging
def setup_logging():
    """設定詳細的 logging 配置"""
    # 創建 logs 目錄
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 設定 log 格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 設定根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 清除現有的 handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 控制台輸出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 檔案輸出 - 一般日誌
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/bot.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 檔案輸出 - 錯誤日誌
    error_handler = logging.handlers.RotatingFileHandler(
        'logs/error.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # 設定 Discord.py 的 logging
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.WARNING)
    
    # 設定其他模組的 logging
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    
    logger = logging.getLogger('Bot')
    logger.info("Logging 系統已設定完成")

# 初始化 logging
setup_logging()
logger = logging.getLogger('Bot')

# 載入設定
def load_config():
    """載入 bot 配置"""
    try:
        with open('setting.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            logger.info("設定檔案載入成功")
            return config
    except FileNotFoundError:
        logger.warning("setting.json 不存在，使用預設配置")
        return {
            "token": os.getenv('TOKEN') or os.getenv('DISCORD_TOKEN'),
            "prefix": "!",
            "intents": ["message_content", "members", "guilds"]
        }
    except Exception as e:
        logger.error(f"載入設定檔案失敗: {e}")
        return {
            "token": os.getenv('TOKEN') or os.getenv('DISCORD_TOKEN'),
            "prefix": "!",
            "intents": ["message_content", "members", "guilds"]
        }

# 載入配置
config = load_config()

# 設定 intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

# 創建 bot 實例
bot = commands.Bot(command_prefix=config.get('prefix', '!'), intents=intents)

# 保活函式：每 4 分鐘 ping 一次，避免 FreeServer 睡眠
async def keep_alive():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                # 嘗試多個外部服務
                urls = [
                    "https://discord.com",
                    "https://httpbin.org/get",
                    "https://api.github.com"
                ]
                
                for url in urls:
                    try:
                        await session.get(url, timeout=10)
                        logger.debug(f"保活 ping 成功: {url}")
                        break  # 成功一個就跳出
                    except:
                        continue
                        
        except Exception as e:
            logger.error(f"保活 ping 失敗: {e}")
        await asyncio.sleep(240)

# Bot 啟動時觸發
@bot.event
async def on_ready():
    """Bot 啟動完成事件"""
    logger.info(f"Bot 已登入為 {bot.user.name}")
    logger.info(f"Bot ID: {bot.user.id}")
    logger.info(f"已連接的伺服器數量: {len(bot.guilds)}")
    
    # 同步 slash commands
    try:
        synced = await bot.tree.sync()
        logger.info(f"已同步 {len(synced)} 個 slash commands")
    except Exception as e:
        logger.error(f"同步 slash commands 失敗: {e}")

@bot.event
async def on_guild_join(guild):
    """加入新伺服器時的事件"""
    logger.info(f"加入新伺服器: {guild.name} (ID: {guild.id})")

@bot.event
async def on_guild_remove(guild):
    """離開伺服器時的事件"""
    logger.info(f"離開伺服器: {guild.name} (ID: {guild.id})")

@bot.event
async def on_command_error(ctx, error):
    """命令錯誤處理"""
    if isinstance(error, commands.CommandNotFound):
        return
    
    logger.error(f"命令錯誤 - 用戶: {ctx.author.name}, 命令: {ctx.command}, 錯誤: {error}")
    
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ 您沒有權限執行此命令")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("❌ Bot 缺少必要權限")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏰ 請等待 {error.retry_after:.1f} 秒後再試")
    else:
        await ctx.send(f"❌ 執行命令時發生錯誤: {error}")

# 載入 cogs
async def load_cogs():
    """自動載入所有 cogs"""
    import os
    
    # 掃描 cogs 資料夾
    cogs_dir = 'cogs'
    if not os.path.exists(cogs_dir):
        logger.warning(f"cogs 資料夾不存在: {cogs_dir}")
        return
    
    # 獲取所有 .py 檔案
    cog_files = []
    for filename in os.listdir(cogs_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            cog_name = filename[:-3]  # 移除 .py 副檔名
            cog_files.append(f'cogs.{cog_name}')
    
    logger.info(f"發現 {len(cog_files)} 個 cog 檔案: {cog_files}")
    
    # 載入每個 cog
    loaded_cogs = []
    failed_cogs = []
    
    for cog in cog_files:
        try:
            await bot.load_extension(cog)
            loaded_cogs.append(cog)
            logger.info(f"✅ 已載入 cog: {cog}")
        except Exception as e:
            failed_cogs.append((cog, str(e)))
            logger.error(f"❌ 載入 cog {cog} 失敗: {e}")
    
    # 顯示載入結果
    logger.info(f"📊 Cog 載入完成: {len(loaded_cogs)} 成功, {len(failed_cogs)} 失敗")
    
    if failed_cogs:
        logger.warning("失敗的 cogs:")
        for cog, error in failed_cogs:
            logger.warning(f"  - {cog}: {error}")

# 啟動 bot
async def main():
    """主函數"""
    logger.info("正在啟動 Bot...")
    
    # 載入 cogs
    await load_cogs()
    
    # 啟動 bot - 直接從環境變數獲取 TOKEN
    token = os.getenv('TOKEN') or os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("未找到 Discord Token")
        logger.error("請在 .env 檔案中設定 TOKEN 或 DISCORD_TOKEN")
        return
    
    logger.info("✅ Discord Token 已找到")
    
    try:
        await bot.start(token)
    except Exception as e:
        logger.error(f"Bot 啟動失敗: {e}")

# 執行主程式
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot 已停止")
    except Exception as e:
        logger.error(f"❌ 主程式異常：{e}")

# 建議：在 cogs/Extensions.py 的管理指令加上 @commands.is_owner()，只允許擁有者使用！
