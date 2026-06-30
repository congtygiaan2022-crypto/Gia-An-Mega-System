@echo off
:: Gams-GALogin Dashboard Launcher for Windows
title Gams-GALogin Dashboard Launcher
color 0B
cls

echo ==========================================================
echo               Gams-GALogin Dashboard Launcher
echo ==========================================================
echo.
echo [1/4] Dang khoi dong Local REST API Server (Cong 1010)...
start "Gams-GALogin API Server" cmd /c "node server.cjs"

echo [2/4] Dang khoi dong Vite React Frontend Server (Cong 5173)...
start "Gams-GALogin Frontend Server" cmd /c "npm run dev"

echo.
echo [3/4] Dang cho cac dich vu khoi tao (3 giay)...
timeout /t 3 /nobreak > nul

echo.
echo [4/4] Dang mo Gams-GALogin Dashboard tren trinh duyet mac dinh...
start http://localhost:5173

echo.
echo ==========================================================
echo [HOAN TAT] Tat ca cac dich vu da duoc khoi chay!
echo   - Local REST API Server:  http://localhost:1010
echo   - Frontend UI Dashboard: http://localhost:5173
echo.
echo Vui long giu cua so nay dang mo de duy tri cac dich vu.
echo Nhan phim bat ky de tat tat ca cac dich vu va thoat...
echo ==========================================================
pause > nul

:: Clean up background node server instances launched by this script
taskkill /fi "windowtitle eq Gams-GALogin API Server*" /f > nul 2>&1
taskkill /fi "windowtitle eq Gams-GALogin Frontend Server*" /f > nul 2>&1
