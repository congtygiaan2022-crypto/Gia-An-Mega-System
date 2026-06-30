import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.browser import BrowserController

def dump_google():
    browser = BrowserController(headless=True)
    if not browser.start():
        print("Failed to start browser")
        return
        
    try:
        driver = browser.driver
        url = "https://www.google.com/search?q=Man+City+vs+Real+Madrid+score"
        print(f"Navigating to: {url}")
        driver.get(url)
        time.sleep(5)
        
        html = driver.page_source
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "google_search.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Page source dumped to {file_path} (length: {len(html)} chars)")
        
        # Take a screenshot
        screenshot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "google_search.png")
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        browser.stop()

if __name__ == "__main__":
    dump_google()
