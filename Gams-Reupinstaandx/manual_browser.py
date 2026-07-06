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
        from worker_process import check_and_login_instagram_playwright, check_and_login_threads_playwright
        
        with sync_playwright() as p:
            pm = profile_manager.ProfileManager(config.get("profiles_dir", "profiles"))
            context = pm.launch_browser_for_profile(p, profile_name, headless=False)
            
            page_fb = context.pages[0] if context.pages else context.new_page()
            print(f"[{profile_name}] Đang mở Tab Facebook...")
            page_fb.goto("https://www.facebook.com")
            
            # Tự động kiểm tra và đăng nhập Instagram và Threads trong background
            print(f"[{profile_name}] Đang kiểm tra tự động đăng nhập Instagram...")
            try:
                check_and_login_instagram_playwright(context, profile_name)
            except Exception as e:
                print(f"Lỗi đăng nhập tự động Instagram: {e}")
                
            print(f"[{profile_name}] Đang kiểm tra tự động đăng nhập Threads...")
            try:
                check_and_login_threads_playwright(context, profile_name)
            except Exception as e:
                print(f"Lỗi đăng nhập tự động Threads: {e}")
                
            # Mở thêm tab cho Instagram và Threads để người dùng dễ kiểm tra trực quan
            print(f"[{profile_name}] Đang mở các Tab trực quan cho Instagram và Threads...")
            page_ig = context.new_page()
            page_ig.goto("https://www.instagram.com")
            
            page_th = context.new_page()
            page_th.goto("https://www.threads.net")
            
            # Đưa tab Facebook lên trước và chờ người dùng tắt trình duyệt
            page_fb.bring_to_front()
            page_fb.wait_for_event("close", timeout=0)
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
