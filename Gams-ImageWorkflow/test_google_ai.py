import time
import sys
import os
import profile_manager
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def test_google_ai():
    pm = profile_manager.ProfileManager("profiles")
    dummy_img = os.path.abspath("dummy.png")
    
    # Tạo dummy image nếu chưa có
    if not os.path.exists(dummy_img):
        from PIL import Image
        Image.new('RGB', (100, 100), color='red').save(dummy_img)
    
    with sync_playwright() as p:
        context = pm.launch_browser_for_profile(p, "Yui Hatano", headless=True)
        page = context.new_page()

        print("Đang truy cập Google AI Studio...")
        page.goto("https://aistudio.google.com/prompts/new_chat", wait_until="domcontentloaded")
        time.sleep(10)
        
        try:
            print("Đang upload ảnh...")
            with page.expect_file_chooser(timeout=5000) as fc_info:
                page.locator('button[aria-label="Insert images or files"]').click()
            fc_info.value.set_files(dummy_img)
            time.sleep(3)
            print("Upload xong.")
        except Exception as e:
            print("Lỗi upload:", e)
            
        try:
            print("Đang gửi prompt...")
            page.locator('textarea[aria-label="Enter a prompt"]').fill("Tạo 1 bức ảnh con mèo và viết 1 câu mô tả nó.")
            page.keyboard.press("Control+Enter")
            print("Gửi xong, đang chờ 30s...")
        except Exception as e:
            print("Lỗi gửi prompt:", e)
            
        time.sleep(30)
        
        print("Đang lưu DOM...")
        with open("google_ai_dom.html", "w", encoding="utf-8") as f:
            f.write(page.evaluate("document.body.innerHTML"))
        print("Lưu xong vào google_ai_dom.html")
        
        context.close()

if __name__ == "__main__":
    test_google_ai()
