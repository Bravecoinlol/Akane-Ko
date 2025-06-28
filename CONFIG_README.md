# Discord Bot 伺服器配置說明

## 環境變數配置

您可以通過設定環境變數來自定義伺服器行為：

### 伺服器配置
- `SERVER_URL`: 伺服器URL (預設: `http://awa.freeserver.tw:22405`)
- `PORT`: 監聽端口 (會自動從SERVER_URL解析，預設: `22405`)

### 日誌配置
- `LOG_LEVEL`: 日誌等級 (預設: `INFO`)
  - 可選值: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

### 保活配置
- `PING_INTERVAL`: Ping間隔秒數 (預設: `25`)
- `HEALTH_CHECK_INTERVAL`: 健康檢查間隔秒數 (預設: `60`)
- `MAX_RETRIES`: 最大重試次數 (預設: `5`)
- `RETRY_DELAY`: 重試延遲秒數 (預設: `10`)

### Discord Bot 配置
- `TOKEN`: Discord Bot Token (優先從 setting.json 獲取)
- `DISCORD_TOKEN`: Discord Bot Token (備用環境變數)

### 開發配置
- `DEBUG`: 除錯模式 (預設: `False`)
  - 可選值: `True`, `False`

## Discord Bot Token 設定

### 方法一：使用 .env 檔案 (推薦)
創建 `.env` 檔案並設定：
```bash
TOKEN=your_discord_bot_token_here
# 或者
DISCORD_TOKEN=your_discord_bot_token_here
```

### 方法二：使用環境變數
```bash
export TOKEN="your_discord_bot_token_here"
# 或者
export DISCORD_TOKEN="your_discord_bot_token_here"
```

## 使用範例

### Windows PowerShell
```powershell
$env:SERVER_URL="http://awa.freeserver.tw:22405"
$env:LOG_LEVEL="INFO"
$env:PING_INTERVAL="25"
python start_server.py
```

### Linux/macOS
```bash
export SERVER_URL="http://awa.freeserver.tw:22405"
export LOG_LEVEL="INFO"
export PING_INTERVAL="25"
python start_server.py
```

### 一次性設定
```bash
SERVER_URL="http://awa.freeserver.tw:22405" LOG_LEVEL="INFO" python start_server.py
```

## 日誌檔案

系統會自動生成以下日誌檔案：
- `startup.log`: 啟動腳本日誌
- `server.log`: 伺服器日誌
- `keep_alive.log`: 保活腳本日誌
- `logs/bot.log`: Discord Bot 日誌
- `logs/error.log`: Discord Bot 錯誤日誌

## 監控端點

啟動後可以訪問：
- `http://awa.freeserver.tw:22405/`: 主頁面 (狀態監控)
- `http://awa.freeserver.tw:22405/health`: 健康檢查
- `http://awa.freeserver.tw:22405/status`: 詳細狀態
- `http://awa.freeserver.tw:22405/ping`: 手動觸發ping

## 啟動方式

### 啟動伺服器 (不含 Discord Bot)
```bash
python start_server.py
```

### 啟動 Discord Bot
```bash
python bot.py
```

### 啟動 Discord Bot (使用 start_bot.py)
```bash
python start_bot.py
```

## 注意事項

1. **端口開放**: 確保防火牆開放 `22405` 端口
2. **域名解析**: 確保 `awa.freeserver.tw` 能正確解析到伺服器IP
3. **環境變數**: 可以通過環境變數自定義所有配置
4. **日誌監控**: 所有操作都會記錄到對應的日誌檔案中
5. **健康檢查**: 系統會定期進行健康檢查和外部ping測試
6. **Discord Token**: 確保 Discord Bot Token 已正確設定
7. **權限設定**: 確保 Discord Bot 有必要的權限 