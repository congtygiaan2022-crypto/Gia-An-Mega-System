import sys
import os
import time
import json

# Add project root and plugins/lib to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "plugins", "lib"))

from gams_utils import BrowserManager

def run_test():
    portable_path = os.getenv("CHROME_PORTABLE_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    if not os.path.exists(portable_path):
        paths = [
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ]
        for p in paths:
            if os.path.exists(p):
                portable_path = p
                break

    bm = BrowserManager(portable_path)
    
    # URL of 'Bạn không biết, Tôi cũng thế' (STT 2) which has the Lookback popup
    url = "https://business.facebook.com/latest/insights/overview/?business_id=1016985112612772&asset_id=929782626889574"
    print(f"Navigating to: {url}")
    
    try:
        bm.launch_browser()
        bm.driver.get(url)
        print("Waiting 10 seconds for initial load...")
        time.sleep(10)
        
        # Test dismiss popups
        print("Dismissing popups...")
        dismissed = bm.dismiss_popups()
        print(f"Popup dismissed: {dismissed}")
        
        # Take a screenshot to verify it is closed!
        screenshot_path = os.path.join(PROJECT_ROOT, "scratch", "popup_test_screenshot.png")
        bm.driver.save_screenshot(screenshot_path)
        print(f"Verification screenshot saved to: {screenshot_path}")
        
        # Extract data
        data = bm.extract_insight_data()
        print(f"Extracted Data: {data}")
        
        post_info = bm.extract_latest_post_date()
        print(f"Extracted Post Info: {post_info}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        bm.close_browser()

if __name__ == "__main__":
    run_test()
