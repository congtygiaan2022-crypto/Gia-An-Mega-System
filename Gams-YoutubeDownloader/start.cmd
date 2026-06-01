@echo off
cd /d "%~dp0"
pm2 start main.py --name "Gams-YoutubeDownloader" --interpreter python
pause
