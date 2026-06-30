import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
import time
import psutil
import os
import json
from playwright.sync_api import sync_playwright

def cleanup_chrome(profile_name):
    abs_profile_dir = os.path.abspath(os.path.join("profiles", profile_name)).lower()
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline:
                    cmd_str = " ".join(cmdline).lower()
                    if abs_profile_dir in cmd_str:
                        proc.kill()
        except:
            pass

def main(profile_name):
    cleanup_chrome(profile_name)
    print(f"[{profile_name}] Đang mở trình duyệt ở chế độ thủ công...")
    print("Bạn có thể tiến hành đăng nhập Facebook hoặc các tài khoản khác.")
    print("Trình duyệt này sẽ tự động lưu lại toàn bộ phiên đăng nhập của bạn.")
    print("\n[!] HÃY ĐÓNG CỬA SỔ TRÌNH DUYỆT NÀY KHI BẠN ĐÃ ĐĂNG NHẬP XONG!")
    
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        
    user_data_dir = os.path.join(os.getcwd(), config.get("profiles_dir", "profiles"), profile_name)
    
    try:
        import profile_manager
        with sync_playwright() as p:
            pm = profile_manager.ProfileManager(config.get("profiles_dir", "profiles"))
            context = pm.launch_browser_for_profile(p, profile_name, headless=False)
            
            page = context.pages[0] if context.pages else context.new_page()
            
            # Điều hướng tự động tới Facebook để người dùng đăng nhập
            page.goto("https://facebook.com")
            
            # Chờ cho đến khi context bị đóng (người dùng bấm dấu X)
            page.wait_for_event("close", timeout=0)
    except Exception as e:
        print(f"\n[Lỗi] Không thể mở trình duyệt: {e}")
        import time
        time.sleep(5)

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            main(sys.argv[1])
        else:
            print("Missing profile name")
    except Exception as e:
        import traceback
        print("\n" + "="*50)
        print("CÓ LỖI NGHIÊM TRỌNG (CRASH) TRONG QUÁ TRÌNH CHẠY:")
        print(traceback.format_exc())
        print("="*50)
        print("\n[!] HÃY COPY TOÀN BỘ ĐOẠN LỖI TRÊN GỬI CHO ANTIGRAVITY ĐỂ FIX!")
        os.system("pause")
