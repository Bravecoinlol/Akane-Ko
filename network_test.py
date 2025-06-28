#!/usr/bin/env python3
"""
網路連線診斷腳本
用於測試 FreeServer 環境的網路連線問題
"""

import socket
import requests
import subprocess
import platform
import os
from datetime import datetime

def test_local_connection():
    """測試本地連線"""
    print("🔍 測試本地連線...")
    ports = [8080, 22405, 5000]  # 測試多個端口
    
    for port in ports:
        try:
            # 測試本地端口
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                print(f"✅ 本地端口 {port} 可以連線")
            else:
                print(f"❌ 本地端口 {port} 無法連線")
        except Exception as e:
            print(f"❌ 本地端口 {port} 測試失敗: {e}")
    
    # 測試 8080 端口
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8080))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"❌ 本地連線測試失敗: {e}")
        return False

def test_external_connection():
    """測試外部連線"""
    print("🔍 測試外部連線...")
    test_urls = [
        "http://awa.freeserver.tw:22405",
        "https://httpbin.org/get",
        "https://api.github.com"
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=10)
            print(f"✅ {url} - 狀態碼: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {url} - 連線失敗")
        except requests.exceptions.Timeout:
            print(f"⏰ {url} - 連線超時")
        except Exception as e:
            print(f"❌ {url} - 錯誤: {e}")

def get_network_info():
    """獲取網路資訊"""
    print("🔍 網路資訊...")
    
    # 獲取本機 IP
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"📱 主機名: {hostname}")
        print(f"🏠 本機 IP: {local_ip}")
    except Exception as e:
        print(f"❌ 無法獲取本機 IP: {e}")
    
    # 獲取公開 IP
    try:
        response = requests.get('https://httpbin.org/ip', timeout=10)
        public_ip = response.json().get('origin', '未知')
        print(f"🌐 公開 IP: {public_ip}")
    except Exception as e:
        print(f"❌ 無法獲取公開 IP: {e}")
    
    # 系統資訊
    print(f"💻 作業系統: {platform.system()} {platform.release()}")
    print(f"🐍 Python 版本: {platform.python_version()}")

def test_dns_resolution():
    """測試 DNS 解析"""
    print("🔍 測試 DNS 解析...")
    domains = ["awa.freeserver.tw", "google.com", "github.com"]
    
    for domain in domains:
        try:
            ip = socket.gethostbyname(domain)
            print(f"✅ {domain} -> {ip}")
        except socket.gaierror as e:
            print(f"❌ {domain} - DNS 解析失敗: {e}")

def main():
    """主函數"""
    print("🤖 網路診斷開始")
    print("=" * 50)
    print(f"⏰ 時間: {datetime.now()}")
    print("=" * 50)
    
    # 測試網路資訊
    get_network_info()
    print()
    
    # 測試 DNS 解析
    test_dns_resolution()
    print()
    
    # 測試外部連線
    test_external_connection()
    print()
    
    # 測試本地連線
    local_ok = test_local_connection()
    print()
    
    # 總結
    print("=" * 50)
    print("📋 診斷總結:")
    if local_ok:
        print("✅ 本地連線正常")
    else:
        print("❌ 本地連線有問題")
    print("💡 建議:")
    print("   1. 如果本地連線有問題，檢查伺服器是否正在運行")
    print("   2. 如果外部連線有問題，可能是 FreeServer 網路限制")
    print("   3. 嘗試使用 localhost 或 127.0.0.1 替代外網 IP")
    print("=" * 50)

if __name__ == "__main__":
    main() 