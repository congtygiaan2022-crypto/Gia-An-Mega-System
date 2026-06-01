import os
import time
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import profile_manager
import social_poster

def main():
    profile_name = "Akiho Yoshizawa"
    chat_url = "https://chatgpt.com/c/6a15ee36-2304-83ec-b50d-4c6bad6790ed"
    output_dir = "output_data"
    os.makedirs(output_dir, exist_ok=True)
    
    img_path = os.path.join(output_dir, f"{profile_name}_recover.png")
    txt_path = os.path.join(output_dir, f"{profile_name}_recover.txt")

    print(f"Bắt đầu khôi phục tiến trình cho {profile_name}...")
    
    with sync_playwright() as p:
        pm = profile_manager.ProfileManager("profiles")
        context = pm.launch_browser_for_profile(p, profile_name, headless=False)
        page = context.new_page()
        
        try:
            print(f"Ảnh và Text đã có sẵn: {img_path}, {txt_path}")
            
            # 3. ĐĂNG LÊN FACEBOOK
            print("Đang tiến hành đăng bài lên Facebook...")
            import json
            import db_manager
            db_manager.init_db()
            profile_cfg = db_manager.get_profile_config(profile_name)
            fanpage_url = profile_cfg.get("fanpage_url", "")
            if not fanpage_url:
                print("Không tìm thấy fanpage_url cho profile này.")
                return
                
            poster = social_poster.SocialPoster(context, fanpage_url)
            poster.post_to_fanpage(profile_name, txt_path, img_path)
            print("DONE! Đã đăng thành công lên Facebook!")

        except Exception as e:
            print(f"LỖI: {e}")
        finally:
            context.close()

if __name__ == "__main__":
    main()
