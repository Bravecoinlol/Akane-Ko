#!/usr/bin/env python3
"""
Discord Bot 配置文件
管理所有環境變數和設定
"""

import os
import json
from typing import Dict, Any
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

class Config:
    """配置管理類"""
    
    def __init__(self):
        # 伺服器配置
        self.SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:8080")
        self.SERVER_HOST = "0.0.0.0"
        self.SERVER_PORT = self._parse_port_from_url(self.SERVER_URL)
        
        # 日誌配置
        self.LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
        self.LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        # 保活配置
        self.PING_INTERVAL = int(os.environ.get("PING_INTERVAL", 25))  # 秒
        self.HEALTH_CHECK_INTERVAL = int(os.environ.get("HEALTH_CHECK_INTERVAL", 60))  # 秒
        self.MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 5))
        self.RETRY_DELAY = int(os.environ.get("RETRY_DELAY", 10))  # 秒
        
        # Discord Bot 配置
        self.DISCORD_TOKEN = self._get_discord_token()
        
        # 外部服務配置
        self.EXTERNAL_PING_URLS = [
            'https://httpbin.org/get',
            'https://api.github.com',
            'https://jsonplaceholder.typicode.com/posts/1',
            'https://httpstat.us/200',
            'https://discord.com/api/v9/gateway'
        ]
        
        # 開發配置
        self.DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
        
    def _parse_port_from_url(self, url: str) -> int:
        """從URL解析端口號"""
        try:
            if ":" in url.split("//")[-1]:
                return int(url.split(":")[-1])
            else:
                return 5000
        except:
            return 8080  # 預設端口
    
    def _get_discord_token(self) -> str:
        """獲取 Discord Bot Token"""
        # 直接從環境變數獲取
        return os.environ.get('TOKEN') or os.environ.get('DISCORD_TOKEN') or ""
    
    def get_server_config(self) -> Dict[str, Any]:
        """獲取伺服器配置"""
        return {
            'host': self.SERVER_HOST,
            'port': self.SERVER_PORT,
            'debug': self.DEBUG,
            'threaded': True,
            'use_reloader': False
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """獲取日誌配置"""
        return {
            'level': self.LOG_LEVEL,
            'format': self.LOG_FORMAT,
            'handlers': [
                'file',
                'console'
            ]
        }
    
    def get_keep_alive_config(self) -> Dict[str, Any]:
        """獲取保活配置"""
        return {
            'server_url': self.SERVER_URL,
            'ping_interval': self.PING_INTERVAL,
            'health_check_interval': self.HEALTH_CHECK_INTERVAL,
            'max_retries': self.MAX_RETRIES,
            'retry_delay': self.RETRY_DELAY,
            'external_ping_urls': self.EXTERNAL_PING_URLS
        }
    
    def get_discord_config(self) -> Dict[str, Any]:
        """獲取 Discord Bot 配置"""
        return {
            'token': self.DISCORD_TOKEN,
            'prefix': '!',
            'intents': ['message_content', 'members', 'guilds']
        }
    
    def print_config(self):
        """打印當前配置"""
        print("🤖 Discord Bot 配置")
        print("=" * 50)
        print(f"🌐 伺服器 URL: {self.SERVER_URL}")
        print(f"🔌 監聽端口: {self.SERVER_PORT}")
        print(f"📝 日誌等級: {self.LOG_LEVEL}")
        print(f"🔄 Ping 間隔: {self.PING_INTERVAL} 秒")
        print(f"🏥 健康檢查間隔: {self.HEALTH_CHECK_INTERVAL} 秒")
        print(f"🔄 最大重試次數: {self.MAX_RETRIES}")
        print(f"⏱️ 重試延遲: {self.RETRY_DELAY} 秒")
        print(f"🐛 除錯模式: {self.DEBUG}")
        print(f"🤖 Discord Token: {'✅ 已設定' if self.DISCORD_TOKEN else '❌ 未設定'}")
        print("=" * 50)

# 全局配置實例
config = Config()

if __name__ == "__main__":
    config.print_config() 