import sys
import os
import time

# Ensure we can load from core or plugins
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugins", "lib"))
from gams_utils import BrowserManager

def inspect():
    # Load Chrome path
    portable_path = os.getenv("CHROME_PORTABLE_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    if not os.path.exists(portable_path):
        # Look for Chrome in other standard directories
        paths = [
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ]
        for p in paths:
            if os.path.exists(p):
                portable_path = p
                break
                
    print(f"Using Chrome path: {portable_path}")
    bm = BrowserManager(portable_path)
    
    # Target URL for "Đỡ phải hóng 24/7"
    url = "https://business.facebook.com/latest/insights/overview/?business_id=1016985112612772&asset_id=243738568828870"
    print(f"Navigating to: {url}")
    
    try:
        bm.launch_browser()
        bm.driver.get(url)
        print("Waiting for page load...")
        time.sleep(10)
        
        # Capture screenshot and text
        os.makedirs(os.path.join(os.getcwd(), "scratch"), exist_ok=True)
        screenshot_path = os.path.abspath(os.path.join(os.getcwd(), "scratch", "fb_screenshot.png"))
        bm.driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
        
        body_text = bm.driver.find_element("tag name", "body").text
        text_path = os.path.abspath(os.path.join(os.getcwd(), "scratch", "fb_body.txt"))
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(body_text)
        print(f"Body text saved to: {text_path}")
        
        print("Page Title:", bm.driver.title)
        print("First 500 chars of body text:")
        print(body_text[:500])
        
    except Exception as e:
        print(f"Error during inspection: {e}")
    finally:
        bm.close_browser()

if __name__ == "__main__":
    inspect()
