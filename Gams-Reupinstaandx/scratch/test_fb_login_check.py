import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
import time
from playwright.sync_api import sync_playwright

# Import từ thư mục cha
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import profile_manager
import db_manager

# Tạo thư mục scratch nếu chưa có
os.makedirs("scratch", exist_ok=True)

def check_login_status(page, name):
    url = page.url
    print(f"[{name}] URL hiện tại: {url}")
    
    # Chụp ảnh màn hình để đối chiếu trực quan
    screenshot_path = f"scratch/screenshot_{name}_{int(time.time())}.png"
    try:
        page.screenshot(path=screenshot_path)
        print(f"[{name}] Đã lưu ảnh màn hình tại: {screenshot_path}")
    except Exception as e:
        print(f"[{name}] Không thể chụp ảnh màn hình: {e}")

    # Check các selector đã đăng nhập
    selectors = [
        "[data-pagelet='LeftRail']",
        "[aria-label='Your profile']",
        "[aria-label='Facebook'][role='navigation']",
        "a[href*='/me/']"
    ]
    
    logged_in = False
    for sel in selectors:
        try:
            if page.locator(sel).first.is_visible():
                print(f"[{name}] Tìm thấy selector đăng nhập: {sel}")
                logged_in = True
        except Exception:
            pass
            
    if "facebook.com" in url and "login" not in url and "checkpoint" not in url and "two_step" not in url and logged_in:
        print(f"[{name}] Kết luận: ĐÃ ĐĂNG NHẬP nick Facebook.")
        return True
    else:
        # Nếu đang ở Business Suite và URL chứa business.facebook.com/latest/home và không chứa login
        if "business.facebook.com" in url and "login" not in url and ("latest/home" in url or page.locator(".meta-business-suite").first.is_visible()):
            print(f"[{name}] Kết luận: ĐÃ ĐĂNG NHẬP nick Facebook (xác minh từ Business Suite).")
            return True
        print(f"[{name}] Kết luận: CHƯA ĐĂNG NHẬP nick Facebook.")
        return False

def main():
    # 1. Giả lập trên Chrome mới tinh
    print("\n=== BƯỚC 1: GIẢ LẬP TRÊN CHROME MỚI TINH ===")
    clean_profile = "fb_test_clean_profile"
    
    # Xóa profile cũ nếu có để đảm bảo mới tinh
    import shutil
    profiles_dir = "profiles"
    clean_path = os.path.join(profiles_dir, clean_profile)
    if os.path.exists(clean_path):
        try:
            shutil.rmtree(clean_path, ignore_errors=True)
        except Exception:
            pass
        
    with sync_playwright() as p:
        pm = profile_manager.ProfileManager(profiles_dir)
        try:
            context = pm.launch_browser_for_profile(p, clean_profile, headless=False)
            page = context.new_page()
            
            print("\n--- Truy cập facebook.com (Chrome mới) ---")
            page.goto("https://www.facebook.com/")
            page.wait_for_timeout(5000)
            check_login_status(page, "Chrome_Moi_Facebook")
            
            print("\n--- Truy cập business.facebook.com (Chrome mới) ---")
            page.goto("https://business.facebook.com/latest/home")
            page.wait_for_timeout(5000)
            check_login_status(page, "Chrome_Moi_Business")
            
            context.close()
        except Exception as e:
            print(f"Lỗi khởi chạy browser Chrome mới: {e}")

    # 2. Giả lập trên Chrome Profile chỉ định
    profile_to_test = sys.argv[1] if len(sys.argv) > 1 else None
    if profile_to_test:
        print(f"\n=== BƯỚC 2: GIẢ LẬP TRÊN CHROME PROFILE '{profile_to_test}' ===")
        with sync_playwright() as p:
            pm = profile_manager.ProfileManager(profiles_dir)
            try:
                context = pm.launch_browser_for_profile(p, profile_to_test, headless=False)
                page = context.new_page()
                
                print(f"\n--- Truy cập facebook.com (Profile {profile_to_test}) ---")
                page.goto("https://www.facebook.com/")
                page.wait_for_timeout(5000)
                is_logged = check_login_status(page, f"Profile_{profile_to_test}_Facebook")
                
                print(f"\n--- Truy cập business.facebook.com (Profile {profile_to_test}) ---")
                page.goto("https://business.facebook.com/latest/home")
                page.wait_for_timeout(5000)
                check_login_status(page, f"Profile_{profile_to_test}_Business")
                    
                context.close()
            except Exception as e:
                print(f"Lỗi khởi chạy browser profile '{profile_to_test}': {e}")
    else:
        print("\n=== BỎ QUA BƯỚC 2: Không cung cấp tên profile để test. Cách dùng: python scratch/test_fb_login_check.py <Profile_Name> ===")

if __name__ == "__main__":
    main()
