import time
import sys
import profile_manager
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def test_fb_upload():
    pm = profile_manager.ProfileManager("profiles")
    with sync_playwright() as p:
        context = pm.launch_browser_for_profile(p, "Yui Hatano", headless=False)
        page = context.new_page()

        # url from the log
        url = "https://business.facebook.com/latest/composer/?asset_id=439411339247687&business_id=1016985112612772&ir_qe_exposed=1&nav_ref=internal_nav&ref=biz_web_content_manager_published_posts&context_ref=POSTS"
        print("Đang truy cập FB Composer...")
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(10)
        
        try:
            print("Đang lưu DOM của FB...")
            with open("fb_upload_dom.html", "w", encoding="utf-8") as f:
                f.write(page.evaluate("document.body.innerHTML"))
            print("Đã lưu DOM vào fb_upload_dom.html.")
            
            # Thử click Thêm ảnh
            print("Đang thử click nút Thêm ảnh...")
            try:
                page.locator('div[role="button"]:has-text("Add Photo"), div[role="button"]:has-text("Thêm ảnh")').click(timeout=5000)
                time.sleep(3) # Wait for dropdown or whatever
                
                print("Đang lưu DOM sau khi click...")
                with open("fb_upload_dom_after_click.html", "w", encoding="utf-8") as f:
                    f.write(page.evaluate("document.body.innerHTML"))
                    
                # In ra các nút mới
                buttons = page.locator('div[role="menuitem"], div[role="button"], span:has-text("Tải")').all()
                for b in buttons:
                    text = b.inner_text().strip()
                    if "tải" in text.lower() or "upload" in text.lower() or "desktop" in text.lower() or "máy tính" in text.lower():
                        print(f"Tìm thấy nút (menu?): '{text}'")
            except Exception as click_err:
                print("Lỗi click:", click_err)
        except Exception as e:
            print("Lỗi:", e)
            
        context.close()

if __name__ == "__main__":
    test_fb_upload()
