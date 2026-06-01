import time
import sys
import os
import profile_manager
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def test_chatgpt():
    pm = profile_manager.ProfileManager("profiles")
    with sync_playwright() as p:
        context = pm.launch_browser_for_profile(p, "Yui Hatano", headless=False)
        page = context.new_page()

        print("Đang truy cập ChatGPT...")
        page.goto("https://chatgpt.com/", wait_until="domcontentloaded")
        time.sleep(5)
        
        # Thử điền text
        try:
            page.locator('#prompt-textarea').fill("Vẽ một con mèo 3D")
            page.keyboard.press("Enter")
            print("Đã gửi prompt vẽ ảnh")
        except Exception as e:
            print("Lỗi:", e)
            
        print("Đang đợi render (15s)...")
        time.sleep(15)
        
        print("Đang lưu DOM...")
        with open("chatgpt_dom.html", "w", encoding="utf-8") as f:
            f.write(page.evaluate("document.body.innerHTML"))
        print("Lưu xong vào chatgpt_dom.html")
        
        context.close()

if __name__ == "__main__":
    test_chatgpt()
