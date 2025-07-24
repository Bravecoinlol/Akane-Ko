# 虛擬環境使用指南

## 為什麼需要虛擬環境？

Discord.py 和相關依賴需要在虛擬環境中運行，原因如下：

1. **依賴管理** - 避免與系統 Python 套件衝突
2. **版本控制** - 確保使用正確的 Discord.py 版本
3. **隔離環境** - 避免影響其他 Python 專案
4. **部署一致性** - 確保在不同環境中行為一致

## 虛擬環境操作

### 1. 檢查虛擬環境狀態

#### Linux/Orange Pi
```bash
# 檢查虛擬環境是否存在
ls -la venv/

# 檢查 Python 版本
source venv/bin/activate
python3 --version

# 檢查 Discord.py 版本
python3 -c "import discord; print(discord.__version__)"
```

#### Windows
```cmd
# 檢查虛擬環境是否存在
dir venv\Scripts\

# 檢查 Python 版本
call venv\Scripts\activate.bat
python --version

# 檢查 Discord.py 版本
python -c "import discord; print(discord.__version__)"
```

### 2. 創建虛擬環境

#### Linux/Orange Pi
```bash
# 創建虛擬環境
python3 -m venv venv

# 啟動虛擬環境
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

#### Windows
```cmd
# 創建虛擬環境
python -m venv venv

# 啟動虛擬環境
call venv\Scripts\activate.bat

# 安裝依賴
pip install -r requirements.txt
```

### 3. 啟動 Bot（在虛擬環境中）

#### Linux/Orange Pi
```bash
# 方法 1：手動啟動
source venv/bin/activate
python3 bot.py

# 方法 2：使用啟動腳本
./start_bot_simple.sh

# 方法 3：背景運行
./start_bot_background.sh
```

#### Windows
```cmd
# 方法 1：手動啟動
call venv\Scripts\activate.bat
python bot.py

# 方法 2：使用啟動腳本
start_bot_simple.bat
```

### 4. 運行測試（在虛擬環境中）

#### 邏輯測試（不需要虛擬環境）
```bash
# Linux/Orange Pi
python3 test_repeat_logic.py

# Windows
python test_repeat_logic.py
```

#### 完整測試（需要虛擬環境）
```bash
# Linux/Orange Pi
source venv/bin/activate
python3 test_repeat_function.py

# Windows
call venv\Scripts\activate.bat
python test_repeat_function.py
```

## 常見問題

### Q: 如何知道是否在虛擬環境中？
A: 檢查命令提示符，如果看到 `(venv)` 前綴，表示已在虛擬環境中。

### Q: 虛擬環境啟動失敗怎麼辦？
A: 檢查 Python 版本和虛擬環境是否正確創建。

### Q: 依賴安裝失敗怎麼辦？
A: 嘗試更新 pip：`pip install --upgrade pip`

### Q: 如何退出虛擬環境？
A: 使用命令 `deactivate`

### Q: 如何重新創建虛擬環境？
A: 刪除 `venv` 資料夾，然後重新創建。

## 自動化腳本

### 完整檢查和修復腳本

#### Linux/Orange Pi
```bash
chmod +x check_venv_and_fix.sh
./check_venv_and_fix.sh
```

#### Windows
```cmd
check_venv_and_fix.bat
```

這些腳本會：
1. 檢查虛擬環境是否存在
2. 如果不存在，創建虛擬環境
3. 安裝所有必要的依賴
4. 修復重複播放功能
5. 運行測試

### 簡單修復腳本

#### Linux/Orange Pi
```bash
chmod +x fix_repeat_command.sh
./fix_repeat_command.sh
```

#### Windows
```cmd
fix_repeat_command.bat
```

這些腳本只修復重複播放功能，不處理虛擬環境。

## 依賴清單

### 主要依賴
- `discord.py` - Discord Bot 框架
- `yt-dlp` - YouTube 下載器
- `PyNaCl` - 音訊處理
- `ffmpeg-python` - 音訊轉換

### 檢查依賴
```bash
# Linux/Orange Pi
source venv/bin/activate
pip list

# Windows
call venv\Scripts\activate.bat
pip list
```

## 故障排除

### 1. 虛擬環境不存在
```bash
# 創建虛擬環境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Discord.py 未安裝
```bash
# 在虛擬環境中安裝
source venv/bin/activate
pip install discord.py
```

### 3. 依賴版本衝突
```bash
# 清理並重新安裝
source venv/bin/activate
pip uninstall -y -r requirements.txt
pip install -r requirements.txt
```

### 4. 權限問題
```bash
# 修復權限
chmod +x *.sh
chmod +x venv/bin/*
```

## 最佳實踐

1. **總是使用虛擬環境** - 運行任何 Discord.py 相關程式碼
2. **定期更新依賴** - 保持套件版本最新
3. **備份虛擬環境** - 在重要更改前備份
4. **使用啟動腳本** - 避免手動啟動的錯誤
5. **監控日誌** - 檢查 Bot 運行狀態

## 相關檔案

- `check_venv_and_fix.sh` - Linux 完整檢查腳本
- `check_venv_and_fix.bat` - Windows 完整檢查腳本
- `start_bot_simple.sh` - Linux 啟動腳本
- `start_bot_background.sh` - Linux 背景啟動腳本
- `requirements.txt` - 依賴清單
- `venv/` - 虛擬環境資料夾 