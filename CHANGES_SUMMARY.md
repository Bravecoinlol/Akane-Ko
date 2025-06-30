# Discord Bot 伺服器修改總結

## 更新日誌

### 2025/6/30 - 錯誤處理與穩定性改進

#### 🔧 主要改進
- **全面錯誤處理優化**: 為所有 cogs 添加詳細的錯誤處理機制
- **用戶體驗提升**: 將模糊的錯誤訊息改為詳細、友善的嵌入訊息
- **Cog 載入問題修復**: 解決 cog 重複載入和名稱衝突問題
- **輸入驗證加強**: 為所有命令添加參數驗證和權限檢查
- **網路連線穩定性修復**: 解決音樂播放和語音連線的網路超時問題
- **互動超時處理**: 修復 Discord 互動超時導致的錯誤

#### 📋 詳細更新內容

##### 1. 錯誤處理系統改進
**影響的 Cogs:**
- `role_manager.py` - 角色管理系統
- `minigames.py` - 小遊戲系統  
- `utility_tools.py` - 實用工具
- `image_tools.py` - 圖片處理工具
- `music.py` - 音樂播放系統
- `chat_responses.py` - 聊天回應系統
- `analytics.py` - 數據分析系統
- `antiraid.py` - 反惡意系統
- `member.py` - 成員管理
- `ping_number.py` - 數字遊戲
- `QuestionCog.py` - 問答系統
- `advanced_games.py` - 進階遊戲

**改進內容:**
- ✅ 添加 try-except 錯誤捕獲機制
- ✅ 輸入參數驗證和類型檢查
- ✅ 權限檢查和用戶友善提示
- ✅ API 錯誤處理和重試機制
- ✅ 檔案操作錯誤處理
- ✅ 網路連線錯誤處理
- ✅ JSON 解析錯誤處理
- ✅ 詳細的錯誤日誌記錄

##### 2. 網路連線穩定性修復
**音樂播放系統修復:**
- 🔧 修復 `TimeoutError` 網路超時問題
- ⏰ 添加 30 秒搜尋超時限制
- 🔄 實現指數退避重試機制
- 🛡️ 添加互動超時保護
- 📊 改進錯誤訊息顯示

**語音連線穩定性:**
- 🔌 修復語音客戶端斷線問題
- 🔄 添加自動重連機制 (最多3次)
- ⏱️ 實現智能重連延遲
- 🧹 定期清理無效連線
- 📢 斷線時自動通知用戶

**互動超時處理:**
- ⚡ 修復 Discord 互動超時錯誤
- 🛡️ 添加 `discord.NotFound` 錯誤處理
- 🔄 實現互動狀態檢查
- 📝 改進錯誤日誌記錄

##### 3. 用戶體驗提升
**錯誤訊息改進:**
- 🔄 從簡單文字錯誤改為詳細的 Discord Embed
- 🎨 使用顏色編碼區分不同類型的錯誤
- 📝 提供具體的錯誤原因和解決建議
- ⚡ 添加錯誤代碼便於追蹤問題

**成功訊息改進:**
- ✅ 統一的成功訊息格式
- 📊 添加操作結果統計
- 🎯 提供後續操作建議

**載入狀態顯示:**
- 🔍 音樂搜尋時顯示載入訊息
- ⏳ 添加進度指示器
- 📈 預估等待時間顯示

**猜數字遊戲改進:**
- 🗑️ 刪除 `/猜` 命令，改用回覆方式
- 💬 直接回覆 Bot 訊息即可猜測數字
- 🎯 更直觀的遊戲體驗
- 🏆 支援多人參與自定義遊戲
- 📝 改進遊戲規則說明
- 🎨 美化遊戲介面和訊息

##### 4. 權限系統優化
**管理員權限檢查:**
- 🔒 加強管理員權限驗證
- 👥 支援自定義管理員角色
- 🛡️ 防止權限提升攻擊

**Bot 權限檢查:**
- 🤖 檢查 Bot 必要權限
- 📋 提供權限不足時的具體提示
- 🔧 自動處理權限相關錯誤

##### 5. 輸入驗證系統
**參數驗證:**
- 📏 字串長度限制檢查
- 🔢 數值範圍驗證
- 📅 日期格式驗證
- 🆔 ID 格式驗證
- 📍 URL 格式驗證

**內容過濾:**
- 🚫 敏感詞彙過濾
- 🔍 惡意內容檢測
- 🛡️ 垃圾訊息防護

