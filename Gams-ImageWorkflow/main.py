import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import json
import random
import threading
from playwright.sync_api import sync_playwright

# Add Jarvis OS core for global logger
import sys
JARVIS_CORE_PATH = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')), 'Gams-AiJarvisOs', 'core')
if JARVIS_CORE_PATH not in sys.path:
    sys.path.insert(0, JARVIS_CORE_PATH)
try:
    import global_logger
except ImportError:
    global_logger = None

from profile_manager import ProfileManager
from ai_generator import AIGenerator
from social_poster import SocialPoster

def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_lines(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def worker_thread(profile_name, config, input_image, prompt, status_base):
    print(f"[{profile_name}] Bắt đầu luồng...")
    if global_logger:
        global_logger.log_history("ImageWorkflow", f"Bắt đầu luồng {profile_name}")
        
    try:
        txt_path, img_path = None, None
        
        # 1. Tạo AI Content
        context = None
        try:
            with sync_playwright() as p:
                pm = ProfileManager(config.get("profiles_dir", "profiles"))
                context = pm.launch_browser_for_profile(p, profile_name, headless=config.get("headless_mode", False))
                ai_gen = AIGenerator(context, config.get("ai_studio_url", "https://aistudio.google.com/prompts/new_chat"), config.get("output_data_dir", "output_data"))
                txt_path, img_path = ai_gen.generate_content(profile_name, prompt, status_base, input_image)
                context.close()
                context = None
        finally:
            if context:
                try:
                    context.close()
                except:
                    pass
        
        # 2. Đăng Fanpage
        if txt_path and img_path:
            context = None
            try:
                with sync_playwright() as p:
                    pm = ProfileManager(config.get("profiles_dir", "profiles"))
                    context = pm.launch_browser_for_profile(p, profile_name, headless=config.get("headless_mode", False))
                    poster = SocialPoster(context, config.get("fanpage_url", ""))
                    poster.post_to_fanpage(profile_name, txt_path, img_path)
                    context.close()
                    context = None
            finally:
                if context:
                    try:
                        context.close()
                    except:
                        pass
        
        print(f"[{profile_name}] Hoàn thành luồng.")
        if global_logger:
            global_logger.log_history("ImageWorkflow", f"Hoàn thành luồng {profile_name}")
    except Exception as e:
        print(f"[{profile_name}] LỖI: {e}")
        if global_logger:
            import traceback
            global_logger.report_bug("ImageWorkflow", "worker_thread", str(e), {"profile": profile_name, "traceback": traceback.format_exc()})

def main():
    config = load_config()
    
    # Load data
    prompts = load_lines(config["prompts_file"])
    statuses = load_lines(config["status_file"])
    
    input_dir = config["input_images_dir"]
    images = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
    
    if not prompts or not statuses:
        print("Lỗi: File prompts.txt hoặc status.txt bị trống!")
        return

    num_threads = config.get("threads", 2)
    threads = []
    
    # Giả lập chạy với N profiles, mỗi profile lấy ngẫu nhiên 1 ảnh, 1 prompt, 1 status
    for i in range(num_threads):
        profile_name = f"Profile_{i+1}"
        input_img = random.choice(images) if images else "dummy.png"
        prompt = random.choice(prompts)
        status = random.choice(statuses)
        
        t = threading.Thread(target=worker_thread, args=(profile_name, config, input_img, prompt, status))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    print("Tất cả các luồng đã chạy xong.")

if __name__ == "__main__":
    main()
