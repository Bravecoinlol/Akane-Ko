# Discord Bot 重啟指南

## 🔧 問題解決

### asyncio 錯誤修復

你遇到的錯誤是：
```
RuntimeError: no running event loop
RuntimeWarning: coroutine 'Music.after_playing' was never awaited
```

這個問題已經在 `cogs/music.py` 中修復了。修復內容：
- 將 `asyncio.create_task()` 改為使用 `asyncio.run_coroutine_threadsafe()`
- 添加了更好的錯誤處理機制

### Python 環境問題

如果遇到 `nohup: 無法執行指令 'python': 沒有此一檔案或目錄` 錯誤：
- Orange Pi 通常使用 `python3` 而不是 `python`
- 所有腳本已經更新為自動檢測 Python 命令

### 虛擬環境問題

如果遇到 `ModuleNotFoundError: No module named 'discord'` 錯誤：
- 這是因為虛擬環境沒有正確激活
- 使用新的啟動腳本可以解決這個問題

## 🚀 重啟方法

### 方法 0: 環境測試（推薦先執行）

```bash
# 1. 給腳本執行權限
chmod +x test_python_env.sh

# 2. 測試 Python 環境
./test_python_env.sh
```

這個腳本會檢查：
- Python 版本和可用性
- pip 版本
- 虛擬環境狀態
- Discord.py 安裝狀態
- 必要文件存在性
- bot.py 語法正確性

### 方法 1: 使用新的啟動腳本（推薦）

```bash
# 1. 給腳本執行權限
chmod +x start_bot_background.sh

# 2. 後台啟動 bot
./start_bot_background.sh
```

這個腳本會：
- 自動檢查虛擬環境
- 自動安裝缺失的依賴
- 在後台啟動 bot
- 提供進程 ID 和日誌信息

### 方法 2: 使用修復腳本

```bash
# 1. 給腳本執行權限
chmod +x fix_asyncio_issue.sh

# 2. 運行修復腳本
./fix_asyncio_issue.sh
```

這個腳本會：
- 自動檢測 Python 命令（python3 或 python）
- 檢查虛擬環境中的 Discord.py
- 自動安裝缺失的依賴
- 停止現有的 bot 進程
- 備份舊日誌
- 啟動修復後的 bot
- 檢查啟動狀態

### 方法 3: 使用狀態檢查腳本

```bash
# 1. 給腳本執行權限
chmod +x check_and_restart_bot.sh

# 2. 運行腳本
./check_and_restart_bot.sh
```

這個腳本提供互動式選項：
- 檢查 bot 狀態
- 重啟 bot
- 強制重啟（清除日誌）
- 查看日誌

### 方法 4: 手動啟動（調試用）

```bash
# 1. 激活虛擬環境
source venv/bin/activate

# 2. 檢查 Discord.py
python -c "import discord; print('Discord.py 可用')"

# 3. 啟動 bot
python bot.py
```

### 方法 5: 手動重啟

```bash
# 1. 檢查 Python 命令
which python3 || which python

# 2. 停止 bot
pkill -f "python.*bot.py"

# 3. 等待進程停止
sleep 5

# 4. 檢查是否還有進程
pgrep -f "python.*bot.py"

# 5. 如果有，強制終止
pkill -9 -f "python.*bot.py"

# 6. 啟動 bot（使用虛擬環境）
cd /mnt/usb/Akane-Ko/Bot
source venv/bin/activate
nohup python bot.py > bot.log 2>&1 &
```

### 方法 6: 使用 systemd 服務（如果已設置）

```bash
# 重啟服務
sudo systemctl restart discord-bot

# 檢查狀態
sudo systemctl status discord-bot

# 查看日誌
sudo journalctl -u discord-bot -f
```

## 📋 檢查命令

### 檢查進程狀態
```bash
# 查看 bot 進程
ps aux | grep "python.*bot.py" | grep -v grep

# 檢查進程 ID
pgrep -f "python.*bot.py"
```

### 查看日誌
```bash
# 查看最新日誌
tail -f bot.log

# 查看最近的錯誤
tail -50 bot.log | grep -i error

# 查看最近的警告
tail -50 bot.log | grep -i warning
```

### 檢查系統資源
```bash
# 查看 CPU 和記憶體使用
top -p $(pgrep -f "python.*bot.py")

# 查看磁碟使用
df -h

# 查看網路連接
netstat -tlnp | grep python
```

## 🔍 故障排除

### 常見問題

1. **Python 命令不存在**
   ```bash
   # 安裝 Python3
   sudo apt update
   sudo apt install python3 python3-pip
   
   # 檢查安裝
   python3 --version
   ```

2. **Discord.py 模組找不到**
   ```bash
   # 檢查虛擬環境
   source venv/bin/activate
   python -c "import discord"
   
   # 如果不存在，重新安裝
   pip install -r requirements.txt
   ```

3. **Bot 無法啟動**
   ```bash
   # 檢查 Python 環境
   ./test_python_env.sh
   
   # 檢查配置文件
   ls -la .env
   cat .env | grep -v "TOKEN"
   ```

4. **音樂播放問題**
   ```bash
   # 檢查 FFmpeg
   ffmpeg -version
   
   # 檢查音頻文件
   ls -la *.mp3 *.wav 2>/dev/null || echo "沒有音頻文件"
   ```

5. **網路連接問題**
   ```bash
   # 測試網路連接
   ping -c 3 discord.com
   
   # 檢查防火牆
   sudo ufw status
   ```

### 日誌分析

常見錯誤和解決方法：

1. **Token 錯誤**
   ```
   discord.errors.LoginFailure: Improper token has been passed.
   ```
   解決：檢查 `.env` 文件中的 TOKEN 是否正確

2. **權限錯誤**
   ```
   discord.errors.Forbidden: 403 Forbidden
   ```
   解決：檢查 bot 權限設定

3. **網路錯誤**
   ```
   discord.errors.ConnectionClosed
   ```
   解決：檢查網路連接，等待重連

4. **asyncio 錯誤**
   ```
   RuntimeError: no running event loop
   ```
   解決：使用修復腳本重啟

5. **Python 命令錯誤**
   ```
   nohup: 無法執行指令 'python': 沒有此一檔案或目錄
   ```
   解決：使用 `./test_python_env.sh` 檢查環境

6. **模組找不到錯誤**
   ```
   ModuleNotFoundError: No module named 'discord'
   ```
   解決：使用 `./start_bot_background.sh` 啟動

## 📞 緊急聯繫

如果以上方法都無法解決問題：

1. **備份重要文件**
   ```bash
   cp -r . backup_$(date +%Y%m%d_%H%M%S)
   ```

2. **查看完整日誌**
   ```bash
   cat bot.log | tail -100
   ```

3. **檢查系統狀態**
   ```bash
   free -h
   df -h
   top
   ```

4. **重新安裝 Python 環境**
   ```bash
   # 刪除虛擬環境
   rm -rf venv
   
   # 重新創建
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## 🛠️ 維護建議

### 定期維護
- 每週檢查日誌文件大小
- 每月清理舊日誌
- 定期更新依賴套件

### 監控腳本
```bash
#!/bin/bash
# 簡單的監控腳本
if ! pgrep -f "python.*bot.py" > /dev/null; then
    echo "$(date): Bot 已停止，正在重啟..."
    ./start_bot_background.sh
fi
```

### 自動重啟（cron）
```bash
# 編輯 crontab
crontab -e

# 添加每小時檢查一次
0 * * * * /path/to/your/bot/check_and_restart_bot.sh
```

---

**注意**: 重啟前請確保沒有重要的音樂播放或遊戲進行中，以免影響用戶體驗。 