##### 6. 日誌系統改進
**詳細日誌記錄:**
- 📝 操作成功/失敗記錄
- 👤 用戶行為追蹤
- ⏰ 時間戳記錄
- 🔍 錯誤堆疊追蹤
- 📊 性能監控數據

**日誌分類:**
- 🚨 錯誤日誌 (ERROR)
- ⚠️ 警告日誌 (WARNING)
- ℹ️ 資訊日誌 (INFO)
- 🔍 除錯日誌 (DEBUG)

##### 7. 穩定性改進
**記憶體管理:**
- 🧹 自動清理暫存數據
- 💾 優化檔案讀寫操作
- 🔄 定期數據備份

**連線穩定性:**
- 🔄 自動重連機制
- ⏱️ 連線超時處理
- 🛡️ 網路錯誤恢復

**配置管理:**
- ⚙️ 新增音樂配置系統
- 🔧 改進 FFmpeg 配置管理
- 📁 統一配置檔案格式

#### 🎯 技術改進

##### 錯誤處理模式
```python
try:
    # 先回應互動，避免超時
    await interaction.response.defer(thinking=True)
except discord.NotFound:
    # 如果互動已經超時，直接返回
    logger.warning(f"[command] 互動已超時，用戶: {interaction.user.name}")
    return
except Exception as e:
    logger.error(f"[command] 回應互動失敗: {e}")
    return

try:
    # 主要操作邏輯
    result = await perform_operation()
    
    # 成功回應
    embed = discord.Embed(
        title="✅ 操作成功",
        description="操作已完成",
        color=discord.Color.green()
    )
    await interaction.followup.send(embed=embed)
    
except asyncio.TimeoutError:
    # 超時錯誤處理
    embed = discord.Embed(
        title="⏰ 操作超時",
        description="操作執行時間過長，請稍後再試",
        color=discord.Color.orange()
    )
    await interaction.followup.send(embed=embed)
    
except discord.NotFound:
    # 互動已失效
    logger.warning(f"[command] 互動已失效，用戶: {interaction.user.name}")
    
except discord.Forbidden:
    # 權限錯誤處理
    embed = discord.Embed(
        title="❌ 權限不足",
        description="Bot 缺少必要權限",
        color=discord.Color.red()
    )
    await interaction.followup.send(embed=embed)
    
except Exception as e:
    # 一般錯誤處理
    logger.error(f"操作失敗: {e}")
    embed = discord.Embed(
        title="❌ 執行錯誤",
        description=f"發生未預期的錯誤：{str(e)}",
        color=discord.Color.red()
    )
    await interaction.followup.send(embed=embed)
```

##### 語音連線重連機制
```python
@commands.Cog.listener()
async def on_voice_client_disconnect(self, voice_client):
    """處理語音客戶端斷線"""
    try:
        guild_id = voice_client.guild.id
        attempts = self.reconnect_attempts.get(guild_id, 0)
        
        if attempts < self.max_reconnect_attempts:
            self.reconnect_attempts[guild_id] = attempts + 1
            await asyncio.sleep(self.reconnect_delay)
            
            try:
                await voice_client.connect(timeout=20.0, self_deaf=True)
                self.reconnect_attempts[guild_id] = 0  # 重置計數
                logger.info(f"重連成功: {voice_client.guild.name}")
            except Exception as e:
                logger.error(f"重連失敗: {e}")
                
    except Exception as e:
        logger.error(f"處理斷線失敗: {e}")
```

#### 📈 性能改進
- ⚡ 減少不必要的 API 呼叫
- 🧹 優化記憶體使用
- 🔄 改善錯誤恢復速度
- 📊 添加性能監控
- 🔄 實現智能重試機制

#### 🔧 維護性改進
- 📝 統一的錯誤處理模式
- 🎯 模組化的驗證函數
- 🔍 詳細的日誌記錄
- 📚 完整的錯誤代碼文檔
- ⚙️ 配置檔案管理系統

#### 🚀 未來計劃
- 🔄 自動錯誤報告系統
- 📊 用戶行為分析
- 🛡️ 進階安全功能
- 🎮 更多遊戲功能
- 🌐 網路連線優化

---

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

### 🔧 身分組管理器 (role_manager.py) - 互動超時修復
- **修復身分組按鈕互動超時問題**
  - 添加 `interaction.response.defer()` 立即回應，避免 3 秒超時
  - 使用 `interaction.followup.send()` 替代 `interaction.response.send_message()`
  - 添加 `discord.NotFound` 異常處理，處理互動已失效的情況
  - 改進錯誤訊息格式，提供更詳細的錯誤資訊和建議

