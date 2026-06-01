@echo off
chcp 65001 >nul
title Shopee Backlink Tool

echo.
echo ====================================================
echo           SHOPEE BACKLINK TOOL  --  Hybrid Engine
echo ====================================================
echo.

:: Kiem tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [LOI] Khong tim thay Python! Vui long cai Python 3.9+ tu python.org
    pause
    exit /b 1
)

echo [1/2] Dang cai / cap nhat thu vien...
pip install -r requirements.txt -q --disable-pip-version-check
if errorlevel 1 (
    echo [LOI] Cai dat thu vien that bai!
    pause
    exit /b 1
)

echo [2/2] Dang khoi chay tool...
echo.
python dashboard_app.py

echo.
echo ==========================================
echo Xong! Nhan phim bat ky de dong cua so.
echo ==========================================
pause >nul
