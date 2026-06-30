# Gams-GALogin Portable Chromium Downloader Script
$ProgressPreference = 'SilentlyContinue'

$destDir = "E:\Gams-GALogin\bin\chromium"
$exePath = "$destDir\chrome-win\chrome.exe"
$zipPath = "E:\Gams-GALogin\chrome-win.zip"
# Chromium Win_x64 Revision 1251996 (Stable Snapshot)
$downloadUrl = "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Win_x64%2F1251996%2Fchrome-win.zip?alt=media"

# Check if Chromium already exists
if (Test-Path $exePath) {
    Write-Host "[INFO] Chromium da ton tai tai: $exePath"
    Write-Host "[INFO] Bo qua buoc tai xuong."
    Exit 0
}

# Create bin directory
if (-not (Test-Path $destDir)) {
    New-Item -ItemType Directory -Force -Path $destDir | Out-Null
    Write-Host "[INFO] Da tao thu muc: $destDir"
}

Write-Host "[1/3] Dang tai xuong portable Chromium tu Google Storage..."
Write-Host "URL: $downloadUrl"
Write-Host "Vui long cho doi trong giay lat..."

try {
    # Download using WebClient for speed and progress bypass
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($downloadUrl, $zipPath)
    Write-Host "[SUCCESS] Da tai xong tep ZIP ve: $zipPath"
}
catch {
    Write-Host "[ERROR] Khong the tai Chromium. Kiem tra lai ket noi mang."
    Write-Host $_.Exception.Message
    Exit 1
}

Write-Host "[2/3] Dang giai nen tap tin ZIP vao: $destDir ..."
try {
    Expand-Archive -Path $zipPath -DestinationPath $destDir -Force
    Write-Host "[SUCCESS] Da giai nen hoan tat!"
}
catch {
    Write-Host "[ERROR] Giai nen that bai. Tep ZIP co the bi loi."
    Write-Host $_.Exception.Message
    Exit 1
}

Write-Host "[3/3] Dang don dep tap tin tam..."
if (Test-Path $zipPath) {
    Remove-Item -Path $zipPath -Force
    Write-Host "[SUCCESS] Da xoa tep ZIP tam thoi."
}

if (Test-Path $exePath) {
    Write-Host "=========================================================="
    Write-Host "[HOAN THANH] Chromium portable da duoc cai dat tai:"
    Write-Host " -> $exePath"
    Write-Host "=========================================================="
} else {
    Write-Host "[ERROR] Khong tim thay file chrome.exe sau khi giai nen!"
}
