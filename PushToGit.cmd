@echo off
chcp 65001 >nul 2>&1
echo ===================================================
echo     GAMS GIT PUSH HELPER (E DRIVE ROOT)
echo ===================================================
echo.
echo Checking Git status...
git init 2>nul
git branch -M main 2>nul
git remote add origin https://github.com/congtygiaan2022-crypto/Gia-An-Mega-System.git 2>nul
git config user.email "developer@giaan.vn" 2>nul
git config user.name "congtygiaan2022-crypto" 2>nul
git rm -r --cached . >nul 2>&1
git add .
git commit -m "Update source code" 2>nul
echo.
echo ===================================================
echo PUSHING TO GITHUB...
echo ===================================================
git push -u origin main -f
pause
