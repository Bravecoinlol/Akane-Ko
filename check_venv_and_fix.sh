#!/bin/bash

# 檢查虛擬環境並修復重複播放功能

echo "🔧 檢查虛擬環境並修復重複播放功能"
echo "===================================="

# 檢查是否在正確目錄
if [ ! -f "bot.py" ]; then
    echo "❌ 錯誤：請在 Bot 目錄中執行此腳本"
    exit 1
fi

# 1. 檢查虛擬環境
echo "🔍 檢查虛擬環境..."
if [ -d "venv" ]; then
    echo "✅ 虛擬環境存在"
    
    # 檢查 Python 版本
    source venv/bin/activate
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "Python 版本: $PYTHON_VERSION"
    
    # 檢查 Discord.py
    if python3 -c "import discord" 2>/dev/null; then
        DISCORD_VERSION=$(python3 -c "import discord; print(discord.__version__)" 2>/dev/null)
        echo "Discord.py 版本: $DISCORD_VERSION"
    else
        echo "❌ Discord.py 未安裝"
        echo "正在安裝 Discord.py..."
        pip install discord.py
    fi
    
    # 檢查其他依賴
    echo "檢查其他依賴..."
    pip list | grep -E "(yt-dlp|PyNaCl|ffmpeg-python)" || {
        echo "安裝缺少的依賴..."
        pip install -r requirements.txt
    }
    
else
    echo "❌ 虛擬環境不存在"
    echo "正在創建虛擬環境..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    echo "✅ 虛擬環境已創建並安裝依賴"
fi

# 2. 修復顏色代碼問題
echo ""
echo "🔧 修復顏色代碼問題..."
if grep -q "discord.Color.light_grey()" cogs/music.py; then
    echo "❌ 發現舊版顏色代碼"
    echo "正在修復..."
    sed -i 's/discord\.Color\.light_grey()/discord.Color.light_gray()/g' cogs/music.py
    echo "✅ 顏色問題已修復"
else
    echo "✅ 顏色代碼正常"
fi

# 3. 檢查重複播放邏輯
echo ""
echo "🔍 檢查重複播放邏輯..."
if grep -q "if self.repeat and self.current:" cogs/music.py; then
    echo "✅ 重複播放邏輯存在"
else
    echo "❌ 重複播放邏輯缺失"
fi

# 4. 測試重複播放邏輯
echo ""
echo "🧪 測試重複播放邏輯..."
python3 test_repeat_logic.py

# 5. 檢查音樂控制按鈕
echo ""
echo "🔍 檢查音樂控制按鈕..."
if grep -q "toggle_repeat" cogs/music.py; then
    echo "✅ 重複播放按鈕存在"
else
    echo "❌ 重複播放按鈕缺失"
fi

# 6. 檢查命令註冊
echo ""
echo "🔍 檢查命令註冊..."
if grep -q "@app_commands.command.*repeat" cogs/music.py; then
    echo "✅ 重複播放命令已註冊"
else
    echo "❌ 重複播放命令未註冊"
fi

# 7. 測試 Discord.py 功能（在虛擬環境中）
echo ""
echo "🧪 測試 Discord.py 功能..."
if [ -d "venv" ]; then
    source venv/bin/activate
    python3 test_repeat_function.py
else
    echo "⚠️ 虛擬環境不存在，跳過 Discord.py 測試"
fi

echo ""
echo "✅ 檢查和修復完成！"
echo ""
echo "📋 修復內容："
echo "• 檢查並創建虛擬環境"
echo "• 安裝 Discord.py 和依賴"
echo "• 修復顏色代碼問題"
echo "• 檢查重複播放邏輯"
echo "• 測試重複播放功能"
echo ""
echo "💡 使用方式："
echo "1. 使用 /repeat 命令切換重複播放"
echo "2. 使用音樂控制按鈕的 🔁 按鈕"
echo "3. 使用 /queue 命令查看重複播放狀態"
echo ""
echo "🔍 測試命令："
echo "python3 test_repeat_logic.py  # 邏輯測試"
echo "source venv/bin/activate && python3 test_repeat_function.py  # 完整測試" 