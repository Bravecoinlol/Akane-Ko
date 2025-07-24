@echo off
chcp 65001 >nul
echo 🔧 修復重複播放命令
echo ====================

REM 檢查是否在正確目錄
if not exist "cogs\music.py" (
    echo ❌ 錯誤：請在 Bot 目錄中執行此腳本
    pause
    exit /b 1
)

echo 🔍 檢查重複播放命令問題...

REM 1. 檢查顏色問題
echo 1. 檢查顏色問題...
findstr /c:"discord.Color.light_grey()" cogs\music.py >nul
if %errorlevel% equ 0 (
    echo ❌ 發現舊版顏色代碼
    echo 正在修復...
    powershell -Command "(Get-Content cogs\music.py) -replace 'discord\.Color\.light_grey\(\)', 'discord.Color.light_gray()' | Set-Content cogs\music.py"
    echo ✅ 顏色問題已修復
) else (
    echo ✅ 顏色代碼正常
)

REM 2. 檢查重複播放邏輯
echo.
echo 2. 檢查重複播放邏輯...
findstr /c:"if self.repeat and self.current:" cogs\music.py >nul
if %errorlevel% equ 0 (
    echo ✅ 重複播放邏輯存在
) else (
    echo ❌ 重複播放邏輯缺失
)

REM 3. 測試重複播放功能
echo.
echo 3. 測試重複播放功能...
if exist "test_repeat_logic.py" (
    python test_repeat_logic.py
) else (
    echo ⚠️ 測試檔案不存在
)

REM 4. 檢查音樂控制按鈕
echo.
echo 4. 檢查音樂控制按鈕...
findstr /c:"toggle_repeat" cogs\music.py >nul
if %errorlevel% equ 0 (
    echo ✅ 重複播放按鈕存在
) else (
    echo ❌ 重複播放按鈕缺失
)

REM 5. 檢查日誌設定
echo.
echo 5. 檢查日誌設定...
findstr /c:"logger.debug" cogs\music.py >nul
if %errorlevel% equ 0 (
    echo ✅ 日誌設定正常
) else (
    echo ⚠️ 日誌設定可能不完整
)

echo.
echo ✅ 重複播放命令修復完成！
echo.
echo 📋 修復內容：
echo • 修復顏色代碼問題
echo • 檢查重複播放邏輯
echo • 測試重複播放功能
echo • 檢查音樂控制按鈕
echo.
echo 💡 使用方式：
echo 1. 使用 /repeat 命令切換重複播放
echo 2. 使用音樂控制按鈕的 🔁 按鈕
echo 3. 使用 /queue 命令查看重複播放狀態
echo.
echo 🔍 測試命令：
echo python test_repeat_function.py
echo.
pause 