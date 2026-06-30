@echo off
echo Dang dung dac nhiem Tool Auto Content (chi tat dung tool nay)...

if exist app.pid (
    set /p PID=<app.pid
    echo Da tim thay PID cua phan mem: %PID%
    taskkill /PID %PID% /T /F >NUL 2>&1
    del app.pid
    echo Da tat an toan cac tien trinh thuoc ve tool nay.
) else (
    echo Khong tim thay file app.pid. Se thu tim bang ten cua so...
    taskkill /FI "WINDOWtitle Gams Image Workflow v1.0.0
    echo Da don dep dua tren ten cua so.
)

pause
