# Discord Bot 系統總結

## 系統概述

這是一個完整的 Discord Bot 系統，包含機器人本體和網頁管理儀表板。系統提供了豐富的功能，包括音樂播放、遊戲、歡迎卡片、自動角色分配等，並通過網頁儀表板提供系統監控和管理功能。

## 主要組件

### 1. Discord Bot 核心 (`bot.py`)
- 機器人主程序
- 支援多個功能模組 (Cogs)
- 自動重連和錯誤處理

### 2. 功能模組 (Cogs)

#### 音樂模組 (`cogs/music.py`)
- 音樂播放功能
- 支援多種音頻格式
- 播放列表管理
- 音量控制
- 自動播放功能

#### 成員管理模組 (`cogs/member.py`)
- 歡迎卡片生成
- 自動角色分配
- 成員加入/離開通知
- 支援網頁儀表板配置

#### 遊戲模組 (`cogs/minigames.py`, `cogs/advanced_games.py`)
- 猜數字遊戲
- 石頭剪刀布
- 其他互動遊戲

#### 工具模組 (`cogs/utility_tools.py`, `cogs/image_tools.py`)
- 實用工具命令
- 圖片處理功能
- 系統信息查詢

#### 分析模組 (`cogs/analytics.py`)
- 使用統計
- 數據分析
- 報告生成

### 3. 網頁儀表板 (`web_dashboard.py`)

#### 功能特色
- **系統監控**: 即時 CPU、記憶體、磁碟使用率
- **日誌查看**: 即時查看機器人日誌
- **歡迎卡片配置**: 視覺化配置歡迎卡片
- **機器人控制**: 啟動/停止/重啟機器人

#### 技術架構
- **後端**: Flask + Python
- **前端**: HTML5 + Bootstrap + JavaScript
- **API**: RESTful API 設計
- **實時更新**: AJAX 輪詢

## 文件結構

```
Bot/
├── bot.py                      # 機器人主程序
├── config.py                   # 配置文件
├── requirements.txt            # Python 依賴
├── web_dashboard.py           # 網頁儀表板
├── web_requirements.txt       # 網頁依賴
├── start_web_dashboard.py     # 啟動腳本
├── install_web_dashboard.sh   # 安裝腳本
├── WEB_DASHBOARD_README.md    # 儀表板說明
├── SYSTEM_SUMMARY.md          # 系統總結
├── cogs/                      # 功能模組
│   ├── music.py              # 音樂功能
│   ├── member.py             # 成員管理
│   ├── minigames.py          # 小遊戲
│   ├── advanced_games.py     # 進階遊戲
│   ├── utility_tools.py      # 工具功能
│   ├── image_tools.py        # 圖片工具
│   ├── analytics.py          # 分析功能
│   └── ...                   # 其他模組
├── templates/                 # 網頁模板
│   └── dashboard.html        # 儀表板頁面
├── logs/                     # 日誌目錄
├── venv/                     # Python 虛擬環境
└── 配置文件
    ├── welcome_card_config.json  # 歡迎卡片配置
    ├── setting.json             # 基本設定
    ├── autorole_settings.json   # 自動角色設定
    ├── ffmpeg_config.json       # FFmpeg 配置
    └── music_config.json        # 音樂配置
```

## 主要功能

### Discord Bot 功能

1. **音樂播放**
   - 支援 YouTube、Spotify 等平台
   - 播放列表管理
   - 音量控制
   - 自動播放

2. **歡迎系統**
   - 自定義歡迎卡片
   - 自動角色分配
   - 可視化配置

3. **遊戲系統**
   - 多種互動遊戲
   - 積分系統
   - 排行榜

4. **管理工具**
   - 頻道管理
   - 角色管理
   - 系統監控

### 網頁儀表板功能

1. **系統監控**
   - 即時系統資源使用率
   - 網路流量監控
   - 自動更新

2. **日誌管理**
   - 即時日誌查看
   - 日誌搜索和過濾
   - 自動滾動

3. **配置管理**
   - 歡迎卡片視覺化配置
   - 即時預覽
   - 配置備份和還原

4. **機器人控制**
   - 一鍵啟動/停止/重啟
   - 狀態監控
   - 遠程管理

## 技術特點

### 1. 模組化設計
- 使用 Discord.py Cogs 架構
- 功能模組獨立開發
- 易於維護和擴展

### 2. 配置管理
- JSON 配置文件
- 網頁可視化配置
- 配置備份和還原

### 3. 錯誤處理
- 完善的異常處理
- 自動重連機制
- 詳細的日誌記錄

### 4. 安全性
- 權限檢查
- 輸入驗證
- 安全的 API 設計

## 部署說明

### 本地開發
```bash
# 安裝依賴
pip install -r requirements.txt
pip install -r web_requirements.txt

# 啟動機器人
python bot.py

# 啟動網頁儀表板
python web_dashboard.py
```

### Orange Pi 部署
```bash
# 運行安裝腳本
chmod +x install_web_dashboard.sh
./install_web_dashboard.sh

# 啟動服務
sudo systemctl start discord-bot-dashboard
```

## API 文檔

### 系統信息 API
- `GET /api/system_info` - 獲取系統狀態

### 日誌 API
- `GET /api/logs?lines=50` - 獲取日誌

### 歡迎卡片配置 API
- `GET /api/welcome_card_config` - 獲取配置
- `POST /api/welcome_card_config` - 保存配置
- `POST /api/generate_preview` - 生成預覽
- `GET /api/preview_image` - 獲取預覽圖片

### 機器人控制 API
- `POST /api/control_bot` - 控制機器人

## 故障排除

### 常見問題

1. **機器人無法啟動**
   - 檢查 Discord Token 是否正確
   - 確認網路連接
   - 查看錯誤日誌

2. **音樂播放問題**
   - 檢查 FFmpeg 安裝
   - 確認音頻文件格式
   - 檢查語音頻道權限

3. **網頁儀表板無法訪問**
   - 確認端口 5000 未被佔用
   - 檢查防火牆設定
   - 確認依賴已安裝

4. **歡迎卡片生成失敗**
   - 檢查圖片和字體文件
   - 確認文件路徑正確
   - 查看錯誤日誌

## 更新日誌

### v1.0.0 (最新)
- 完整的 Discord Bot 功能
- 網頁管理儀表板
- 歡迎卡片可視化配置
- 系統監控和日誌管理
- Orange Pi 部署支援

## 開發計劃

### 短期目標
- [ ] 添加更多遊戲功能
- [ ] 改進音樂播放體驗
- [ ] 增強網頁儀表板功能

### 長期目標
- [ ] 移動端應用
- [ ] 多語言支援
- [ ] 雲端部署支援
- [ ] 機器學習功能

## 貢獻指南

1. Fork 項目
2. 創建功能分支
3. 提交更改
4. 發起 Pull Request

## 授權

本項目遵循 MIT 授權條款。

## 聯繫方式

如有問題或建議，請通過以下方式聯繫：
- GitHub Issues
- Discord 伺服器
- 電子郵件

---

**注意**: 本系統需要 Python 3.7+ 和 Discord.py 2.0+ 支援。 