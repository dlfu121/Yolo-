@echo off
REM FitVision MVP - Quick Start Script for Windows

echo.
echo ======================================
echo   FitVision MVP - Bicep Curl Demo
echo   Quick Start Script
echo ======================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python 未安装或未在 PATH 中。请先安装 Python 3.9+
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv" (
    echo [1/3] 创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo [Error] 虚拟环境创建失败！
        pause
        exit /b 1
    )
    echo [✓] 虚拟环境创建成功
) else (
    echo [✓] 虚拟环境已存在
)

REM 激活虚拟环境
echo [2/3] 激活虚拟环境...
call venv\Scripts\activate.bat

REM 检查并安装依赖
echo [3/3] 安装 Python 依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo [Error] 依赖安装失败！
    pause
    exit /b 1
)

echo.
echo ======================================
echo   ✓ 环境准备完成！
echo ======================================
echo.
echo 即将启动 FitVision MVP...
echo 提示: 按 Q 键退出程序
echo.

REM 启动程序
cd src
python main.py
cd ..

pause
