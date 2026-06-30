import time
import sys
import os
from playwright.sync_api import sync_playwright
import profile_manager

sys.stdout.reconfigure(encoding='utf-8')

def test_fb_upload():
    profile_name = "Yui Hatano"
    url = "https://business.facebook.com/latest/composer/?asset_id=439411339247687&business_id=1016985112612772"
    pm = profile_manager.ProfileManager("profiles")
    
    with sync_playwright() as p:
        print(f"Khởi động trình duyệt profile {profile_name}...")
        context = pm.launch_browser_for_profile(p, profile_name, headless=False)
        page = context.new_page()
        
        print("Đang truy cập FB Meta Business Suite...")
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(10)
        
        # Thử tìm input type=file ẩn trước
        inputs = page.locator('input[type="file"]').count()
        print(f"Số lượng input[type=file] ban đầu: {inputs}")
        
        # Cách 1: Click nút Thêm ảnh
        add_photo_locators = [
            'div[aria-label*="photo"]', 'div[aria-label*="Photo"]', 'div[aria-label*="ảnh"]', 'div[aria-label*="Ảnh"]', 
            'span:has-text("Add photo")', 'span:has-text("Thêm ảnh")', 
            'div:has-text("Photo/video")', 'div:has-text("Ảnh/video")'
        ]
        
        add_photo_btn = None
        for loc in add_photo_locators:
            if page.locator(loc).count() > 0:
                # Find the most deeply nested one
                add_photo_btn = page.locator(loc).last
                print(f"Tìm thấy nút upload bằng locator: {loc}")
                break
                
        if not add_photo_btn:
            # Fallback for exact text
            add_photo_btn = page.locator("text='Thêm ảnh'").first
            print("Tìm nút qua text='Thêm ảnh'")
            
        if add_photo_btn:
            print("Đang click nút Thêm ảnh...")
            add_photo_btn.click(timeout=5000)
            time.sleep(2)
            
            # Dump DOM sau khi click
            with open("fb_upload_dom_after_click2.html", "w", encoding="utf-8") as f:
                f.write(page.evaluate("document.body.innerHTML"))
            print("Đã lưu fb_upload_dom_after_click2.html")
            
            inputs = page.locator('input[type="file"]').count()
            print(f"Số lượng input[type=file] sau khi click: {inputs}")
            
            # Tìm menu item
            menu_item = page.locator('div:has-text("Tải lên từ máy tính"), div:has-text("Upload from desktop"), span:has-text("Tải lên từ máy tính"), span:has-text("Upload from desktop")').last
            if menu_item.count() > 0:
                print("Tìm thấy menu item 'Tải lên từ máy tính'. Đang click...")
                try:
                    with page.expect_file_chooser(timeout=5000) as fc_info:
                        menu_item.click()
                    print("Mở File Chooser THÀNH CÔNG qua menu item!")
                    # Đóng trình duyệt
                except Exception as e:
                    print("Lỗi khi mở File Chooser qua menu:", e)
            else:
                print("Không tìm thấy menu item 'Tải lên từ máy tính'!")
                
        context.close()

if __name__ == "__main__":
    test_fb_upload()
