import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.browser import BrowserController

def main():
    print("Starting screenshot check...")
    browser = BrowserController(headless=True)
    if not browser.start():
        print("Failed to start browser")
        return

    try:
        url = "https://bcvn2.com/vi/sports/soccer-1"
        print(f"Navigating to {url}...")
        browser.navigate(url)
        print("Waiting 15 seconds for page to load...")
        time.sleep(15)
        
        # Take screenshot
        scratch_dir = os.path.dirname(os.path.abspath(__file__))
        screenshot_path = os.path.join(scratch_dir, "bcgame_screenshot.png")
        if browser.take_screenshot(screenshot_path):
            print(f"Screenshot saved to: {screenshot_path}")
        else:
            print("Failed to take screenshot")
            
        # Get page source summary
        source = browser.get_page_source()
        print(f"HTML source length: {len(source)}")
        if len(source) > 0:
            print("Snippet of HTML:")
            print(source[:1000])
            
            # Count elements with <a> containing /sports/soccer/
            import re
            links = re.findall(r'href=["\']/?[a-zA-Z0-9_/.\-]+["\']', source)
            soccer_links = [l for l in links if "sports/soccer" in l]
            print(f"Found {len(soccer_links)} soccer links in raw HTML source")

    finally:
        browser.stop()

if __name__ == "__main__":
    main()
