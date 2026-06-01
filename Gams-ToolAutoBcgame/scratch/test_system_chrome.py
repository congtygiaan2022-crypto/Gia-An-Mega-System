import undetected_chromedriver as uc
import os
import sys
import time
import traceback

# Cấu hình UTF-8 cho console Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def test_without_version_main():
    print("Starting uc.Chrome with version_main=None...")
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    profile_dir = os.path.join(os.getcwd(), "data", "chrome_profile_test_system1")
    os.makedirs(profile_dir, exist_ok=True)
    try:
        driver = uc.Chrome(
            options=options,
            user_data_dir=profile_dir,
            use_subprocess=False,
            suppress_welcome=True
        )
        print("SUCCESS: Started Chrome without version_main!")
        print(f"Current URL: {driver.current_url}")
        driver.quit()
    except Exception as e:
        print(f"FAILED without version_main: {e}")
        traceback.print_exc()

def test_with_version_main(chrome_version):
    print(f"\nStarting uc.Chrome with version_main={chrome_version}...")
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    profile_dir = os.path.join(os.getcwd(), "data", "chrome_profile_test_system2")
    os.makedirs(profile_dir, exist_ok=True)
    try:
        driver = uc.Chrome(
            options=options,
            version_main=chrome_version,
            user_data_dir=profile_dir,
            use_subprocess=False,
            suppress_welcome=True
        )
        print("SUCCESS: Started Chrome with version_main!")
        print(f"Current URL: {driver.current_url}")
        driver.quit()
    except Exception as e:
        print(f"FAILED with version_main: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("--- START SYSTEM CHROME TEST ---")
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
        version, _ = winreg.QueryValueEx(key, "version")
        chrome_version = int(version.split('.')[0])
        print(f"Detected Chrome version from registry: {chrome_version}")
    except Exception as e:
        print(f"Failed to detect Chrome version: {e}")
        chrome_version = None

    test_without_version_main()
    if chrome_version:
        test_with_version_main(chrome_version)
    print("--- END TEST ---")
