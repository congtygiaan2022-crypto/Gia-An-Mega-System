import time
import sys
import profile_manager
import os
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def test_2_images():
    profile_name = "Yui Hatano"
    pm = profile_manager.ProfileManager("profiles")
    with sync_playwright() as p:
        context = pm.launch_browser_for_profile(p, profile_name, headless=False)
        page = context.new_page()

        url = "https://chatgpt.com/c/6a135be0-9fe4-83ec-be9f-a67517b1cc09"
        print(f"Đang truy cập {url}...")
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(10)
        
        try:
            print("Đang tìm ảnh...")
            img_elements = page.locator('img[alt*="Generated"], img[alt*="generated"]').all()
            if img_elements:
                print(f"Tìm thấy {len(img_elements)} ảnh generated.")
                print("Đang click vào ảnh cuối cùng...")
                img_elements[-1].click()
                time.sleep(3)
                
                print("Đang chờ nút tải xuống...")
                # Lấy y hệt locator trong ai_generator.py
                download_btn = page.locator('button[aria-label*="Download"], button[title*="Download"], button[aria-label*="Save"], button[title*="Save"], button[aria-label*="Lưu"], div[role="button"]:has-text("Download"), a[download]').first
                
                if download_btn.count() > 0:
                    print("Tìm thấy nút Save, đang click để mở menu...")
                    download_btn.click()
                    time.sleep(1)
                    
                    print("Đang tìm nút Download trong menu...")
                    # In ra DOM để xem popup chứa gì
                    with open("chatgpt_menu_dom.html", "w", encoding="utf-8") as f:
                        f.write(page.evaluate("document.body.innerHTML"))
                        
                    real_download_btn = page.locator('div[role="menuitem"]:has-text("Download"), div[role="menuitem"]:has-text("Save image"), div[role="menuitem"]:has-text("Lưu ảnh"), a[download]').first
                    if real_download_btn.count() > 0:
                        print("Tìm thấy nút tải thực sự, click...")
                        try:
                            with page.expect_download(timeout=10000) as download_info:
                                real_download_btn.click()
                            download = download_info.value
                            download_path = os.path.join(os.getcwd(), f"test_2_img_{download.suggested_filename}")
                            download.save_as(download_path)
                            print(f"Đã tải ảnh thành công: {download_path}")
                        except Exception as e:
                            print("Lỗi khi click download thực sự:", e)
                    else:
                        print("Không tìm thấy nút download bên trong menu!")
                else:
                    print("Không tìm thấy nút tải xuống! Đang lưu DOM modal...")
                    with open("chatgpt_modal_dom_2_images.html", "w", encoding="utf-8") as f:
                        f.write(page.evaluate("document.body.innerHTML"))
            else:
                print("Không tìm thấy thẻ img nào có alt='Generated'.")
                
        except Exception as e:
            print("Lỗi:", e)
        
        context.close()

if __name__ == "__main__":
    test_2_images()
