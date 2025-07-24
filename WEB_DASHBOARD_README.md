# Discord Bot 網頁儀表板

這是一個用於管理 Discord Bot 的網頁儀表板，提供系統監控、日誌查看、歡迎卡片配置和機器人控制功能。

## 功能特色

### 🖥️ 系統監控
- 即時 CPU、記憶體、磁碟使用率
- 網路流量監控
- 系統資源使用情況

### 📋 日誌查看
- 即時查看機器人日誌
- 自動滾動顯示最新日誌
- 支援日誌重新整理和清除

### 🎨 歡迎卡片配置
- 視覺化配置歡迎卡片
- 背景圖片選擇
- 字體和顏色設定
- 文字位置調整
- 即時預覽功能

### 🤖 機器人控制
- 啟動/停止/重啟機器人
- 機器人狀態監控
- 一鍵控制功能

## 安裝說明

### 1. 安裝依賴

```bash
pip install -r web_requirements.txt
```

### 2. 啟動儀表板

```bash
python start_web_dashboard.py
```

或者直接啟動：

```bash
python web_dashboard.py
```

### 3. 訪問儀表板

打開瀏覽器訪問：`http://localhost:5000`

## 文件結構

```
Bot/
├── web_dashboard.py          # 主應用程式
├── start_web_dashboard.py    # 啟動腳本
├── web_requirements.txt      # Python 依賴
├── templates/
│   └── dashboard.html        # 儀表板模板
├── welcome_card_config.json  # 歡迎卡片配置（自動生成）
└── welcome_card_preview.png  # 預覽圖片（自動生成）
```

## 配置說明

### 歡迎卡片配置

儀表板會自動創建 `welcome_card_config.json` 文件，包含以下配置：

```json
{
  "background_image": "welcome_card.png",
  "font_file": "Arial_1.ttf",
  "font_size": 60,
  "text_color": "#FFFFFF",
  "subtitle_position": {
    "x": 400,
    "y": 300
  },
  "main_text_position": {
    "x": 400,
    "y": 200
  }
}
```

### 支援的文件格式

- **背景圖片**: PNG, JPG, JPEG
- **字體文件**: TTF, OTF

## API 端點

### 系統信息
- `GET /api/system_info` - 獲取系統狀態

### 日誌
- `GET /api/logs?lines=50` - 獲取日誌（可指定行數）

### 歡迎卡片配置
- `GET /api/welcome_card_config` - 獲取配置
- `POST /api/welcome_card_config` - 保存配置
- `POST /api/generate_preview` - 生成預覽
- `GET /api/preview_image` - 獲取預覽圖片
- `GET /api/available_files` - 獲取可用文件列表

### 機器人控制
- `POST /api/control_bot` - 控制機器人（start/stop/restart）

## 使用說明

### 系統監控
1. 儀表板會每 5 秒自動更新系統信息
2. 點擊「重新整理」按鈕可手動更新

### 日誌查看
1. 日誌會每 10 秒自動更新
2. 使用「重新整理日誌」按鈕手動更新
3. 使用「清除顯示」按鈕清空顯示區域

### 歡迎卡片配置
1. 選擇背景圖片和字體文件
2. 調整字體大小和顏色
3. 設定文字位置座標
4. 點擊「保存配置」保存設定
5. 點擊「生成預覽」查看效果

### 機器人控制
1. 查看機器人當前狀態
2. 使用按鈕控制機器人：
   - **啟動**: 啟動機器人
   - **重啟**: 重啟機器人
   - **停止**: 停止機器人

## 故障排除

### 常見問題

1. **儀表板無法啟動**
   - 檢查是否安裝了所有依賴
   - 確認 Python 版本（建議 3.7+）

2. **無法訪問儀表板**
   - 確認端口 5000 未被佔用
   - 檢查防火牆設定

3. **歡迎卡片預覽失敗**
   - 確認背景圖片和字體文件存在
   - 檢查文件格式是否支援

4. **機器人控制失敗**
   - 確認 bot.py 文件存在
   - 檢查 Python 環境

### 日誌查看

如果遇到問題，可以查看控制台輸出來診斷問題。

## 安全注意事項

1. 儀表板預設綁定到所有網路介面（0.0.0.0）
2. 建議在生產環境中使用反向代理（如 Nginx）
3. 考慮添加身份驗證機制
4. 定期更新依賴套件

## 開發說明

### 添加新功能

1. 在 `web_dashboard.py` 中添加新的路由
2. 在 `templates/dashboard.html` 中添加對應的 UI
3. 更新 JavaScript 代碼處理新功能

### 自定義樣式

修改 `templates/dashboard.html` 中的 CSS 樣式來自定義外觀。

## 版本歷史

- v1.0.0 - 初始版本
  - 基本系統監控
  - 日誌查看功能
  - 歡迎卡片配置
  - 機器人控制

## 授權

本項目遵循 MIT 授權條款。 