- **修復身分組選擇器互動問題**
  - 修復 `RoleSelect` 回調函數的互動超時
  - 修復 `CreatePanelButton` 的互動處理
  - 添加完整的錯誤處理和日誌記錄

- **修復命令互動問題**
  - 修復 `/createidentify` 命令的互動超時
  - 修復 `/listidentify` 命令的互動處理
  - 修復 `/clearidentify` 命令的錯誤處理
  - 修復 `/removeidentify` 命令的互動回應

- **改進錯誤處理機制**
  - 添加分層錯誤處理：權限錯誤、HTTP錯誤、一般錯誤
  - 每個錯誤類型都有專門的處理邏輯
  - 添加詳細的日誌記錄，便於除錯
  - 提供用戶友好的錯誤訊息和解決建議

- **隱私保護改進**
  - 所有身分組操作回應都設為 `ephemeral=True`（只有自己可見）
  - 創建面板完成通知只對管理員可見
  - 添加面板資訊（訊息ID、頻道、身分組數量）到管理員通知
  - 保持身分組選擇面板公開（用戶需要看到才能選擇）

- **穩定性提升**
  - 所有互動操作都有適當的超時處理
  - 添加網路錯誤重試機制
  - 改進身分組操作的可靠性
  - 防止因互動超時導致的「此交互失敗」錯誤

### 🎮 猜數字遊戲 (minigames.py) - 回覆式猜測系統
- **移除 `/猜` 命令**
  - 刪除原有的斜線命令猜測功能
  - 簡化命令結構，避免重複功能

- **實現回覆式猜測系統**
  - 用戶使用 `/猜數字` 開始遊戲
  - 用戶回覆機器人的遊戲訊息來猜測數字
  - 機器人檢查回覆內容並提供提示
  - 支援多種數字格式：純數字、包含數字的文字

- **改進用戶體驗**
  - 清晰的遊戲說明和操作指引
  - 即時反饋和提示訊息
  - 遊戲狀態追蹤和管理
  - 自動清理過期遊戲

- **增強錯誤處理**
  - 處理無效回覆和格式錯誤
  - 防止重複猜測和作弊行為
  - 改進互動超時處理
  - 添加詳細的錯誤日誌

### 🎵 音樂播放器 (music.py) - 穩定性提升
- **修復播放命令超時問題**
  - 添加 `interaction.response.defer()` 立即回應
  - 實現分階段回應機制
  - 改進錯誤處理和用戶反饋

- **修復 Cog 載入錯誤**
  - 修復 `AttributeError: loop attribute cannot be accessed in non-async contexts` 錯誤
  - 將異步任務創建從 `__init__` 移到 `setup` 函數
  - 添加 `_start_cleanup_task()` 方法來安全啟動清理任務
  - 改進異步初始化流程

- **增強語音連接穩定性**
  - 添加自動重連機制
  - 改進連接狀態檢查
  - 添加清理任務防止記憶體洩漏

- **改進錯誤處理**
  - 處理網路延遲和連接問題
  - 添加重試機制
  - 提供更詳細的錯誤訊息

### 🔧 其他改進
- **日誌系統優化**
  - 添加更詳細的錯誤日誌
  - 改進日誌格式和分類
  - 便於除錯和問題追蹤

- **代碼結構優化**
  - 統一錯誤處理模式
  - 改進代碼可讀性
  - 添加適當的註釋和文檔

- **用戶體驗提升**
  - 更清晰的錯誤訊息
  - 改進操作指引
  - 減少用戶困惑

---

## 技術細節

### 互動超時修復原理
1. **立即回應**: 使用 `interaction.response.defer()` 在 3 秒內回應 Discord
2. **分階段處理**: 先回應，再執行實際操作
3. **錯誤處理**: 處理各種可能的錯誤情況
4. **用戶反饋**: 提供清晰的狀態和錯誤訊息

### 回覆式猜測系統設計
1. **遊戲初始化**: `/猜數字` 命令創建遊戲狀態
2. **回覆檢測**: 監聽對遊戲訊息的回覆
3. **內容解析**: 提取回覆中的數字
4. **狀態管理**: 追蹤遊戲進度和結果

### 穩定性改進
1. **連接管理**: 自動處理語音連接問題
2. **錯誤恢復**: 從各種錯誤狀態中恢復
3. **資源清理**: 防止記憶體洩漏和資源浪費 