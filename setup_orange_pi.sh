#!/bin/bash
# 香橙派 Discord Bot 自動化設定腳本

echo "🍊 香橙派 Discord Bot 設定開始"
echo "=================================="

# 更新系統
echo "📦 更新系統套件..."
sudo apt update && sudo apt upgrade -y

# 安裝必要套件
echo "🔧 安裝必要套件..."
sudo apt install -y python3 python3-pip python3-venv git screen htop

# 安裝圖片處理套件
echo "🖼️ 安裝圖片處理套件..."
sudo apt install -y python3-pil python3-pil.imagetk

# 安裝字體
echo "📝 安裝字體..."
sudo apt install -y fonts-liberation

# 設定 swap 空間
echo "💾 設定 swap 空間..."
if [ ! -f /swapfile ]; then
    sudo fallocate -l 1G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

# 創建 bot 目錄
echo "📁 創建 bot 目錄..."
mkdir -p ~/discord-bot
cd ~/discord-bot

# 創建 Python 虛擬環境
echo "🐍 創建 Python 虛擬環境..."
python3 -m venv bot_env
source bot_env/bin/activate

# 安裝 Python 套件
echo "📦 安裝 Python 套件..."
pip install discord.py python-dotenv pillow requests aiohttp

# 創建 systemd 服務
echo "⚙️ 創建 systemd 服務..."
sudo tee /etc/systemd/system/discord-bot.service > /dev/null <<EOF
[Unit]
Description=Discord Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/discord-bot
Environment=PATH=/home/$USER/discord-bot/bot_env/bin
ExecStart=/home/$USER/discord-bot/bot_env/bin/python bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 啟用服務
echo "🚀 啟用自動啟動服務..."
sudo systemctl daemon-reload
sudo systemctl enable discord-bot

# 創建管理腳本
echo "📝 創建管理腳本..."
tee ~/discord-bot/manage.sh > /dev/null <<EOF
#!/bin/bash
# Discord Bot 管理腳本

case "\$1" in
    start)
        echo "🚀 啟動 Discord Bot..."
        sudo systemctl start discord-bot
        ;;
    stop)
        echo "🛑 停止 Discord Bot..."
        sudo systemctl stop discord-bot
        ;;
    restart)
        echo "🔄 重啟 Discord Bot..."
        sudo systemctl restart discord-bot
        ;;
    status)
        echo "📊 Discord Bot 狀態..."
        sudo systemctl status discord-bot
        ;;
    logs)
        echo "📋 Discord Bot 日誌..."
        sudo journalctl -u discord-bot -f
        ;;
    screen)
        echo "🖥️ 使用 screen 啟動..."
        screen -S discord-bot python3 bot.py
        ;;
    *)
        echo "用法: \$0 {start|stop|restart|status|logs|screen}"
        exit 1
        ;;
esac
EOF

chmod +x ~/discord-bot/manage.sh

# 設定 SSH（如果還沒設定）
echo "🔐 設定 SSH..."
sudo systemctl enable ssh
sudo systemctl start ssh

# 顯示網路資訊
echo "🌐 網路資訊..."
echo "IP 地址:"
hostname -I

echo ""
echo "=================================="
echo "✅ 設定完成！"
echo ""
echo "📋 使用說明："
echo "1. 將 bot.py 和其他檔案複製到 ~/discord-bot/"
echo "2. 設定 .env 檔案（包含 TOKEN）"
echo "3. 啟動 bot: ~/discord-bot/manage.sh start"
echo "4. 查看狀態: ~/discord-bot/manage.sh status"
echo "5. 查看日誌: ~/discord-bot/manage.sh logs"
echo ""
echo "🔌 斷電後重啟會自動啟動 bot"
echo "🌐 SSH 連線: ssh $USER@$(hostname -I | awk '{print $1}')"
echo "==================================" 