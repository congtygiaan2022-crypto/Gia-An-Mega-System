@echo off
chcp 65001 >nul 2>&1
echo ===================================================
echo     GAMS AUTO-UPDATE CLIENT INSTALLER
echo ===================================================
echo.
echo [INFO] Running environment check...
where python >nul 2>&1
if %%errorlevel%% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python and try again.
    pause
    exit /b 1
)

echo [INFO] Starting automatic configuration script...
python "%%~dp0update_client.py"
pause
