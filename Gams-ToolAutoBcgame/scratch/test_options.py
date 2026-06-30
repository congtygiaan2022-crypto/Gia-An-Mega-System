import undetected_chromedriver as uc
import os
import time

print("--- TESTING DETAILED OPTIONS ---")
current_dir = os.getcwd()
portable_chrome = os.path.join(current_dir, "bin", "chrome", "chrome.exe")
profile_dir = os.path.join(current_dir, "data", "chrome_profile_test_v2")

options = uc.ChromeOptions()
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
    print("Initializing uc.Chrome...")
    driver = uc.Chrome(
        options=options,
        browser_executable_path=portable_chrome,
        version_main=124,
        user_data_dir=profile_dir,
        use_subprocess=True,
        suppress_welcome=True
    )
    print("SUCCESS!")
    time.sleep(2)
    driver.quit()
    print("Closed driver.")
except Exception as e:
    import traceback
    traceback.print_exc()

print("--- TEST END ---")
