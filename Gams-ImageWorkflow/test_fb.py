import time
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import profile_manager
import os

def test_facebook():
    pm = profile_manager.ProfileManager("profiles")
    with sync_playwright() as p:
        context = pm.launch_browser_for_profile(p, "Yui Hatano", headless=False)
        page = context.new_page()
        page.goto("https://business.facebook.com/latest/composer/?asset_id=439411339247687&business_id=1016985112612772", wait_until="domcontentloaded")
        
        print("Đợi FB load 10 giây...")
        time.sleep(10)
        
        # In ra các thẻ div hoặc span chứa chữ "Thêm"
        elements = page.locator('div, span, i').all()
        found = False
        for el in elements:
            try:
                text = el.inner_text().strip()
                if "Thêm ảnh" in text or "Add photo" in text:
                    print("TÌM THẤY:", text, el.evaluate("node => node.className"))
                    found = True
            except:
                pass
        
        if not found:
            print("Không tìm thấy chữ 'Thêm ảnh'. In ra nội dung toàn trang:")
            print(page.locator("body").inner_text()[:1000])

        context.close()

if __name__ == "__main__":
    test_facebook()
