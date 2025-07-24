#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
啟動網頁儀表板
"""

import os
import sys
import subprocess
import time

def check_dependencies():
    """檢查並安裝依賴"""
    try:
        import flask
        import psutil
        from PIL import Image
        print("✓ 所有依賴已安裝")
        return True
    except ImportError as e:
        print(f"✗ 缺少依賴: {e}")
        print("正在安裝依賴...")
        
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "web_requirements.txt"])
            print("✓ 依賴安裝完成")
            return True
        except subprocess.CalledProcessError:
            print("✗ 依賴安裝失敗")
            return False

def create_templates_dir():
    """創建templates目錄"""
    if not os.path.exists('templates'):
        os.makedirs('templates')
        print("✓ 創建templates目錄")

def main():
    print("=== Discord Bot 網頁儀表板啟動器 ===")
    
    # 檢查依賴
    if not check_dependencies():
        print("無法啟動儀表板，請手動安裝依賴")
        return
    
    # 創建必要目錄
    create_templates_dir()
    
    # 檢查必要文件
    required_files = ['web_dashboard.py', 'templates/dashboard.html']
    for file in required_files:
        if not os.path.exists(file):
            print(f"✗ 缺少必要文件: {file}")
            return
    
    print("✓ 所有文件檢查完成")
    
    # 啟動儀表板
    print("\n啟動網頁儀表板...")
    print("訪問地址: http://localhost:5000")
    print("按 Ctrl+C 停止服務")
    
    try:
        subprocess.run([sys.executable, "web_dashboard.py"])
    except KeyboardInterrupt:
        print("\n儀表板已停止")
    except Exception as e:
        print(f"啟動失敗: {e}")

if __name__ == "__main__":
    main() 