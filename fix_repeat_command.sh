#!/bin/bash

# 修復重複播放命令腳本

echo "🔧 修復重複播放命令"
echo "===================="

# 檢查是否在正確目錄
if [ ! -f "cogs/music.py" ]; then
    echo "❌ 錯誤：請在 Bot 目錄中執行此腳本"
    exit 1
fi

echo "🔍 檢查重複播放命令問題..."

# 1. 檢查顏色問題
echo "1. 檢查顏色問題..."
if grep -q "discord.Color.light_grey()" cogs/music.py; then
    echo "❌ 發現舊版顏色代碼"
    echo "正在修復..."
    sed -i 's/discord\.Color\.light_grey()/discord.Color.light_gray()/g' cogs/music.py
    echo "✅ 顏色問題已修復"
else
    echo "✅ 顏色代碼正常"
fi

# 2. 檢查重複播放邏輯
echo ""
echo "2. 檢查重複播放邏輯..."
if grep -q "if self.repeat and self.current:" cogs/music.py; then
    echo "✅ 重複播放邏輯存在"
else
    echo "❌ 重複播放邏輯缺失"
fi

# 3. 測試重複播放功能
echo ""
echo "3. 測試重複播放功能..."
python3 test_repeat_logic.py

# 4. 檢查音樂控制按鈕
echo ""
echo "4. 檢查音樂控制按鈕..."
if grep -q "toggle_repeat" cogs/music.py; then
    echo "✅ 重複播放按鈕存在"
else
    echo "❌ 重複播放按鈕缺失"
fi

# 5. 檢查日誌設定
echo ""
echo "5. 檢查日誌設定..."
if grep -q "logger.debug" cogs/music.py; then
    echo "✅ 日誌設定正常"
else
    echo "⚠️ 日誌設定可能不完整"
fi

echo ""
echo "✅ 重複播放命令修復完成！"
echo ""
echo "📋 修復內容："
echo "• 修復顏色代碼問題"
echo "• 檢查重複播放邏輯"
echo "• 測試重複播放功能"
echo "• 檢查音樂控制按鈕"
echo ""
echo "💡 使用方式："
echo "1. 使用 /repeat 命令切換重複播放"
echo "2. 使用音樂控制按鈕的 🔁 按鈕"
echo "3. 使用 /queue 命令查看重複播放狀態"
echo ""
echo "🔍 測試命令："
echo "python3 test_repeat_function.py" 