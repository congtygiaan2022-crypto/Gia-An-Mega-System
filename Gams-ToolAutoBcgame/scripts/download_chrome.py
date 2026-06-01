import os
import requests
import zipfile
import io
import shutil
from loguru import logger

# Sử dụng "Chrome for Testing" - bản ổn định dành riêng cho automation
# Phiên bản 124.0.6367.91
CHROME_URL = "https://storage.googleapis.com/chrome-for-testing-public/124.0.6367.91/win64/chrome-win64.zip"
DEST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bin")
CHROME_DIR = os.path.join(DEST_DIR, "chrome")

def download_chrome():
    if os.path.exists(os.path.join(CHROME_DIR, "chrome.exe")):
        logger.info("✅ Chrome portable đã tồn tại.")
        return True

    logger.info("🌐 Đang tải Chrome for Testing (Bản ổn định v124) (khoảng 150MB)...")
    
    try:
        os.makedirs(DEST_DIR, exist_ok=True)
        
        response = requests.get(CHROME_URL, stream=True)
        response.raise_for_status()
        
        zip_data = io.BytesIO()
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                zip_data.write(chunk)

        logger.info("📦 Đang giải nén...")
        with zipfile.ZipFile(zip_data) as zip_ref:
            zip_ref.extractall(DEST_DIR)
            
        extracted_path = os.path.join(DEST_DIR, "chrome-win64")
        if os.path.exists(extracted_path):
            if os.path.exists(CHROME_DIR):
                shutil.rmtree(CHROME_DIR)
            os.rename(extracted_path, CHROME_DIR)
            
        logger.info("✅ Tải và cài đặt Chrome portable thành công!")
        return True

    except Exception as e:
        logger.error(f"❌ Lỗi khi tải Chrome: {e}")
        return False

if __name__ == "__main__":
    download_chrome()
