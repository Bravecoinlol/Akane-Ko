#!/bin/bash

# Discord Bot 網頁儀表板安裝腳本
# 適用於 Orange Pi One

set -e

echo "=== Discord Bot 網頁儀表板安裝腳本 ==="
echo "適用於 Orange Pi One"
echo ""

# 檢查是否為 root 用戶
if [ "$EUID" -eq 0 ]; then
    echo "請不要使用 root 用戶運行此腳本"
    exit 1
fi

# 檢查系統
echo "檢查系統環境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安裝，正在安裝..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
fi

if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 未安裝，正在安裝..."
    sudo apt install -y python3-pip
fi

echo "✓ Python3 環境檢查完成"

# 創建虛擬環境
echo "創建 Python 虛擬環境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ 虛擬環境創建完成"
else
    echo "✓ 虛擬環境已存在"
fi

# 激活虛擬環境
echo "激活虛擬環境..."
source venv/bin/activate

# 升級 pip
echo "升級 pip..."
pip install --upgrade pip

# 安裝依賴
echo "安裝網頁儀表板依賴..."
pip install -r web_requirements.txt

# 安裝系統依賴
echo "安裝系統依賴..."
sudo apt update
sudo apt install -y python3-dev python3-pil python3-pil.imagetk

echo "✓ 依賴安裝完成"

# 創建必要目錄
echo "創建必要目錄..."
mkdir -p templates
mkdir -p logs

# 檢查必要文件
echo "檢查必要文件..."
required_files=("web_dashboard.py" "templates/dashboard.html" "web_requirements.txt")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 缺少必要文件: $file"
        exit 1
    fi
done

echo "✓ 所有文件檢查完成"

# 創建 systemd 服務
echo "創建 systemd 服務..."
sudo tee /etc/systemd/system/discord-bot-dashboard.service > /dev/null <<EOF
[Unit]
Description=Discord Bot Web Dashboard
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python web_dashboard.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✓ systemd 服務創建完成"

# 創建啟動腳本
echo "創建啟動腳本..."
cat > start_dashboard.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python web_dashboard.py
EOF

chmod +x start_dashboard.sh

# 創建停止腳本
echo "創建停止腳本..."
cat > stop_dashboard.sh << 'EOF'
#!/bin/bash
sudo systemctl stop discord-bot-dashboard
echo "網頁儀表板已停止"
EOF

chmod +x stop_dashboard.sh

# 創建狀態檢查腳本
echo "創建狀態檢查腳本..."
cat > status_dashboard.sh << 'EOF'
#!/bin/bash
echo "=== Discord Bot 網頁儀表板狀態 ==="
echo ""

echo "systemd 服務狀態:"
sudo systemctl status discord-bot-dashboard --no-pager -l

echo ""
echo "進程狀態:"
ps aux | grep web_dashboard.py | grep -v grep || echo "未找到運行中的進程"

echo ""
echo "端口使用情況:"
netstat -tlnp | grep :5000 || echo "端口 5000 未被使用"

echo ""
echo "日誌文件:"
if [ -f "logs/dashboard.log" ]; then
    echo "最近的日誌:"
    tail -10 logs/dashboard.log
else
    echo "日誌文件不存在"
fi
EOF

chmod +x status_dashboard.sh

# 創建日誌查看腳本
echo "創建日誌查看腳本..."
cat > view_logs.sh << 'EOF'
#!/bin/bash
echo "=== Discord Bot 網頁儀表板日誌 ==="
echo ""

if [ -f "logs/dashboard.log" ]; then
    tail -f logs/dashboard.log
else
    echo "日誌文件不存在"
fi
EOF

chmod +x view_logs.sh

# 創建配置備份腳本
echo "創建配置備份腳本..."
cat > backup_config.sh << 'EOF'
#!/bin/bash
echo "=== 備份配置 ==="
backup_dir="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"

# 備份配置文件
cp -f welcome_card_config.json "$backup_dir/" 2>/dev/null || echo "welcome_card_config.json 不存在"
cp -f setting.json "$backup_dir/" 2>/dev/null || echo "setting.json 不存在"
cp -f autorole_settings.json "$backup_dir/" 2>/dev/null || echo "autorole_settings.json 不存在"

echo "配置已備份到: $backup_dir"
ls -la "$backup_dir"
EOF

chmod +x backup_config.sh

# 創建還原配置腳本
echo "創建還原配置腳本..."
cat > restore_config.sh << 'EOF'
#!/bin/bash
echo "=== 還原配置 ==="

if [ $# -eq 0 ]; then
    echo "用法: $0 <備份目錄>"
    echo "可用的備份:"
    ls -d backup_* 2>/dev/null || echo "沒有找到備份目錄"
    exit 1
fi

backup_dir="$1"
if [ ! -d "$backup_dir" ]; then
    echo "錯誤: 備份目錄不存在: $backup_dir"
    exit 1
fi

echo "從 $backup_dir 還原配置..."
cp -f "$backup_dir"/*.json . 2>/dev/null || echo "沒有找到配置文件"

echo "配置還原完成"
EOF

chmod +x restore_config.sh

# 重新載入 systemd
echo "重新載入 systemd..."
sudo systemctl daemon-reload

# 啟用服務
echo "啟用服務..."
sudo systemctl enable discord-bot-dashboard

echo ""
echo "=== 安裝完成 ==="
echo ""
echo "可用命令:"
echo "  ./start_dashboard.sh     - 手動啟動儀表板"
echo "  ./stop_dashboard.sh      - 停止儀表板"
echo "  ./status_dashboard.sh    - 查看狀態"
echo "  ./view_logs.sh          - 查看日誌"
echo "  ./backup_config.sh      - 備份配置"
echo "  ./restore_config.sh     - 還原配置"
echo ""
echo "systemd 服務命令:"
echo "  sudo systemctl start discord-bot-dashboard    - 啟動服務"
echo "  sudo systemctl stop discord-bot-dashboard     - 停止服務"
echo "  sudo systemctl restart discord-bot-dashboard  - 重啟服務"
echo "  sudo systemctl status discord-bot-dashboard   - 查看服務狀態"
echo ""
echo "訪問地址:"
echo "  本地: http://localhost:5000"
echo "  網路: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "注意事項:"
echo "  1. 確保防火牆允許端口 5000"
echo "  2. 建議在生產環境中使用反向代理"
echo "  3. 定期備份配置文件"
echo ""
echo "安裝完成！" 