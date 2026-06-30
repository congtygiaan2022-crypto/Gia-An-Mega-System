import time
import sys
import os
import profile_manager
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def test_chatgpt_modal():
    pm = profile_manager.ProfileManager("profiles")
    with sync_playwright() as p:
        context = pm.launch_browser_for_profile(p, "Yui Hatano", headless=False)
        page = context.new_page()

        url = "https://chatgpt.com/c/6a12d2cd-bf7c-83ec-b4b8-8ce17202eacb"
        print(f"Đang truy cập {url}...")
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(8)
        
        try:
            # Tìm ảnh do ChatGPT tạo
            img_elements = page.locator('img[alt*="Generated"], img[alt*="generated"]').all()
            if img_elements:
                print(f"Tìm thấy {len(img_elements)} ảnh generated. Click vào ảnh cuối cùng...")
                img_elements[-1].click()
                time.sleep(3) # Đợi modal mở
                
                print("Đang thử bấm nút Download HQ...")
                
                os.makedirs("output_data", exist_ok=True)
                output_image_path = os.path.join("output_data", "test_hq_download.png")
                
                with page.expect_download(timeout=15000) as download_info:
                    dl_btn = page.locator('button[aria-label="Download"], button[aria-label="Tải xuống"], button[aria-label="Save"], button[aria-label="Lưu"], a[download], button[aria-label="Save image"]').first
                    dl_btn.click()
                    
                download = download_info.value
                download.save_as(output_image_path)
                print(f"ĐÃ TẢI THÀNH CÔNG ẢNH VÀ LƯU TẠI: {output_image_path}")
                
            else:
                print("KHÔNG TÌM THẤY ẢNH GENERATED NÀO!")
        except Exception as e:
            print("Lỗi:", e)
        
        context.close()

if __name__ == "__main__":
    test_chatgpt_modal()
