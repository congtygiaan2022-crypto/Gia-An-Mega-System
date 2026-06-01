@echo off
chcp 65001 >nul
title Shopee Backlink Tool

echo.
echo ====================================================
echo           SHOPEE BACKLINK TOOL  --  Hybrid Engine
echo ====================================================
echo.

echo [1/3] Đang dọn dẹp các tiến trình chạy ngầm cũ (nếu có)...
:: Tắt các tiến trình dashboard_app.py cũ
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -like '*dashboard_app.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1

:: Tắt các trình duyệt Chrome chạy ngầm sử dụng profile của tool
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'chrome.exe' -and $_.CommandLine -like '*shopee_profile*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1

:: Tắt chromedriver.exe chạy ngầm
taskkill /F /IM chromedriver.exe /T >nul 2>&1

echo.

:: Kiem tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [LOI] Khong tim thay Python! Vui long cai Python 3.9+ tu python.org
    pause
    exit /b 1
)

echo [2/3] Dang cai / cap nhat thu vien...
pip install -r requirements.txt -q --disable-pip-version-check
if errorlevel 1 (
    echo [LOI] Cai dat thu vien that bai!
    pause
    exit /b 1
)

echo [3/3] Dang khoi chay tool...
echo.
python dashboard_app.py

echo.
echo ==========================================
echo Xong! Nhan phim bat ky de dong cua so.
echo ==========================================
pause >nul
