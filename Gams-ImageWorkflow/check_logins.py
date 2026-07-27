import sys
import os
import time
import argparse
from playwright.sync_api import sync_playwright
import db_manager
import profile_manager

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Import 2FA and FB login helpers directly from worker_process
sys.path.append(os.getcwd())
try:
    import worker_process
except ImportError:
    worker_process = None

def p_log(profile_name, msg):
    print(msg)
    try:
        db_manager.log_msg(profile_name, msg)
    except Exception:
        pass

def check_is_logged_in_facebook(page) -> bool:
    try:
        if worker_process is not None:
            try:
                return worker_process.check_is_logged_in_playwright(page)
            except:
                pass
                
        url = page.url
        if "facebook.com" not in url or "login" in url or "checkpoint" in url or "two_step" in url:
            return False
        
        selectors = [
            "[data-pagelet='LeftRail']",
            "[aria-label='Your profile']",
            "[aria-label='Facebook'][role='navigation']",
            "a[href*='/me/']",
            "a[href*='profile.php']",
            "div[role='banner'] [aria-label*='Trang cá nhân']",
            "div[role='banner'] [aria-label*='Profile']"
        ]
        for sel in selectors:
            try:
                if page.locator(sel).first.is_visible():
                    return True
            except:
                pass
        return False
    except Exception:
        return False

def check_chatgpt(page) -> bool:
    try:
        try:
            page.wait_for_selector('#prompt-textarea', timeout=10000)
        except:
            pass
        
        login_selectors = [
            'button[data-testid="login-button"]',
            'a[href*="auth/login"]',
            'button:has-text("Log in")',
            'button:has-text("Sign up")',
            'button:has-text("Đăng nhập")',
            'button:has-text("Đăng ký")',
            'a:has-text("Log in")',
            'a:has-text("Sign up")',
            'a:has-text("Đăng nhập")',
            'a:has-text("Đăng ký")'
        ]
        is_logged_in = True
        for sel in login_selectors:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible():
                    is_logged_in = False
                    break
            except:
                pass
                
        if is_logged_in:
            if page.locator('#prompt-textarea').count() == 0:
                is_logged_in = False
                
        return is_logged_in
    except Exception:
        return False

def check_google_ai(page) -> bool:
    try:
        textarea_selectors = [
            'textarea[aria-label="Enter a prompt"]',
            'textarea[formcontrolname="promptText"]',
            'textarea.textarea',
            'textarea[placeholder*="prompt"]'
        ]
        for _ in range(10):
            for sel in textarea_selectors:
                try:
                    if page.locator(sel).first.is_visible():
                        return True
                except:
                    pass
            time.sleep(1)
        return False
    except Exception:
        return False

def login_chatgpt_playwright(page, email, password) -> bool:
    try:
        p_log(page.context.browser.contexts[0].owner or "Profile", f"Đang tiến hành tự động đăng nhập ChatGPT với email: {email}...")
        page.goto("https://chatgpt.com/auth/login", timeout=45000)
        page.wait_for_timeout(3000)
        
        # Click Log in button if it exists
        try:
            login_btn = page.locator('button:has-text("Log in"), button:has-text("Đăng nhập")').first
            if login_btn.is_visible():
                login_btn.click()
                page.wait_for_timeout(2000)
        except:
            pass
            
        email_selectors = ['input[type="email"]', 'input#email', 'input[name="email"]', 'input[name="username"]']
        email_input = None
        for _ in range(15):
            for sel in email_selectors:
                try:
                    loc = page.locator(sel).first
                    if loc.is_visible() and loc.is_enabled():
                        email_input = loc
                        break
                except:
                    pass
            if email_input:
                break
            page.wait_for_timeout(1000)
            
        if not email_input:
            return False
            
        email_input.fill(email)
        page.wait_for_timeout(1000)
        
        # Click Continue
        continue_btn = None
        continue_selectors = [
            'button[type="submit"]',
            'button:has-text("Continue")',
            'button:has-text("Tiếp tục")'
        ]
        for sel in continue_selectors:
            try:
                loc = page.locator(sel).first
                if loc.is_visible():
                    continue_btn = loc
                    break
            except:
                pass
        if continue_btn:
            continue_btn.click()
        else:
            page.keyboard.press("Enter")
            
        page.wait_for_timeout(3000)
        
        # Wait for password input
        password_selectors = ['input[type="password"]', 'input#password', 'input[name="password"]']
        password_input = None
        for _ in range(15):
            for sel in password_selectors:
                try:
                    loc = page.locator(sel).first
                    if loc.is_visible() and loc.is_enabled():
                        password_input = loc
                        break
                except:
                    pass
            if password_input:
                break
            page.wait_for_timeout(1000)
            
        if not password_input:
            return False
            
        password_input.fill(password)
        page.wait_for_timeout(1000)
        
        # Click Continue
        continue_btn = None
        for sel in continue_selectors:
            try:
                loc = page.locator(sel).first
                if loc.is_visible():
                    continue_btn = loc
                    break
            except:
                pass
        if continue_btn:
            continue_btn.click()
        else:
            page.keyboard.press("Enter")
            
        page.wait_for_timeout(5000)
        return True
    except Exception as e:
        return False

