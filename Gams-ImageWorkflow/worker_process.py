import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import os
import time
import random
import psutil
import traceback
from datetime import datetime
from playwright.sync_api import sync_playwright
import db_manager
import importlib
import core.bug_tracker as bug_tracker

# Tải cấu hình động
import json

def load_global_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

config = load_global_config()

def cleanup_chrome(profile_name):
    # Tìm và diệt các process chrome.exe đang mở thư mục profile này
    profiles_dir = config.get("profiles_dir", "profiles")
    abs_profile_dir = os.path.abspath(os.path.join(profiles_dir, profile_name)).lower()
    
    count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline:
                    cmd_str = " ".join(cmdline).lower()
                    if abs_profile_dir in cmd_str:
                        proc.kill()
                        count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    if count > 0:
        db_manager.log_msg(profile_name, f"[{profile_name}] Đã dọn dẹp {count} tiến trình Chrome kẹt.")

def p_log(profile_name, msg):
    print(msg)
    db_manager.log_msg(profile_name, msg)

def main(profile_name, current_loop):
    db_manager.set_status(profile_name, "Initializing")
    p_log(profile_name, f"[{profile_name}] Tiến trình worker đã khởi động (PID: {os.getpid()})")

    import ai_generator
    import social_poster
    import profile_manager
    
    has_error = False
    
    p_log(profile_name, f"\n--- Bắt đầu vòng {current_loop} ---")
    
    global_cfg = db_manager.get_global_config()
    profile_cfg = db_manager.get_profile_config(profile_name)

    # VALIDATION: Kiểm tra các trường thông tin cấu hình bắt buộc
    ai_source = profile_cfg.get("ai_source", "google").strip()
    status_base = profile_cfg.get("status_base", "").strip()
    prompt_base = profile_cfg.get("prompt_base", "").strip()
    output_txt_dir = profile_cfg.get("output_txt_dir", "").strip()
    
    input_img_dir = profile_cfg.get("input_img_dir", "").strip()
    prompt_img = profile_cfg.get("prompt_img", "").strip()
    output_img_dir = profile_cfg.get("output_img_dir", "").strip()
    
    fanpage_url = profile_cfg.get("fanpage_url", config.get("fanpage_url", "")).strip()

    missing_fields = []
    if not status_base: missing_fields.append("Status mẫu")
    if not prompt_base: missing_fields.append("Prompt viết status")
    if not output_txt_dir: missing_fields.append("Thư mục lưu Text")
    
    if not input_img_dir: missing_fields.append("Thư mục ảnh mẫu")
    if not prompt_img: missing_fields.append("Prompt tạo ảnh")
    if not output_img_dir: missing_fields.append("Thư mục lưu Ảnh")
    
    if not fanpage_url: missing_fields.append("Link Fanpage")

    if missing_fields:
        err_msg = f"[{profile_name}] KHÔNG THỂ CHẠY. Thiếu thông tin: " + ", ".join(missing_fields)
        p_log(profile_name, err_msg)
        db_manager.set_status(profile_name, "Missing Config")
        sys.exit(1)

    db_manager.set_status(profile_name, "Cleaning up Chrome")
    cleanup_chrome(profile_name)

    db_manager.set_status(profile_name, "Initializing Playwright")
    
    if not os.path.exists(input_img_dir):
        os.makedirs(input_img_dir, exist_ok=True)
    if not os.path.exists(output_txt_dir):
        os.makedirs(output_txt_dir, exist_ok=True)
    if not os.path.exists(output_img_dir):
        os.makedirs(output_img_dir, exist_ok=True)

    images = [os.path.join(input_img_dir, f) for f in os.listdir(input_img_dir) if os.path.isfile(os.path.join(input_img_dir, f))]
    if not images:
        err_msg = f"[{profile_name}] LỖI: Thư mục ảnh ({input_img_dir}) trống! Không có ảnh đầu vào."
        p_log(profile_name, err_msg)
        db_manager.set_status(profile_name, "Missing Input Images")
        sys.exit(1)
        
    input_img = random.choice(images)
    
    txt_path, img_path = None, None
    try:
        # 1. AI Studio
        db_manager.set_status(profile_name, "Generating Content")
        p_log(profile_name, f"[{profile_name}] Khởi động trình duyệt tạo nội dung AI...")
        context = None
        try:
            with sync_playwright() as p:
                pm = profile_manager.ProfileManager(config.get("profiles_dir", "profiles"))
                context = pm.launch_browser_for_profile(p, profile_name, headless=config.get("headless_mode", False))
                ai_gen = ai_generator.AIGenerator(context, config.get("ai_studio_url", "https://aistudio.google.com/prompts/new_chat"))
                txt_path, img_path = ai_gen.generate_content(
                    profile_name, 
                    prompt_base, 
                    status_base, 
                    input_img, 
                    prompt_img, 
                    output_txt_dir, 
                    output_img_dir,
                    ai_source
                )
                context.close()
                context = None
        finally:
            if context:
                try:
                    context.close()
                except:
                    pass
        p_log(profile_name, f"[{profile_name}] Text đã lưu: {txt_path}")
        p_log(profile_name, f"[{profile_name}] Ảnh đã lưu: {img_path}")
        
        # 2. Posting
        if txt_path and img_path:
            db_manager.set_status(profile_name, "Posting to Fanpage")
            p_log(profile_name, f"[{profile_name}] Khởi động trình duyệt đăng bài Fanpage...")
            context = None
            try:
                with sync_playwright() as p:
                    pm = profile_manager.ProfileManager(config.get("profiles_dir", "profiles"))
                    context = pm.launch_browser_for_profile(p, profile_name, headless=config.get("headless_mode", False))
                    poster = social_poster.SocialPoster(context, fanpage_url)
                    poster.post_to_fanpage(profile_name, txt_path, img_path)
                    context.close()
                    context = None
            finally:
                if context:
                    try:
                        context.close()
                    except:
                        pass
                        
    except Exception as e:
        err_msg = str(e)
        if "free plan limit" in err_msg.lower() or "limit resets" in err_msg.lower():
            p_log(profile_name, f"[{profile_name}] Lỗi hết hạn GPT: {err_msg} -> Tự động chuyển sang nghỉ chờ thử lại.")
            db_manager.set_status(profile_name, "Chờ thử lại (Hết hạn GPT)")
            sys.exit(3)

        if "POLICY_VIOLATION" in err_msg:
            p_log(profile_name, f"[{profile_name}] Lỗi Policy: {err_msg} -> Tự động báo lỗi và sẽ chạy lại tác vụ.")
            sys.exit(2) # Code 2 means policy violation, controller can decide to retry
            
        if "Target page, context or browser has been closed" in err_msg or "Execution context was destroyed" in err_msg or "Timeout" in err_msg:
            p_log(profile_name, f"[{profile_name}] Lỗi Trình duyệt Crash/Timeout: {err_msg} -> Hệ thống sẽ tự động chạy lại vòng này.")
            sys.exit(2)
            
        # BUG TRACKER: Ghi lại lỗi cấu trúc thông qua bug_tracker
        bug_tracker.log_bug(
            feature="worker_process",
            step="main",
            exc=e,
            context={"profile_name": profile_name}
        )
            
        p_log(profile_name, f"[{profile_name}] Lỗi Runtime: {err_msg}")
        db_manager.set_status(profile_name, f"Lỗi: {err_msg[:60]}")
        sys.exit(1)
        
    db_manager.set_status(profile_name, "Completed Task")
    sys.exit(0)

if __name__ == "__main__":
    try:
        if len(sys.argv) > 2:
            main(sys.argv[1], int(sys.argv[2]))
        else:
            print("Vui lòng cung cấp tên profile và current_loop. Cách dùng: python worker_process.py <Profile_Name> <Current_Loop>")
            sys.exit(1)
    except Exception as e:
        import traceback
        print("\n" + "="*50)
        print("CÓ LỖI NGHIÊM TRỌNG (CRASH) XẢY RA KHÔNG THỂ PHỤC HỒI:")
        print(traceback.format_exc())
        print("="*50)
        sys.exit(1)
