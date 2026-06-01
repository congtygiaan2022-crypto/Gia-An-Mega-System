@echo off
chcp 65001 > nul
echo.
echo ==================================================
echo        CONG CU XOA DU LIEU TOOL (RESET)
echo ==================================================
echo.
echo CANH BAO: Hanh dong nay se xoa toan bo:
echo 1. Video da tai trong thu muc 'downloads'
echo 2. Lich su tai (lichsutai.txt)
echo 3. Hang doi cho tai (hangdoi.txt)
echo 4. File log (automation.log)
echo.
echo.
echo Dang xoa du lieu...

if exist downloads (
    rmdir /s /q downloads
    echo [OK] Da xoa thu muc downloads
)

if exist lichsutai.txt (
    del lichsutai.txt
    echo [OK] Da xoa lichsutai.txt
)

if exist hangdoi.txt (
    del hangdoi.txt
    echo [OK] Da xoa hangdoi.txt
)

if exist automation.log (
    del automation.log
    echo [OK] Da xoa automation.log
)

echo.
echo Hoan tat! Tool da tro ve trang thai moi.
exit
