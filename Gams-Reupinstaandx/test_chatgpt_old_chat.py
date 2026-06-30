import time
import sys
import profile_manager
import os
import shutil
import glob
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def test_old_chat():
    profile_name = "Yui Hatano"
    pm = profile_manager.ProfileManager("profiles")
    with sync_playwright() as p:
        context = pm.launch_browser_for_profile(p, profile_name, headless=False)
        page = context.new_page()

        url = "https://chatgpt.com/c/6a13582d-c114-83ec-a635-537b0bc9efbe"
        print(f"Đang truy cập {url}...")
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(10)
        
        try:
            # 1. Lấy ảnh cuối cùng
            print("Đang tìm ảnh...")
            img_elements = page.locator('img[alt*="Generated"], img[alt*="generated"]').all()
            if img_elements:
                print(f"Tìm thấy {len(img_elements)} ảnh generated. Click vào ảnh cuối cùng...")
                img_elements[-1].click()
                time.sleep(3)
                
                print("Đang chờ nút tải xuống...")
                
                # Dump DOM modal
                with open("chatgpt_modal_dom_old_chat.html", "w", encoding="utf-8") as f:
                    f.write(page.evaluate("document.body.innerHTML"))
                    
                download_btn = page.locator('button[aria-label*="Download"], button[title*="Download"], div[role="button"]:has-text("Download"), a[download]').first
                if download_btn.count() > 0:
                    try:
                        with page.expect_download(timeout=10000) as download_info:
                            download_btn.click()
                        download = download_info.value
                        
                        download_path = os.path.join(os.getcwd(), download.suggested_filename)
                        download.save_as(download_path)
                        print(f"Đã tải ảnh thành công: {download_path}")
                    except Exception as e:
                        print("Lỗi click download:", e)
                else:
                    print("Không tìm thấy nút tải xuống!")
            else:
                print("Không tìm thấy thẻ img nào có alt='Generated'.")
                
            # 2. Lấy text
            print("Đang lấy text...")
            # Click ra ngoài để tắt modal (nếu có)
            page.keyboard.press("Escape")
            time.sleep(1)
            
            elements = page.locator('[data-message-author-role="assistant"]').all()
            if elements:
                # Dùng thuật toán mới nhất
                markdown_locator = elements[-1].locator('.markdown')
                if markdown_locator.count() > 0:
                    raw_text = markdown_locator.first.inner_text()
                else:
                    raw_text = elements[-1].inner_text()
                
                import re
                clean_text = re.sub(r'^(Edit|Copy|Like|Dislike)[\r\n]+', '', raw_text.strip(), flags=re.IGNORECASE)
                print("==== TEXT SAU KHI LỌC ====")
                print(repr(clean_text))
                print("==========================")
            else:
                print("Không tìm thấy tin nhắn assistant nào!")
                
        except Exception as e:
            print("Lỗi:", e)
        
        context.close()

if __name__ == "__main__":
    test_old_chat()
