#!/usr/bin/env python3
"""
測試重複播放功能
"""

import asyncio
import discord
from discord.ext import commands
import logging

# 設定日誌
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('RepeatTest')

class TestMusicPlayer:
    def __init__(self):
        self.queue = []
        self.current = None
        self.repeat = False
        self.volume = 0.5

    def add(self, song):
        self.queue.append(song)
        print(f"新增歌曲：{song['title']}")

    def next(self):
        # 如果開啟重複播放且有當前歌曲
        if self.repeat and self.current:
            print(f"重複播放：{self.current['title']}")
            return self.current
        
        # 如果隊列中有歌曲
        if self.queue:
            self.current = self.queue.pop(0)
            print(f"取出下一首：{self.current['title']}")
            return self.current
        
        # 如果沒有歌曲且開啟重複播放，但沒有當前歌曲
        if self.repeat and not self.current:
            print("重複播放開啟但沒有當前歌曲")
            return None
            
        # 播放隊列空了
        self.current = None
        print("播放隊列空了")
        return None

    def toggle_repeat(self):
        self.repeat = not self.repeat
        status = "開啟" if self.repeat else "關閉"
        print(f"重複播放：{status}")
        return self.repeat

def test_repeat_function():
    """測試重複播放功能"""
    print("🧪 測試重複播放功能")
    print("=" * 30)
    
    # 創建測試播放器
    player = TestMusicPlayer()
    
    # 添加測試歌曲
    test_songs = [
        {"title": "測試歌曲 1", "url": "test1"},
        {"title": "測試歌曲 2", "url": "test2"},
        {"title": "測試歌曲 3", "url": "test3"}
    ]
    
    for song in test_songs:
        player.add(song)
    
    print(f"\n📋 初始隊列：{len(player.queue)} 首歌曲")
    
    # 測試 1：正常播放（重複播放關閉）
    print("\n🔍 測試 1：正常播放（重複播放關閉）")
    print("-" * 40)
    
    for i in range(5):
        song = player.next()
        if song:
            print(f"播放：{song['title']}")
        else:
            print("沒有歌曲可播放")
    
    # 重置播放器
    player = TestMusicPlayer()
    for song in test_songs:
        player.add(song)
    
    # 測試 2：重複播放開啟
    print("\n🔍 測試 2：重複播放開啟")
    print("-" * 40)
    
    # 先播放一首歌
    song = player.next()
    if song:
        print(f"播放：{song['title']}")
    
    # 開啟重複播放
    player.toggle_repeat()
    
    # 測試重複播放
    for i in range(5):
        song = player.next()
        if song:
            print(f"播放：{song['title']}")
        else:
            print("沒有歌曲可播放")
    
    # 測試 3：重複播放但沒有當前歌曲
    print("\n🔍 測試 3：重複播放但沒有當前歌曲")
    print("-" * 40)
    
    player = TestMusicPlayer()
    player.toggle_repeat()  # 開啟重複播放
    
    song = player.next()
    if song:
        print(f"播放：{song['title']}")
    else:
        print("沒有歌曲可播放")
    
    print("\n✅ 測試完成！")

if __name__ == "__main__":
    test_repeat_function() 