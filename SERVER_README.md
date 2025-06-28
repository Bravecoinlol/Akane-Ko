# Discord Bot 伺服器保活系統

這個系統專門設計來防止 Discord Bot 在雲端服務上進入休眠狀態，確保機器人能夠持續運行。

## 🚀 快速開始

### 方法一：使用啟動腳本（推薦）
```bash
python start_server.py
```

### 方法二：分別啟動
```bash
# 終端機 1：啟動伺服器
python server.py

# 終端機 2：啟動保活腳本
python keep_alive.py
```

## 📋 功能特色

### 🔄 自動保活機制
- **每 30 秒**自動 ping 外部服務
- **每 60 秒**執行健康檢查
- **多個備用 URL**確保連線穩定
- **自動重試機制**處理網路問題

### 📊 監控功能
- 即時狀態顯示
- 詳細統計資訊
- 自動日誌記錄
- 健康檢查端點

### 🌐 Web 介面
- 美觀的狀態頁面
- 自動刷新（每30秒）
- 響應式設計
- JSON API 端點

## 🔧 配置選項

### 環境變數
```bash
# 伺服器配置
PORT=5000                    # 伺服器端口
DEBUG=False                  # 除錯模式

# 保活配置
SERVER_URL=http://localhost:5000  # 伺服器 URL
PING_INTERVAL=25             # Ping 間隔（秒）
HEALTH_CHECK_INTERVAL=60     # 健康檢查間隔（秒）
MAX_RETRIES=5               # 最大重試次數
RETRY_DELAY=10              # 重試延遲（秒）
```

### 自定義配置
編輯 `server.py` 中的 `CONFIG` 字典：
```python
CONFIG = {
    'ping_interval': 30,        # 調整 ping 頻率
    'health_check_interval': 60, # 調整健康檢查頻率
    'ping_urls': [              # 自定義 ping URL
        'https://httpbin.org/get',
        'https://api.github.com',
        # 添加更多 URL...
    ]
}
```

## 📡 API 端點

### 主要端點
- `GET /` - 狀態頁面（HTML）
- `GET /health` - 健康檢查（JSON）
- `GET /ping` - 手動觸發 ping（JSON）
- `GET /status` - 詳細狀態（JSON）

### 範例回應
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "uptime": 3600,
  "ping_count": 120,
  "health_checks": 60,
  "last_ping": "2024-01-01T12:00:00"
}
```

## 📊 監控和日誌

### 日誌檔案
- `server.log` - 伺服器日誌
- `keep_alive.log` - 保活腳本日誌

### 日誌級別
- `INFO` - 一般資訊
- `WARNING` - 警告訊息
- `ERROR` - 錯誤訊息

### 監控建議
1. 定期檢查日誌檔案
2. 監控 `/health` 端點
3. 設定外部監控服務（如 UptimeRobot）

## 🔍 故障排除

### 常見問題

**Q: 伺服器無法啟動**
```bash
# 檢查端口是否被佔用
netstat -tulpn | grep :5000

# 檢查依賴是否安裝
pip install -r requirements.txt
```

**Q: Ping 失敗**
```bash
# 檢查網路連線
curl https://httpbin.org/get

# 檢查防火牆設定
# 確保允許對外連線
```

**Q: 日誌檔案過大**
```bash
# 定期清理日誌
find . -name "*.log" -size +10M -delete
```

### 效能優化

**減少資源使用**
```python
# 在 server.py 中調整
CONFIG['ping_interval'] = 60  # 增加間隔
CONFIG['health_check_interval'] = 120  # 減少健康檢查頻率
```

**增加穩定性**
```python
# 添加更多備用 URL
CONFIG['ping_urls'].extend([
    'https://api.ipify.org',
    'https://httpbin.org/status/200'
])
```

## 🚀 部署建議

### 雲端服務配置

**Heroku**
```bash
# Procfile
web: python server.py
worker: python keep_alive.py
```

**Railway**
```bash
# 設定環境變數
PORT=5000
SERVER_URL=https://your-app.railway.app
```

**Vercel**
```bash
# vercel.json
{
  "functions": {
    "server.py": {
      "maxDuration": 30
    }
  }
}
```

### 系統服務（Linux）
```bash
# 創建 systemd 服務
sudo nano /etc/systemd/system/discord-bot.service

[Unit]
Description=Discord Bot Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/bot
ExecStart=/usr/bin/python3 start_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# 啟用服務
sudo systemctl enable discord-bot
sudo systemctl start discord-bot
```

## 📈 效能指標

### 預期表現
- **99.9% 可用性** - 透過多重保活機制
- **< 1 秒響應時間** - 本地伺服器
- **< 5 秒恢復時間** - 自動重試機制

### 資源使用
- **CPU**: < 5% (空閒時)
- **記憶體**: < 50MB
- **網路**: < 1KB/分鐘 (ping 流量)

## 🔐 安全注意事項

1. **不要暴露敏感資訊**在狀態頁面
2. **使用 HTTPS**在生產環境
3. **限制 API 存取**如果需要
4. **定期更新依賴**套件

## 📞 支援

如果遇到問題：
1. 檢查日誌檔案
2. 確認網路連線
3. 驗證配置設定
4. 重新啟動服務

---

**版本**: 1.0.0  
**最後更新**: 2024-01-01  
**維護者**: Discord Bot Team 