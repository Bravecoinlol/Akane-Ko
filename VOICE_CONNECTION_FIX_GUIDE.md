# 語音連接修復指南

## 問題描述

你的 Discord Bot 遇到錯誤代碼 4006 "Unknown session" 的語音連接問題。這個錯誤通常表示：

- 語音會話已過期或無效
- 網路連接不穩定
- Discord 語音服務問題
- 重連機制過於頻繁

## 錯誤代碼 4006 的常見原因

### 1. 網路連接問題
- Orange Pi 的網路連接不穩定
- WiFi 信號弱或干擾
- 網路延遲過高
- 防火牆阻擋語音連接

### 2. Discord 服務問題
- Discord 語音服務暫時不可用
- 語音伺服器負載過高
- 地區性服務中斷

### 3. Bot 配置問題
- 重連次數過多
- 連接超時設定過短
- FFmpeg 配置不當

## 解決方案

### 方案一：使用修復腳本（推薦）

```bash
# 1. 執行語音連接修復腳本
chmod +x fix_voice_connection.sh
./fix_voice_connection.sh

# 2. 執行優化腳本
python3 optimize_voice_connection.py

# 3. 重新啟動 Bot
./start_bot_simple.sh
```

### 方案二：手動修復

#### 1. 檢查網路連接
```bash
# 測試基本網路連接
ping -c 4 8.8.8.8

# 測試 Discord API 連接
curl -I https://discord.com/api/v10/gateway

# 測試語音服務連接
curl -I https://voice.discord.com
```

#### 2. 優化 FFmpeg 配置
創建 `ffmpeg_config.json`：
```json
{
  "ffmpeg_path": "ffmpeg",
  "ffmpeg_options": {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 15 -reconnect_at_eof 1 -reconnect_on_network_error 1 -reconnect_on_http_error 1",
    "options": "-vn -b:a 96k -bufsize 2048k -maxrate 128k -ar 48000 -ac 2 -af volume=0.5"
  }
}
```

#### 3. 優化音樂配置
創建 `music_config.json`：
```json
{
  "default_volume": 0.5,
  "max_queue_size": 25,
  "auto_disconnect_delay": 900,
  "max_song_duration": 480,
  "enable_cache": true,
  "cache_size": 30,
  "reconnect_attempts": 1,
  "reconnect_delay": 20,
  "voice_timeout": 45,
  "enable_voice_reconnect": true,
  "max_voice_retries": 1,
  "voice_retry_delay": 30
}
```

#### 4. 修改音樂 Cog
在 `cogs/music.py` 中修改以下設定：
```python
# 減少重連次數
self.max_reconnect_attempts = 1
self.reconnect_delay = 20

# 增加連接超時
timeout=45.0
```

### 方案三：網路優化

#### 1. 使用有線網路
如果可能，將 Orange Pi 連接到有線網路而非 WiFi。

#### 2. 檢查網路設定
```bash
# 檢查網路介面
ip addr show

# 檢查路由
ip route show

# 檢查 DNS
cat /etc/resolv.conf
```

#### 3. 優化網路設定
```bash
# 增加網路緩衝區
echo 'net.core.rmem_max = 16777216' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max = 16777216' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

## 監控和診斷

### 1. 使用監控腳本
```bash
# 監控語音連接狀態
./monitor_voice_connection.sh

# 網路診斷
./network_diagnosis.sh

# 語音連接修復
python3 voice_connection_fix.py
```

### 2. 查看日誌
```bash
# 實時查看語音相關日誌
tail -f bot.log | grep -E "(voice|4006|ConnectionClosed)"

# 查看最近的錯誤
grep -E "(4006|ConnectionClosed)" bot.log | tail -20
```

### 3. 檢查系統資源
```bash
# 檢查 CPU 和記憶體使用
top

# 檢查網路使用
iftop

# 檢查磁碟使用
df -h
```

## 預防措施

### 1. 定期維護
- 每週重啟 Bot
- 清理舊的日誌檔案
- 更新系統和依賴

### 2. 監控設定
- 設定自動重啟機制
- 監控網路連接狀態
- 記錄語音連接錯誤

### 3. 備用方案
- 準備多個網路連接
- 設定自動故障轉移
- 保持備用 Bot 實例

## 常見問題

### Q: 修復後仍然出現 4006 錯誤？
A: 檢查網路連接穩定性，考慮使用有線網路。

### Q: 如何減少重連頻率？
A: 修改 `reconnect_attempts` 為 1，增加 `reconnect_delay` 為 20 秒。

### Q: 語音連接不穩定怎麼辦？
A: 使用 `voice_monitor.py` 監控連接狀態，設定自動重啟。

### Q: 如何檢查 Discord 服務狀態？
A: 訪問 https://status.discord.com 查看服務狀態。

## 聯絡支援

如果問題持續存在：

1. 檢查 Discord 官方狀態頁面
2. 確認網路連接穩定性
3. 查看 Bot 日誌中的詳細錯誤信息
4. 考慮升級網路設備或使用有線連接

## 相關檔案

- `fix_voice_connection.sh` - 語音連接修復腳本
- `optimize_voice_connection.py` - 語音連接優化工具
- `voice_monitor.py` - 語音連接監控工具
- `network_diagnosis.sh` - 網路診斷工具
- `monitor_voice_connection.sh` - 語音連接狀態監控

## 更新日誌

- 2025-07-10: 創建初始版本
- 2025-07-10: 添加網路優化建議
- 2025-07-10: 添加監控工具說明 