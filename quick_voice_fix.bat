@echo off
chcp 65001 >nul
echo 🚀 快速語音連接修復
echo ====================

REM 檢查是否在正確目錄
if not exist "bot.py" (
    echo ❌ 錯誤：請在 Bot 目錄中執行此腳本
    pause
    exit /b 1
)

REM 1. 停止 Bot
echo 🛑 停止 Bot...
taskkill /f /im python.exe 2>nul
taskkill /f /im python3.exe 2>nul
timeout /t 3 /nobreak >nul
echo ✅ Bot 已停止

REM 2. 創建優化的 FFmpeg 配置
echo.
echo ⚙️ 創建優化的 FFmpeg 配置...
(
echo {
echo   "ffmpeg_path": "ffmpeg",
echo   "ffmpeg_options": {
echo     "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 15 -reconnect_at_eof 1 -reconnect_on_network_error 1 -reconnect_on_http_error 1",
echo     "options": "-vn -b:a 96k -bufsize 2048k -maxrate 128k -ar 48000 -ac 2 -af volume=0.5"
echo   }
echo }
) > ffmpeg_config.json
echo ✅ FFmpeg 配置已創建

REM 3. 創建優化的音樂配置
echo.
echo 🎼 創建優化的音樂配置...
(
echo {
echo   "default_volume": 0.5,
echo   "max_queue_size": 25,
echo   "auto_disconnect_delay": 900,
echo   "max_song_duration": 480,
echo   "enable_cache": true,
echo   "cache_size": 30,
echo   "reconnect_attempts": 1,
echo   "reconnect_delay": 20,
echo   "voice_timeout": 45,
echo   "enable_voice_reconnect": true,
echo   "max_voice_retries": 1,
echo   "voice_retry_delay": 30
echo }
) > music_config.json
echo ✅ 音樂配置已創建

REM 4. 檢查並安裝依賴
echo.
echo 📦 檢查依賴...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    python -m pip install -r requirements.txt --quiet
    echo ✅ 依賴檢查完成
) else (
    echo ⚠️ 虛擬環境不存在，請先創建
)

REM 5. 清理舊的日誌
echo.
echo 🧹 清理舊的日誌...
if exist "bot.log" (
    ren bot.log bot.log.old.%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
    echo ✅ 舊日誌已備份
)

REM 6. 檢查網路連接
echo.
echo 🌐 檢查網路連接...
ping -n 3 8.8.8.8 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 網路連接正常
) else (
    echo ❌ 網路連接異常
    echo 請檢查網路設定
)

REM 7. 重新啟動 Bot
echo.
echo 🚀 重新啟動 Bot...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    start /b python bot.py > bot.log 2>&1
    echo ✅ Bot 已重新啟動
    echo 📋 查看日誌: type bot.log
) else (
    echo ❌ 虛擬環境不存在，無法啟動 Bot
    echo 請先創建虛擬環境: python -m venv venv
)

echo.
echo ✅ 快速修復完成！
echo.
echo 📋 修復內容:
echo • 減少重連次數 (3 → 1)
echo • 增加重連延遲 (5秒 → 20秒)
echo • 增加連接超時 (20秒 → 45秒)
echo • 優化 FFmpeg 配置
echo • 優化音樂配置
echo.
echo 💡 建議:
echo 1. 監控 Bot 運行狀態
echo 2. 如果問題持續，檢查網路連接
echo 3. 考慮使用有線網路
echo.
echo 🔍 監控命令:
echo findstr /i "voice 4006 ConnectionClosed" bot.log
echo.
pause 