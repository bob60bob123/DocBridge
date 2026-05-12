@echo off
chcp 65001 >nul 2>&1
title 格式转换器
cd /d "%~dp0"
echo ========================================
echo          格式转换器 v0.3.0
echo ========================================
echo.
python src\gui_qt.py
if errorlevel 1 (
    echo.
    echo [错误] 启动失败，请检查Python环境
    echo 提示: 确保已安装 Python 3.11+ 和依赖库
    echo 按任意键退出...
    pause >nul
)
