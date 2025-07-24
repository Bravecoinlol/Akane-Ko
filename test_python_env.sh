#!/bin/bash

# 測試 Python 環境的腳本

echo "=== Python 環境測試 ==="
echo ""

# 檢查 Python 版本
echo "1. 檢查 Python 版本:"
if command -v python3 &> /dev/null; then
    echo "✅ python3 可用:"
    python3 --version
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    echo "✅ python 可用:"
    python --version
    PYTHON_CMD="python"
else
    echo "❌ 找不到 Python 命令"
    echo "請安裝 Python3: sudo apt install python3"
    exit 1
fi

echo ""
echo "2. 檢查 pip 版本:"
if command -v pip3 &> /dev/null; then
    echo "✅ pip3 可用:"
    pip3 --version
elif command -v pip &> /dev/null; then
    echo "✅ pip 可用:"
    pip --version
else
    echo "❌ 找不到 pip 命令"
    echo "請安裝 pip: sudo apt install python3-pip"
fi

echo ""
echo "3. 檢查虛擬環境:"
if [ -d "venv" ]; then
    echo "✅ 虛擬環境存在"
    echo "虛擬環境路徑: $(pwd)/venv"
    
    # 測試虛擬環境中的 Python
    if [ -f "venv/bin/python" ]; then
        echo "✅ 虛擬環境中的 Python 可用"
        venv/bin/python --version
    else
        echo "❌ 虛擬環境中的 Python 不可用"
    fi
else
    echo "❌ 虛擬環境不存在"
fi

echo ""
echo "4. 檢查 Discord.py:"
if [ -d "venv" ]; then
    # 在虛擬環境中檢查
    if venv/bin/python -c "import discord; print('Discord.py 版本:', discord.__version__)" 2>/dev/null; then
        echo "✅ Discord.py 已安裝在虛擬環境中"
    else
        echo "❌ Discord.py 未安裝在虛擬環境中"
    fi
else
    # 在系統中檢查
    if $PYTHON_CMD -c "import discord; print('Discord.py 版本:', discord.__version__)" 2>/dev/null; then
        echo "✅ Discord.py 已安裝在系統中"
    else
        echo "❌ Discord.py 未安裝"
    fi
fi

echo ""
echo "5. 檢查必要文件:"
if [ -f "bot.py" ]; then
    echo "✅ bot.py 存在"
else
    echo "❌ bot.py 不存在"
fi

if [ -f ".env" ]; then
    echo "✅ .env 配置文件存在"
else
    echo "❌ .env 配置文件不存在"
fi

if [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt 存在"
else
    echo "❌ requirements.txt 不存在"
fi

echo ""
echo "6. 測試 bot.py 語法:"
if [ -d "venv" ]; then
    if venv/bin/python -m py_compile bot.py 2>/dev/null; then
        echo "✅ bot.py 語法正確"
    else
        echo "❌ bot.py 語法錯誤"
    fi
else
    if $PYTHON_CMD -m py_compile bot.py 2>/dev/null; then
        echo "✅ bot.py 語法正確"
    else
        echo "❌ bot.py 語法錯誤"
    fi
fi

echo ""
echo "=== 測試完成 ==="
echo ""
echo "建議:"
echo "1. 如果 Python 不可用，請安裝: sudo apt install python3 python3-pip"
echo "2. 如果虛擬環境不存在，請創建: python3 -m venv venv"
echo "3. 如果依賴未安裝，請安裝: pip install -r requirements.txt"
echo "4. 如果配置文件不存在，請複製: cp env_example.txt .env" 