def parse_gpt_account(profile_name):
    # Đọc tài khoản GPT từ gpt_account.txt nếu có
    acc_file = os.path.join("profiles", profile_name, "gpt_account.txt")
    if not os.path.exists(acc_file):
        return None, None
    try:
        email, password = None, None
        with open(acc_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("Email:"):
                    email = line.split(":", 1)[1].strip()
                elif line.startswith("Password:"):
                    password = line.split(":", 1)[1].strip()
        return email, password
    except:
        return None, None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("profile_name")
    parser.add_argument("--action", default="check", choices=["check", "login"])
    parser.add_argument("--platforms", default="fb,gpt,google")
    args = parser.parse_args()
    
    profile_name = args.profile_name
    action = args.action
    platforms = [p.strip().lower() for p in args.platforms.split(",") if p.strip()]
    
    action_text = "Kiểm tra" if action == "check" else "Tự động đăng nhập"
    p_log(profile_name, f"🔍 Bắt đầu {action_text} cho các nền tảng: {', '.join(platforms).upper()}...")
    
    config = db_manager.get_profile_config(profile_name)
    ai_source = config.get("ai_source", "google").lower()
    
    pm = profile_manager.ProfileManager("profiles")
    
    fb_status = config.get("facebook_login_status", "Chưa kiểm tra")
    ai_status = config.get("ai_login_status", "Chưa kiểm tra")
    
    with sync_playwright() as p:
        try:
            # Nếu chỉ check thì headless=True, nếu cần login tự động thì headless=False
            is_headless = (action == "check")
            context = pm.launch_browser_for_profile(p, profile_name, headless=is_headless)
            page = context.new_page()
            
            # 1. Xử lý Facebook
            if "fb" in platforms:
                p_log(profile_name, f"Kiểm tra đăng nhập Facebook...")
                is_fb_ok = False
                try:
                    page.goto("https://www.facebook.com/", timeout=30000)
                    page.wait_for_timeout(3000)
                    is_fb_ok = check_is_logged_in_facebook(page)
                    if not is_fb_ok:
                        page.goto("https://business.facebook.com/latest/home", timeout=30000)
                        page.wait_for_timeout(3000)
                        if "login" not in page.url and ("business.facebook.com" in page.url or page.locator(".meta-business-suite").first.is_visible() or "latest/home" in page.url):
                            is_fb_ok = True
                except Exception as fb_err:
                    p_log(profile_name, f"Lỗi load Facebook: {fb_err}")
                
                if is_fb_ok:
                    p_log(profile_name, f"Facebook: Đã đăng nhập.")
                    fb_status = "Thành công"
                else:
                    if action == "login" and worker_process is not None:
                        p_log(profile_name, f"Facebook chưa đăng nhập. Tiến hành tự động đăng nhập...")
                        fb_account = config.get("facebook_account", "").strip()
                        if not fb_account:
                            global_cfg = db_manager.get_global_config()
                            if global_cfg.get("apply_fb_global"):
                                fb_account = global_cfg.get("global_facebook_account", "").strip()
                        
                        if fb_account:
                            try:
                                login_success = worker_process.check_and_login_facebook_playwright(context, profile_name, fb_account)
                                if login_success:
                                    fb_status = "Thành công"
                                else:
                                    fb_status = "Thất bại"
                            except Exception as login_err:
                                p_log(profile_name, f"Lỗi tự động đăng nhập FB: {login_err}")
                                fb_status = "Thất bại"
                        else:
                            p_log(profile_name, f"⚠️ Facebook chưa đăng nhập và không có thông tin tài khoản cấu hình.")
                            fb_status = "Thất bại"
                    else:
                        fb_status = "Thất bại"
            
            # 2. Xử lý AI
            # ChatGPT
            if "gpt" in platforms and ai_source == "chatgpt":
                p_log(profile_name, f"Kiểm tra đăng nhập ChatGPT...")
                is_gpt_ok = False
                try:
                    page.goto("https://chatgpt.com/", timeout=30000)
                    page.wait_for_timeout(3000)
                    is_gpt_ok = check_chatgpt(page)
                except Exception as gpt_err:
                    p_log(profile_name, f"Lỗi load ChatGPT: {gpt_err}")
                    
                if is_gpt_ok:
                    p_log(profile_name, f"ChatGPT: Đã đăng nhập.")
                    ai_status = "Thành công"
                else:
                    if action == "login":
                        p_log(profile_name, f"ChatGPT chưa đăng nhập. Đang tìm tài khoản GPT đã lưu...")
                        email, password = parse_gpt_account(profile_name)
                        if email and password:
                            try:
                                login_success = login_chatgpt_playwright(page, email, password)
                                page.wait_for_timeout(5000)
                                page.goto("https://chatgpt.com/", timeout=30000)
                                page.wait_for_timeout(3000)
                                if check_chatgpt(page):
                                    p_log(profile_name, f"ChatGPT: Đăng nhập tự động thành công.")
                                    ai_status = "Thành công"
                                else:
                                    p_log(profile_name, f"❌ Đăng nhập tự động ChatGPT thất bại (có thể kẹt Captcha).")
                                    ai_status = "Thất bại"
                            except Exception as login_err:
                                p_log(profile_name, f"Lỗi tự động đăng nhập ChatGPT: {login_err}")
                                ai_status = "Thất bại"
                        else:
                            p_log(profile_name, f"⚠️ ChatGPT chưa đăng nhập và không tìm thấy file gpt_account.txt để đăng nhập tự động.")
                            ai_status = "Thất bại"
                    else:
                        ai_status = "Thất bại"
                        
            # Google AI
            if "google" in platforms and ai_source == "google":
                p_log(profile_name, f"Kiểm tra đăng nhập Google AI Studio...")
                is_google_ok = False
                try:
                    page.goto("https://aistudio.google.com/prompts/new_chat?model=gemini-3-pro-image-preview", timeout=30000)
                    page.wait_for_timeout(3000)
                    is_google_ok = check_google_ai(page)
                except Exception as google_err:
                    p_log(profile_name, f"Lỗi load Google AI Studio: {google_err}")
                    
                if is_google_ok:
                    p_log(profile_name, f"Google AI Studio: Đã đăng nhập.")
                    ai_status = "Thành công"
                else:
                    if action == "login":
                        p_log(profile_name, f"⚠️ Google AI Studio chưa đăng nhập. Hãy mở trình duyệt thủ công (Browser) để đăng nhập tài khoản Google.")
                    ai_status = "Thất bại"
            
            context.close()
        except Exception as e:
            p_log(profile_name, f"Lỗi kiểm tra/đăng nhập: {e}")
            
    p_log(profile_name, f"Kết quả kiểm tra: Facebook -> {fb_status} | AI ({ai_source.upper()}) -> {ai_status}")
    
    # Lưu lại trạng thái vào database
    config = db_manager.get_profile_config(profile_name)
    if "fb" in platforms:
        config["facebook_login_status"] = fb_status
    if "gpt" in platforms and ai_source == "chatgpt":
        config["ai_login_status"] = ai_status
    if "google" in platforms and ai_source == "google":
        config["ai_login_status"] = ai_status
        
    db_manager.save_profile_config(profile_name, config)

if __name__ == "__main__":
    main()
