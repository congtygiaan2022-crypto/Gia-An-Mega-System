import undetected_chromedriver as uc
import os
import time

print("--- BẮT ĐẦU TEST CHROME ---")
current_dir = os.getcwd()
portable_chrome = os.path.join(current_dir, "bin", "chrome", "chrome.exe")
profile_dir = os.path.join(current_dir, "data", "chrome_profile_test")

print(f"Path Chrome: {portable_chrome}")
print(f"Path Profile: {profile_dir}")

options = uc.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=800,600")

try:
    print("Đang khởi tạo driver...")
    # Thử không dùng version_main và dùng use_subprocess
    driver = uc.Chrome(
        options=options,
        browser_executable_path=portable_chrome,
        version_main=124,
        user_data_dir=profile_dir,
        use_subprocess=True
    )
    print("Khởi tạo THÀNH CÔNG!")
    print(f"URL hiện tại: {driver.current_url}")
    time.sleep(2)
    driver.quit()
    print("Đã đóng driver.")
except Exception as e:
    print(f"LỖI RỒI: {str(e)}")
    import traceback
    traceback.print_exc()

print("--- KẾT THÚC TEST ---")
