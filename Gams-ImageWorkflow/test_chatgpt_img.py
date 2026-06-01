import time
import sys
import os
import profile_manager
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def test_chatgpt_img():
    pm = profile_manager.ProfileManager("profiles")
    with sync_playwright() as p:
        context = pm.launch_browser_for_profile(p, "Yui Hatano", headless=False)
        page = context.new_page()

        print("Đang truy cập ChatGPT...")
        page.goto("https://chatgpt.com/", wait_until="domcontentloaded")
        time.sleep(5)
        
        try:
            page.locator('#prompt-textarea').fill("Vẽ một con chó con dễ thương")
            page.keyboard.press("Enter")
            print("Đã gửi prompt VẼ ẢNH...")
            
            # Wait for generation to stop
            print("Đang đợi ChatGPT phản hồi...")
            wait_start = time.time()
            while time.time() - wait_start < 60:
                is_generating = page.locator('button[data-testid="stop-button"]').count() > 0
                if not is_generating and (time.time() - wait_start > 5):
                    # Check if there is an image in the latest response
                    msgs = page.locator('div[data-message-author-role="assistant"]').all()
                    if msgs:
                        # Wait an extra few seconds for image to fully render in DOM
                        time.sleep(5)
                        break
                time.sleep(2)
                
            print("Đang lưu DOM của toàn bộ message...")
            with open("chatgpt_img_dom.html", "w", encoding="utf-8") as f:
                f.write(page.evaluate("document.body.innerHTML"))
            print("Lưu xong vào chatgpt_img_dom.html")

        except Exception as e:
            print("Lỗi:", e)
        
        context.close()

if __name__ == "__main__":
    test_chatgpt_img()
