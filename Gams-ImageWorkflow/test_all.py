import time
import sys
import os
import profile_manager
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def test_pipeline():
    pm = profile_manager.ProfileManager("profiles")
    dummy_img = os.path.abspath("dummy.png")
    # Create dummy image
    from PIL import Image
    Image.new('RGB', (100, 100), color='red').save(dummy_img)
    
    with sync_playwright() as p:
        context = pm.launch_browser_for_profile(p, "Yui Hatano", headless=False)
        page = context.new_page()

        # 1. Test Google AI Studio
        print("--- Đang test Google AI Studio ---")
        page.goto("https://aistudio.google.com/prompts/new_chat", wait_until="domcontentloaded")
        time.sleep(5)
        
        try:
            # Upload image
            with page.expect_file_chooser(timeout=5000) as fc_info:
                page.locator('button[aria-label="Insert images, videos, audio, or files"]').click()
            fc_info.value.set_files(dummy_img)
            print("Đã upload ảnh lên Google AI Studio.")
            time.sleep(2)
        except Exception as e:
            print("Lỗi upload ảnh Google AI:", e)
            
        try:
            page.locator('textarea[aria-label="Enter a prompt"]').fill("Xin chào, đây là test.")
            page.keyboard.press("Control+Enter")
            print("Đã gửi prompt Google AI.")
            time.sleep(10)
            
            # Extract text
            res = page.locator('.model-response-text').last.inner_text()
            print("Kết quả text Google AI:", res)
            
            # Extract image (nếu có)
            imgs = page.locator('.model-response-text').last.locator('img').all()
            if imgs:
                print("Tìm thấy thẻ img trong Google AI:", imgs[0].get_attribute('src'))
            else:
                print("Không tìm thấy thẻ img trong Google AI.")
        except Exception as e:
            print("Lỗi tương tác Google AI:", e)

        # 2. Test ChatGPT
        print("--- Đang test ChatGPT ---")
        page.goto("https://chatgpt.com/", wait_until="domcontentloaded")
        time.sleep(5)
        
        try:
            page.locator('input[type="file"]').first.set_input_files(dummy_img)
            print("Đã upload ảnh lên ChatGPT.")
            time.sleep(2)
            page.locator('#prompt-textarea').fill("Test sinh ảnh.")
            page.keyboard.press("Enter")
            print("Đã gửi prompt ChatGPT.")
            time.sleep(15)
            
            # Extract text
            res = page.locator('div[data-message-author-role="assistant"]').last.inner_text()
            print("Kết quả text ChatGPT:", res)
            
            # Extract image
            imgs = page.locator('div[data-message-author-role="assistant"]').last.locator('img[alt*="Generated"]').all()
            if imgs:
                print("Tìm thấy thẻ img DALL-E:", imgs[-1].get_attribute('src'))
            else:
                print("Không tìm thấy thẻ img DALL-E trong ChatGPT.")
        except Exception as e:
            print("Lỗi tương tác ChatGPT:", e)

        # 3. Test Facebook Business Suite
        print("--- Đang test Facebook Fanpage ---")
        page.goto("https://business.facebook.com/latest/composer/?asset_id=439411339247687&business_id=1016985112612772", wait_until="domcontentloaded")
        time.sleep(8)
        
        try:
            # Upload image using multiple strategies
            uploaded = False
            file_inputs = page.locator('input[type="file"][accept*="image"]').all()
            for fi in file_inputs:
                try:
                    fi.set_input_files(dummy_img, timeout=2000)
                    print("Đã set file vào thẻ input trực tiếp.")
                    uploaded = True
                    break
                except:
                    pass
            
            if not uploaded:
                print("Đang thử dùng file chooser...")
                with page.expect_file_chooser(timeout=5000) as fc_info:
                    page.get_by_text("Thêm ảnh", exact=True).first.click()
                fc_info.value.set_files(dummy_img)
                print("Đã upload ảnh qua file chooser.")
        except Exception as e:
            print("Lỗi upload ảnh Facebook:", e)
            
        time.sleep(3)
        
        try:
            textbox = page.locator('div[aria-label="Hãy viết vào ô hộp thoại để thêm văn bản vào bài viết."]')
            textbox.click()
            textbox.press_sequentially("Test đăng bài auto.\nXin chào!", delay=50)
            print("Đã gõ văn bản từng chữ.")
        except Exception as e:
            print("Lỗi điền text Facebook:", e)
            
        time.sleep(3)
        
        try:
            btn = page.get_by_role("button", name="Đăng", exact=True)
            print("Nút Đăng có đang bật (enabled) không?", btn.is_enabled())
            if btn.is_enabled():
                btn.click()
                print("Đã bấm nút Đăng.")
        except Exception as e:
            print("Lỗi bấm nút Đăng Facebook:", e)

        time.sleep(3)
        context.close()

if __name__ == "__main__":
    test_pipeline()
