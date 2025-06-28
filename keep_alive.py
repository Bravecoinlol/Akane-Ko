#!/usr/bin/env python3
"""
Discord Bot 保活腳本
用於保持伺服器活躍狀態，避免進入休眠
"""

import requests
import time
import logging
import json
from datetime import datetime
import os
from config import config

# 設定日誌
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    format=config.LOG_FORMAT,
    handlers=[
        logging.FileHandler('keep_alive.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class KeepAlive:
    def __init__(self):
        # 使用配置系統
        keep_alive_config = config.get_keep_alive_config()
        
        self.server_url = keep_alive_config['server_url']
        self.ping_interval = keep_alive_config['ping_interval']
        self.health_check_interval = keep_alive_config['health_check_interval']
        self.max_retries = keep_alive_config['max_retries']
        self.retry_delay = keep_alive_config['retry_delay']
        
        self.stats = {
            'start_time': datetime.now(),
            'ping_count': 0,
            'success_count': 0,
            'failure_count': 0,
            'last_success': None,
            'last_failure': None
        }
        
        # 外部 ping URL 列表
        self.external_ping_urls = keep_alive_config['external_ping_urls']
        
        logger.info(f"🔧 保活腳本初始化完成 - 伺服器: {self.server_url}")
        logger.info(f"📋 配置: Ping間隔={self.ping_interval}s, 健康檢查間隔={self.health_check_interval}s")
        
    def ping_server(self):
        """Ping 本地伺服器"""
        try:
            # 嘗試連線到設定的伺服器
            response = requests.get(f"{self.server_url}/ping", timeout=10)
            if response.status_code == 200:
                self.stats['success_count'] += 1
                self.stats['last_success'] = datetime.now()
                logger.info(f"✅ 伺服器 Ping 成功 (狀態碼: {response.status_code})")
                return True
            else:
                self.stats['failure_count'] += 1
                self.stats['last_failure'] = datetime.now()
                logger.warning(f"⚠️ 伺服器 Ping 警告 (狀態碼: {response.status_code})")
                return False
                
        except requests.exceptions.ConnectionError as e:
            self.stats['failure_count'] += 1
            self.stats['last_failure'] = datetime.now()
            logger.error(f"❌ 伺服器連線失敗: {e}")
            
            # 如果是外網 IP 連線失敗，嘗試本地連線
            if "awa.freeserver.tw" in self.server_url:
                logger.info("🔄 嘗試本地連線作為備用...")
                try:
                    local_response = requests.get("http://localhost:8080/ping", timeout=5)
                    if local_response.status_code == 200:
                        logger.info("✅ 本地連線成功")
                        return True
                except:
                    pass
            
            return False
        except requests.exceptions.Timeout as e:
            self.stats['failure_count'] += 1
            self.stats['last_failure'] = datetime.now()
            logger.error(f"⏰ 伺服器連線超時: {e}")
            return False
        except Exception as e:
            self.stats['failure_count'] += 1
            self.stats['last_failure'] = datetime.now()
            logger.error(f"❌ 伺服器 Ping 失敗: {e}")
            return False
    
    def health_check(self):
        """健康檢查"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=15)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"🏥 健康檢查成功 - 狀態: {data.get('status', 'unknown')}")
                return True
            else:
                logger.warning(f"⚠️ 健康檢查警告 (狀態碼: {response.status_code})")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 健康檢查失敗: {e}")
            return False
    
    def external_ping(self):
        """Ping 外部服務以保持網路活躍"""
        for url in self.external_ping_urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code in [200, 401, 403]:  # 接受 401/403 (Discord API)
                    logger.info(f"🌐 外部 Ping 成功: {url}")
                    return True
            except:
                continue
        
        logger.warning("⚠️ 所有外部 Ping 都失敗")
        return False
    
    def get_status(self):
        """獲取伺服器狀態"""
        try:
            response = requests.get(f"{self.server_url}/status", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except:
            return None
    
    def run(self):
        """主執行循環"""
        logger.info(f"🚀 啟動保活腳本 (伺服器: {self.server_url})")
        logger.info(f"📊 配置: Ping間隔={self.ping_interval}s, 健康檢查間隔={self.health_check_interval}s")
        
        last_health_check = 0
        
        while True:
            try:
                current_time = time.time()
                self.stats['ping_count'] += 1
                
                # 執行 ping
                ping_success = self.ping_server()
                
                # 定期健康檢查
                if current_time - last_health_check >= self.health_check_interval:
                    self.health_check()
                    last_health_check = current_time
                
                # 如果 ping 失敗，嘗試外部 ping
                if not ping_success:
                    logger.warning("🔄 嘗試外部 Ping 作為備用")
                    self.external_ping()
                
                # 顯示統計資訊
                if self.stats['ping_count'] % 10 == 0:  # 每10次顯示一次統計
                    self.show_stats()
                
                # 等待下次 ping
                time.sleep(self.ping_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 收到中斷信號，正在停止...")
                break
            except Exception as e:
                logger.error(f"❌ 執行循環錯誤: {e}")
                time.sleep(self.retry_delay)
    
    def show_stats(self):
        """顯示統計資訊"""
        uptime = datetime.now() - self.stats['start_time']
        success_rate = (self.stats['success_count'] / self.stats['ping_count']) * 100 if self.stats['ping_count'] > 0 else 0
        
        logger.info(f"📊 統計: Ping={self.stats['ping_count']}, "
                   f"成功={self.stats['success_count']}, "
                   f"失敗={self.stats['failure_count']}, "
                   f"成功率={success_rate:.1f}%, "
                   f"運行時間={str(uptime).split('.')[0]}")

def main():
    """主函數"""
    keep_alive = KeepAlive()
    
    # 檢查伺服器是否可用
    logger.info("🔍 檢查伺服器可用性...")
    if keep_alive.get_status():
        logger.info("✅ 伺服器可用，開始保活循環")
        keep_alive.run()
    else:
        logger.error("❌ 伺服器不可用，請檢查伺服器是否正在運行")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 