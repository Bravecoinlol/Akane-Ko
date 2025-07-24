@echo off
chcp 65001 >nul
echo 🔧 檢查虛擬環境並修復重複播放功能
echo ====================================

REM 檢查是否在正確目錄
if not exist "bot.py" (
    echo ❌ 錯誤：請在 Bot 目錄中執行此腳本
    pause
    exit /b 1
)

REM 1. 檢查虛擬環境
echo 🔍 檢查虛擬環境...
if exist "venv\Scripts\activate.bat" (
    echo ✅ 虛擬環境存在
    
    REM 檢查 Python 版本
    call venv\Scripts\activate.bat
    python --version
    
    REM 檢查 Discord.py
    python -c "import discord; print('Discord.py 版本:', discord.__version__)" 2>nul
    if %errorlevel% neq 0 (
        echo ❌ Discord.py 未安裝
        echo 正在安裝 Discord.py...
        pip install discord.py
    ) else (
        echo ✅ Discord.py 已安裝
    )
    
    REM 檢查其他依賴
    echo 檢查其他依賴...
    pip list | findstr /i "yt-dlp PyNaCl ffmpeg-python" >nul
    if %errorlevel% neq 0 (
        echo 安裝缺少的依賴...
        pip install -r requirements.txt
    )
    
) else (
    echo ❌ 虛擬環境不存在
    echo 正在創建虛擬環境...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    echo ✅ 虛擬環境已創建並安裝依賴
)

REM 2. 修復顏色代碼問題
echo.
echo 🔧 修復顏色代碼問題...
findstr /c:"discord.Color.light_grey()" cogs\music.py >nul
if %errorlevel% equ 0 (
    echo ❌ 發現舊版顏色代碼
    echo 正在修復...
    powershell -Command "(Get-Content cogs\music.py) -replace 'discord\.Color\.light_grey\(\)', 'discord.Color.light_gray()' | Set-Content cogs\music.py"
    echo ✅ 顏色問題已修復
) else (
    echo ✅ 顏色代碼正常
)

REM 3. 檢查重複播放邏輯
echo.
echo 🔍 檢查重複播放邏輯...
findstr /c:"if self.repeat and self.current:" cogs\music.py >nul
if %errorlevel% equ 0 (
    echo ✅ 重複播放邏輯存在
) else (
    echo ❌ 重複播放邏輯缺失
)

REM 4. 測試重複播放邏輯
echo.
echo 🧪 測試重複播放邏輯...
if exist "test_repeat_logic.py" (
    python test_repeat_logic.py
) else (
    echo ⚠️ 測試檔案不存在
)

REM 5. 檢查音樂控制按鈕
echo.
echo 🔍 檢查音樂控制按鈕...
findstr /c:"toggle_repeat" cogs\music.py >nul
if %errorlevel% equ 0 (
    echo ✅ 重複播放按鈕存在
) else (
    echo ❌ 重複播放按鈕缺失
)

REM 6. 檢查命令註冊
echo.
echo 🔍 檢查命令註冊...
findstr /c:"@app_commands.command.*repeat" cogs\music.py >nul
if %errorlevel% equ 0 (
    echo ✅ 重複播放命令已註冊
) else (
    echo ❌ 重複播放命令未註冊
)

REM 7. 測試 Discord.py 功能（在虛擬環境中）
echo.
echo 🧪 測試 Discord.py 功能...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    if exist "test_repeat_function.py" (
        python test_repeat_function.py
    ) else (
        echo ⚠️ Discord.py 測試檔案不存在
    )
) else (
    echo ⚠️ 虛擬環境不存在，跳過 Discord.py 測試
)

echo.
echo ✅ 檢查和修復完成！
echo.
echo 📋 修復內容：
echo • 檢查並創建虛擬環境
echo • 安裝 Discord.py 和依賴
echo • 修復顏色代碼問題
echo • 檢查重複播放邏輯
echo • 測試重複播放功能
echo.
echo 💡 使用方式：
echo 1. 使用 /repeat 命令切換重複播放
echo 2. 使用音樂控制按鈕的 🔁 按鈕
echo 3. 使用 /queue 命令查看重複播放狀態
echo.
echo 🔍 測試命令：
echo python test_repeat_logic.py  # 邏輯測試
echo call venv\Scripts\activate.bat ^&^& python test_repeat_function.py  # 完整測試
echo.
pause 