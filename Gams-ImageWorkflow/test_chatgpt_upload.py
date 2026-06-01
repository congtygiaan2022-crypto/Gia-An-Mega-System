import time
import sys
import os
import profile_manager
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def test_chatgpt_upload():
    pm = profile_manager.ProfileManager("profiles")
    with sync_playwright() as p:
        context = pm.launch_browser_for_profile(p, "Yui Hatano", headless=False)
        page = context.new_page()

        print("Đang truy cập ChatGPT...")
        page.goto("https://chatgpt.com/", wait_until="domcontentloaded")
        time.sleep(5)
        
        # Test Upload Menu
        print("Clicking Add files button...")
        try:
            page.locator('button[data-testid="composer-plus-btn"]').click()
            time.sleep(2)
            print("Đang lưu DOM của Menu...")
            with open("chatgpt_menu_dom.html", "w", encoding="utf-8") as f:
                f.write(page.evaluate("document.body.innerHTML"))
            print("Đã lưu menu DOM.")
        except Exception as e:
            print("Lỗi click menu:", e)
        
        context.close()

if __name__ == "__main__":
    test_chatgpt_upload()
