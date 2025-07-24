# 重複播放功能使用指南

## 問題描述

你的 Discord Bot 的 `/repeat` 命令無法正常使用。這通常是由於以下原因：

1. **顏色代碼問題** - 使用了舊版的 `discord.Color.light_grey()`
2. **重複播放邏輯問題** - 播放器邏輯可能有缺陷
3. **命令註冊問題** - 斜線命令可能沒有正確註冊

## 修復方案

### 方案一：使用修復腳本（推薦）

#### Linux/Orange Pi 環境
```bash
chmod +x check_venv_and_fix.sh
./check_venv_and_fix.sh
```

#### Windows 環境
```cmd
check_venv_and_fix.bat
```

### 方案二：手動修復

#### 1. 修復顏色代碼
在 `cogs/music.py` 中找到：
```python
color=discord.Color.green() if player.repeat else discord.Color.light_grey()
```

改為：
```python
color=discord.Color.green() if player.repeat else discord.Color.light_gray()
```

#### 2. 檢查重複播放邏輯
確保 `AutoMusicPlayer` 類的 `next()` 方法包含正確的重複播放邏輯：

```python
def next(self):
    # 如果開啟重複播放且有當前歌曲
    if self.repeat and self.current:
        logger.debug(f"[Queue] 重複播放：{self.current['title']}")
        return self.current
    
    # 如果隊列中有歌曲
    if self.queue:
        self.current = self.queue.popleft()
        logger.debug(f"[Queue] 取出下一首：{self.current['title']}")
        return self.current
    
    # 如果沒有歌曲且開啟重複播放，但沒有當前歌曲
    if self.repeat and not self.current:
        logger.debug("[Queue] 重複播放開啟但沒有當前歌曲")
        return None
        
    # 播放隊列空了
    self.current = None
    logger.debug("[Queue] 播放隊列空了")
    return None
```

#### 3. 檢查命令註冊
確保 `/repeat` 命令正確註冊：

```python
@app_commands.command(name="repeat", description="切換重複播放")
async def repeat(self, interaction: discord.Interaction):
    try:
        player = self.get_player(interaction.guild.id)
        player.repeat = not player.repeat
        status = "開啟" if player.repeat else "關閉"
        
        embed = discord.Embed(
            title="🔁 重複播放設定",
            description=f"重複播放已**{status}**",
            color=discord.Color.green() if player.repeat else discord.Color.light_gray()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"[repeat] 切換重複播放失敗: {e}")
        await interaction.response.send_message(f"❌ 切換重複播放失敗：{str(e)}", ephemeral=True)
```

## 使用方法

### 1. 使用斜線命令
```
/repeat
```
- 切換重複播放的開啟/關閉狀態
- 會顯示當前狀態的嵌入訊息

### 2. 使用音樂控制按鈕
- 播放音樂時會顯示控制按鈕
- 點擊 🔁 按鈕可以切換重複播放

### 3. 查看狀態
```
/queue
```
- 顯示播放隊列
- 包含重複播放狀態

```
/nowplaying
```
- 顯示目前播放的音樂
- 包含重複播放狀態

## 重複播放邏輯

### 開啟重複播放時：
1. 當前歌曲播放完畢後，會重新播放同一首歌曲
2. 如果沒有當前歌曲，重複播放不會生效
3. 重複播放只會重複最後播放的歌曲

### 關閉重複播放時：
1. 正常播放隊列中的歌曲
2. 播放完畢後停止

## 測試功能

### 使用測試腳本

#### 邏輯測試（不需要虛擬環境）
```bash
python3 test_repeat_logic.py
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

### 手動測試步驟
1. 播放一首歌曲
2. 使用 `/repeat` 開啟重複播放
3. 等待歌曲播放完畢
4. 確認歌曲重新播放
5. 再次使用 `/repeat` 關閉重複播放

## 常見問題

### Q: `/repeat` 命令沒有回應？
A: 檢查 Bot 是否有正確的權限，確保命令已註冊。

### Q: 重複播放不生效？
A: 確保有歌曲正在播放，重複播放需要當前歌曲才能生效。

### Q: 顏色顯示錯誤？
A: 使用 `discord.Color.light_gray()` 而不是 `discord.Color.light_grey()`。

### Q: 重複播放按鈕不顯示？
A: 確保音樂正在播放，控制按鈕只在播放時顯示。

## 故障排除

### 1. 檢查日誌
```bash
tail -f bot.log | grep -i repeat
```

### 2. 檢查命令註冊
```bash
grep -n "repeat" cogs/music.py
```

### 3. 測試播放器邏輯
```bash
python3 test_repeat_function.py
```

## 相關檔案

- `check_venv_and_fix.sh` - Linux 完整檢查和修復腳本
- `check_venv_and_fix.bat` - Windows 完整檢查和修復腳本
- `fix_repeat_command.sh` - Linux 簡單修復腳本
- `fix_repeat_command.bat` - Windows 簡單修復腳本
- `test_repeat_logic.py` - 重複播放邏輯測試（不需要虛擬環境）
- `test_repeat_function.py` - 重複播放完整測試（需要虛擬環境）
- `cogs/music.py` - 音樂功能主檔案

## 更新日誌

- 2025-07-10: 創建初始版本
- 2025-07-10: 修復顏色代碼問題
- 2025-07-10: 改進重複播放邏輯
- 2025-07-10: 添加測試工具 