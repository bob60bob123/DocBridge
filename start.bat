@echo off
chcp 65001 >nul 2>&1
title Format Converter
cd /d "%~dp0"
echo ========================================
echo       Format Converter v0.3.0
echo ========================================
echo.
python src\gui_qt.py
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start. Please check Python installation.
    echo Make sure Python 3.11+ is installed.
    echo.
    pause
)
