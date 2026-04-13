#!/bin/bash
# FitVision MVP - Quick Start Script for macOS/Linux

echo ""
echo "======================================"
echo "  FitVision MVP - Bicep Curl Demo"
echo "  Quick Start Script"
echo "======================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[Error] Python 3 未安装。请先安装 Python 3.9+"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "[1/3] 创建虚拟环境..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[Error] 虚拟环境创建失败！"
        exit 1
    fi
    echo "[✓] 虚拟环境创建成功"
else
    echo "[✓] 虚拟环境已存在"
fi

# 激活虚拟环境
echo "[2/3] 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "[3/3] 安装 Python 依赖包..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[Error] 依赖安装失败！"
    exit 1
fi

echo ""
echo "======================================"
echo "  ✓ 环境准备完成！"
echo "======================================"
echo ""
echo "即将启动 FitVision MVP..."
echo "提示: 按 Q 键退出程序"
echo ""

# 启动程序
cd src
python main.py
cd ..
