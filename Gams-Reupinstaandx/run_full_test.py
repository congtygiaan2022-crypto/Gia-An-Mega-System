import time
import sys
import os
import re
from playwright.sync_api import sync_playwright
import profile_manager
from social_poster import SocialPoster

sys.stdout.reconfigure(encoding='utf-8')

def test_full_loop():
    profile_name = "Yui Hatano"
    url = "https://chatgpt.com/c/6a14a26e-a5e4-83ec-9b44-52c0ca57acd5"
    pm = profile_manager.ProfileManager("profiles")
    
    with sync_playwright() as p:
        print(f"[{profile_name}] Khởi động trình duyệt để lấy nội dung từ link cũ...")
        context = pm.launch_browser_for_profile(p, profile_name, headless=False)
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(10)
        
        # 1. TRÍCH XUẤT ẢNH (Có fix dropdown menu)
        print(f"[{profile_name}] Đang trích xuất ảnh...")
        img_elements = page.locator('img[alt*="Generated"], img[alt*="generated"]').all()
        if not img_elements:
            print("Không tìm thấy ảnh!")
            context.close()
            return
            
        img_elements[-1].click()
        time.sleep(3)
        
        download_btn = page.locator('button[aria-label*="Download"], button[title*="Download"], button[aria-label*="Save"], button[title*="Save"], button[aria-label*="Lưu"], div[role="button"]:has-text("Download"), a[download]').first
        
        if download_btn.count() > 0:
            is_menu = download_btn.get_attribute("aria-haspopup") == "menu"
            try:
                if is_menu:
                    download_btn.click()
                    time.sleep(1)
                    real_dl_btn = page.locator('div[role="menuitem"]:has-text("Download"), div[role="menuitem"]:has-text("Save"), div[role="menuitem"]:has-text("Lưu"), a[download]').first
                    with page.expect_download(timeout=10000) as download_info:
                        real_dl_btn.click()
                else:
                    with page.expect_download(timeout=10000) as download_info:
                        download_btn.click()
                        
                download = download_info.value
                raw_image_path = os.path.join(os.getcwd(), f"temp_test_img.png")
                download.save_as(raw_image_path)
                print(f"[{profile_name}] Đã tải ảnh HQ thành công.")
                
                page.keyboard.press("Escape")
                time.sleep(1)
                
            except Exception as e:
                print(f"[{profile_name}] Lỗi tải ảnh: {e}")
                context.close()
                return
        
        # 2. TRÍCH XUẤT TEXT (Có fix strict mode)
        print(f"[{profile_name}] Đang trích xuất text...")
        elements = page.locator('[data-message-author-role="assistant"]').all()
        if not elements:
            print("Không tìm thấy text!")
            context.close()
            return
            
        markdown_locator = elements[-1].locator('.markdown')
        if markdown_locator.count() > 0:
            raw_text = markdown_locator.first.inner_text()
        else:
            raw_text = elements[-1].inner_text()
            
        clean_text = re.sub(r'^(Edit|Copy|Like|Dislike)[\r\n]+', '', raw_text.strip(), flags=re.IGNORECASE)
        generated_text = clean_text.strip()
        print(f"[{profile_name}] Đã lấy được text sạch:\n{generated_text}\n")
        
        context.close()
        
    # Lưu ra file và chuẩn bị đăng
    print(f"[{profile_name}] Xử lý lưu text...")
    
    txt_path = os.path.join(os.getcwd(), f"temp_test_text.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(generated_text)
        
    # 3. ĐĂNG LÊN FACEBOOK
    print(f"[{profile_name}] Bắt đầu quy trình đăng lên Fanpage...")
    
    pm = profile_manager.ProfileManager("profiles")
    with sync_playwright() as p:
        context = pm.launch_browser_for_profile(p, profile_name, headless=False)
        poster = SocialPoster(context, "https://business.facebook.com/latest/composer/?asset_id=439411339247687&business_id=1016985112612772")
        try:
            poster.post_to_fanpage(profile_name, txt_path, raw_image_path)
            print(f"[{profile_name}] Đã đăng thành công lên Facebook!")
        except Exception as e:
            print(f"[{profile_name}] Lỗi khi đăng Facebook: {e}")
        finally:
            context.close()

if __name__ == "__main__":
    test_full_loop()
