import undetected_chromedriver as uc
import os
import sys
import time
import traceback
import glob

# Cấu hình UTF-8 cho console Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def test_profile(profile_name):
    print(f"\n--- Testing profile: {profile_name} ---")
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    profile_dir = os.path.join(current_dir, "data", profile_name)
    print(f"Profile directory: {profile_dir}")
    
    # Clean locks
    try:
        for lock_file in glob.glob(os.path.join(profile_dir, "**/LOCK"), recursive=True):
            try:
                os.remove(lock_file)
                print(f"  Removed lock file: {lock_file}")
            except Exception as e:
                print(f"  Could not remove lock file {lock_file}: {e}")
    except Exception as e:
        print(f"  Error globbing locks: {e}")

    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1366,768")
    options.add_argument("--lang=vi-VN")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-crash-reporter")
    options.add_argument("--disable-breakpad")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-features=RendererCodeIntegrity")

    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
        version, _ = winreg.QueryValueEx(key, "version")
        chrome_version = int(version.split('.')[0])
    except Exception as e:
        chrome_version = None

    try:
        driver = uc.Chrome(
            options=options,
            version_main=chrome_version,
            user_data_dir=profile_dir,
            use_subprocess=False,
            suppress_welcome=True
        )
        print(f"  SUCCESS! Started Chrome with profile: {profile_name}")
        driver.quit()
        return True
    except Exception as e:
        print(f"  FAILED: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_profile("chrome_profile_test_clean")
    test_profile("chrome_profile_v2")
