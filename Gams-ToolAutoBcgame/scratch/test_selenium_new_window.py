import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.browser import BrowserController

def test_tabs():
    browser = BrowserController(headless=True)
    if not browser.start():
        print("Failed to start browser")
        return
        
    try:
        driver = browser.driver
        print(f"Initial window handles: {driver.window_handles}")
        original_window = driver.current_window_handle
        print(f"Original window handle: {original_window}")
        
        # Test native new window
        print("Opening new tab natively...")
        driver.switch_to.new_window('tab')
        print(f"New window handles: {driver.window_handles}")
        
        driver.get("https://www.google.com")
        print(f"Current URL in new tab: {driver.current_url}")
        
        # Safe closing
        if len(driver.window_handles) > 1:
            print("Closing the new tab...")
            driver.close()
            
        print("Switching back to original window...")
        driver.switch_to.window(original_window)
        print(f"Window handles after close: {driver.window_handles}")
        
        driver.get("https://bongda.wap.vn")
        print(f"Current URL in original tab: {driver.current_url}")
        print("Success! No session crashed.")
        
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        browser.stop()

if __name__ == "__main__":
    test_tabs()
