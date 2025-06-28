# Discord Bot 伺服器修改總結

## 主要修改內容

### 1. 伺服器連線IP更新
- **原配置**: `http://localhost:5000`
- **新配置**: `http://awa.freeserver.tw:22405`
- **修改檔案**: 
  - `start_server.py`
  - `server.py` 
  - `keep_alive.py`
  - `config.py` (新增)

### 2. 新增配置管理系統
- **新增檔案**: `config.py`
  - 統一管理所有環境變數
  - 自動解析URL中的端口號
  - 提供配置驗證和顯示功能
  - **新增**: Discord Bot TOKEN 支援

### 3. 修正 Discord Bot TOKEN 載入問題
- **問題**: `bot.py` 沒有正確載入 `.env` 檔案和 TOKEN
- **修正**:
  - 加入 `load_dotenv()` 調用
  - 直接從環境變數讀取 TOKEN (`TOKEN` 或 `DISCORD_TOKEN`)
  - 從 `setting.json` 中移除 TOKEN 和 application_id
  - 在 `config.py` 中加入 Discord Bot 配置支援

### 4. 加強Logger功能
- **日誌等級**: 可通過 `LOG_LEVEL` 環境變數設定
- **日誌格式**: 統一的時間戳和模組名稱格式
- **日誌檔案**:
  - `startup.log`: 啟動腳本日誌
  - `server.log`: 伺服器日誌  
  - `keep_alive.log`: 保活腳本日誌
  - `logs/bot.log`: Discord Bot 日誌
  - `logs/error.log`: Discord Bot 錯誤日誌

### 5. 環境變數配置
所有配置都可以通過環境變數自定義：

```bash
# 伺服器配置
SERVER_URL=http://awa.freeserver.tw:22405
LOG_LEVEL=INFO

# 保活配置
PING_INTERVAL=25
HEALTH_CHECK_INTERVAL=60
MAX_RETRIES=5
RETRY_DELAY=10

# Discord Bot 配置
TOKEN=your_discord_bot_token_here
# 或者
DISCORD_TOKEN=your_discord_bot_token_here

# 開發配置
DEBUG=False
```

### 6. 監控端點
伺服器啟動後可訪問：
- `http://awa.freeserver.tw:22405/`: 主頁面 (狀態監控)
- `http://awa.freeserver.tw:22405/health`: 健康檢查
- `http://awa.freeserver.tw:22405/status`: 詳細狀態
- `http://awa.freeserver.tw:22405/ping`: 手動觸發ping

## 使用方法

### 啟動伺服器
```bash
python start_server.py
```

### 啟動 Discord Bot
```bash
python bot.py
```

### 單獨啟動伺服器
```bash
python server.py
```

### 單獨啟動保活腳本
```bash
python keep_alive.py
```

### 查看配置
```bash
python config.py
```

## Discord Bot Token 設定

### 方法一：使用 .env 檔案 (推薦)
```bash
TOKEN=your_discord_bot_token_here
```

### 方法二：使用環境變數
```bash
export TOKEN="your_discord_bot_token_here"
```

## 檔案結構
```
Akane-Ko/
├── start_server.py      # 主啟動腳本 (已更新)
├── server.py           # Flask伺服器 (已更新)
├── keep_alive.py       # 保活腳本 (已更新)
├── bot.py              # Discord Bot (已修正TOKEN載入)
├── config.py           # 配置管理 (新增)
├── CONFIG_README.md    # 配置說明 (已更新)
├── CHANGES_SUMMARY.md  # 修改總結 (已更新)
├── env_example.txt     # .env範例 (新增)
└── 其他檔案...
```

## 注意事項

1. **端口開放**: 確保防火牆開放 `22405` 端口
2. **域名解析**: 確保 `awa.freeserver.tw` 能正確解析到伺服器IP
3. **環境變數**: 可以通過環境變數自定義所有配置
4. **日誌監控**: 所有操作都會記錄到對應的日誌檔案中
5. **健康檢查**: 系統會定期進行健康檢查和外部ping測試
6. **Discord Token**: 確保 Discord Bot Token 已正確設定
7. **權限設定**: 確保 Discord Bot 有必要的權限

## 測試建議

1. 先測試配置檔案是否正常載入
2. 測試 Discord Bot Token 是否能正確獲取
3. 測試伺服器是否能正常啟動
4. 測試保活腳本是否能正常運行
5. 測試網頁端點是否能正常訪問
6. 檢查日誌檔案是否正常生成
7. 測試 Discord Bot 是否能正常連接 