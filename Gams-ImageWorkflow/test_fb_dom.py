import time
import sys
import os
import profile_manager
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def test_fb():
    pm = profile_manager.ProfileManager("profiles")
    with sync_playwright() as p:
        context = pm.launch_browser_for_profile(p, "Yui Hatano", headless=False)
        page = context.new_page()

        print("Đang truy cập Facebook Fanpage...")
        page.goto("https://business.facebook.com/latest/composer/?asset_id=439411339247687&business_id=1016985112612772", wait_until="domcontentloaded")
        time.sleep(15)
        
        print("Đang lưu DOM...")
        with open("fb_dom.html", "w", encoding="utf-8") as f:
            f.write(page.evaluate("document.body.innerHTML"))
        print("Lưu xong vào fb_dom.html")
        
        context.close()

if __name__ == "__main__":
    test_fb()
