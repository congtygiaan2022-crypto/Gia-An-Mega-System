import time
import sys
import profile_manager
import os
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def test_text():
    profile_name = "Yui Hatano"
    pm = profile_manager.ProfileManager("profiles")
    with sync_playwright() as p:
        context = pm.launch_browser_for_profile(p, profile_name, headless=False)
        page = context.new_page()

        url = "https://chatgpt.com/c/6a14a26e-a5e4-83ec-9b44-52c0ca57acd5"
        print(f"Đang truy cập {url}...")
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(10)
        
        try:
            print("Đang lấy text...")
            elements = page.locator('[data-message-author-role="assistant"]').all()
            if elements:
                markdown_locator = elements[-1].locator('.markdown')
                
                try:
                    # Lỗi strict mode ở đây nếu count > 1
                    raw_text_fail = markdown_locator.evaluate("el => el.innerText")
                    print("evaluate thành công:", repr(raw_text_fail))
                except Exception as e:
                    print("Lỗi evaluate:", e)
                    
                # Cách đúng
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
    test_text()
