# 音樂系統修復指南

## 問題描述

從日誌中發現以下問題：

1. **yt-dlp JavaScript 解釋器阻塞**：導致 voice heartbeat 被阻塞超過10-20秒
2. **FFmpeg 連接問題**：出現 "End of file" 錯誤和重複重連嘗試
3. **重複的 FFmpeg 選項警告**：Multiple -ac 和 -ar 選項
4. **/repeat 命令無法使用**：由於系統阻塞導致

## 已修復的問題

### 1. yt-dlp 配置優化

**問題**：JavaScript 解釋器過於複雜，導致阻塞
**解決方案**：
- 減少重試次數和超時時間
- 添加 `skip: ['dash', 'live']` 避免複雜格式
- 使用 `prefer_insecure: True` 避免簽名解密
- 添加 `asyncio.wait_for` 超時控制

### 2. FFmpeg 配置修復

**問題**：重複的音頻選項和過於複雜的重連設定
**解決方案**：
- 移除重複的 `-ac` 和 `-ar` 選項
- 簡化重連選項
- 移除 `-af volume=0.5` 避免衝突

### 3. 快取清理

**問題**：快取檔案過大（3.3MB）導致載入緩慢
**解決方案**：
- 清空 `song_cache.json`
- 重新建立空快取檔案

### 4. 日誌系統改善

**問題**：使用 `print` 而非 `logger`
**解決方案**：
- 將所有 `print` 改為 `logger.error/info`
- 改善錯誤追蹤

## 修復檔案清單

1. `cogs/music.py` - 主要音樂系統檔案
2. `ffmpeg_config.json` - FFmpeg 配置
3. `song_cache.json` - 歌曲快取（已清空）
4. `fix_music_system.py` - 修復腳本
5. `test_music_fix.py` - 測試腳本

## 使用方法

### 重新啟動 Bot

```bash
# 停止當前 Bot
# 重新啟動
python bot.py
```

### 測試修復

```bash
python test_music_fix.py
```

### 手動修復（如果需要）

```bash
python fix_music_system.py
```

## 預期改善

1. **/repeat 命令**：應該可以正常使用
2. **播放穩定性**：減少連接錯誤和重連
3. **響應速度**：更快的歌曲搜尋和載入
4. **日誌清晰度**：更好的錯誤追蹤

## 監控建議

1. 觀察新的日誌輸出
2. 測試 `/repeat` 命令功能
3. 檢查語音連接穩定性
4. 監控快取檔案大小

## 故障排除

如果問題仍然存在：

1. **檢查 FFmpeg 安裝**：
   ```bash
   ffmpeg -version
   ```

2. **檢查網路連線**：
   ```bash
   ping youtube.com
   ```

3. **清理所有快取**：
   ```bash
   rm song_cache.json
   echo "{}" > song_cache.json
   ```

4. **重新安裝 yt-dlp**：
   ```bash
   pip install --upgrade yt-dlp
   ```

## 聯繫支援

如果問題持續，請提供：
- 新的錯誤日誌
- 系統環境資訊
- 具體的錯誤步驟 