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
import pyotp
import re
import scraper
import content_deduplicator

def get_totp_code(secret: str) -> str:
    try:
        secret = secret.replace(" ", "").replace("-", "").upper()
        # Add padding if needed
        missing_padding = len(secret) % 8
        if missing_padding:
            secret += '=' * (8 - missing_padding)
        totp = pyotp.TOTP(secret)
        return totp.now()
    except Exception as e:
        print(f"Loi sinh ma 2FA: {e}")
        return ""

def acquire_fb_lock(profile_name, lock_file="scratch/fb_posting.lock", timeout=600):
    """
    Chờ và tạo file lock để độc quyền truy cập luồng đăng Facebook (tránh xung đột session của cùng 1 tài khoản).
    """
    os.makedirs("scratch", exist_ok=True)
    start_time = time.time()
    last_logged_time = 0
    while time.time() - start_time < timeout:
        try:
            with open(lock_file, "x") as f:
                f.write(profile_name)
            p_log(profile_name, f"[{profile_name}] ✅ Đã lấy được Khóa Độc Quyền Đăng Facebook.")
            return True
        except FileExistsError:
            try:
                with open(lock_file, "r") as f:
                    holder = f.read().strip()
            except:
                holder = "profile khác"
            
            now = time.time()
            if now - last_logged_time >= 15:
                p_log(profile_name, f"[{profile_name}] ⏳ Đang xếp hàng chờ đăng Facebook. Khóa đang được giữ bởi: {holder}...")
                last_logged_time = now
                
            time.sleep(2)
            
            # Tự giải phóng nếu khóa quá cũ (tránh deadlock)
            try:
                mtime = os.path.getmtime(lock_file)
                if time.time() - mtime > 240:
                    os.remove(lock_file)
                    p_log(profile_name, f"[{profile_name}] Warning: Phát hiện khóa cũ quá 4 phút, tự động giải phóng.")
            except:
                pass
                
    p_log(profile_name, f"[{profile_name}] ❌ Timeout chờ khóa đăng Facebook.")
    return False

def release_fb_lock(lock_file="scratch/fb_posting.lock"):
    """
    Giải phóng khóa đăng Facebook.
    """
    try:
        if os.path.exists(lock_file):
            os.remove(lock_file)
    except:
        pass

def check_is_logged_in_playwright(page) -> bool:
    try:
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

def check_and_login_instagram_playwright(context, profile_name) -> bool:
    """
    Truy cập Instagram, nếu chưa đăng nhập thì click 'Đăng nhập bằng Facebook'.
    Do context đã đăng nhập Facebook trước đó, Instagram sẽ tự động login thành công.
    """
    page = context.new_page()
    try:
        p_log(profile_name, f"[{profile_name}] Kiểm tra đăng nhập Instagram...")
        page.goto("https://www.instagram.com/", timeout=45000)
        page.wait_for_timeout(4000)
        
        # Click Escape để đóng các popups nếu có
        for _ in range(2):
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            
        # Kiểm tra đã đăng nhập chưa
        is_logged_in = False
        for sel in ['a[href*="/direct/inbox/"]', 'svg[aria-label="New post"]', 'span:has-text("Messages")', 'a[href*="/stories/"]']:
            try:
                if page.locator(sel).first.count() > 0:
                    is_logged_in = True
                    break
            except:
                pass
                
        if is_logged_in:
            p_log(profile_name, f"[{profile_name}] Instagram đã được đăng nhập từ trước.")
            page.close()
            return True
            
        p_log(profile_name, f"[{profile_name}] Phát hiện Instagram chưa đăng nhập. Thử click 'Đăng nhập bằng Facebook'...")
        
        # Tìm nút Log in with Facebook
        fb_btn = None
        for sel in [
            'button:has-text("Log in with Facebook")',
            'span:has-text("Log in with Facebook")',
            'span:has-text("Đăng nhập bằng Facebook")',
            'button:has-text("Đăng nhập bằng Facebook")',
            'button.sqdOP.y3zKF:has-text("Facebook")',
            'a[href*="/oauth/authorize"]',
            'button:has-text("Continue as")',
            'span:has-text("Continue as")'
        ]:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible():
                    fb_btn = loc
                    break
            except:
                pass
                
        if fb_btn:
            fb_btn.click()
            p_log(profile_name, f"[{profile_name}] Đã click liên kết đăng nhập Facebook trên Instagram. Đang chờ 10s...")
            page.wait_for_timeout(10000)
            
            # Đôi khi Facebook hỏi xác nhận "Continue as [Name]"
            try:
                continue_btn = page.locator('button[name="__CONFIRM__"], button:has-text("Tiếp tục dưới tên"), button:has-text("Continue as")').first
                if continue_btn.count() > 0 and continue_btn.is_visible():
                    continue_btn.click()
                    p_log(profile_name, f"[{profile_name}] Đã click xác nhận Tiếp tục đăng nhập Facebook.")
                    page.wait_for_timeout(8000)
            except:
                pass
                
            # Đóng các popup "Lưu thông tin đăng nhập" hay "Bật thông báo"
            try:
                for btn_text in ["Save info", "Lưu thông tin", "Not now", "Lúc khác", "Turn on", "Bật"]:
                    btn = page.locator(f'button:has-text("{btn_text}")').first
                    if btn.count() > 0 and btn.is_visible():
                        btn.click()
                        page.wait_for_timeout(2000)
            except:
                pass
                
            # Kiểm tra lại đăng nhập
            is_logged_in = False
            for sel in ['a[href*="/direct/inbox/"]', 'svg[aria-label="New post"]', 'span:has-text("Messages")']:
                try:
                    if page.locator(sel).first.count() > 0:
                        is_logged_in = True
                        break
                except:
                    pass
            if is_logged_in:
                p_log(profile_name, f"[{profile_name}] Đăng nhập Instagram bằng Facebook thành công!")
                page.close()
                return True
                
        p_log(profile_name, f"[{profile_name}] Không thể tự động đăng nhập Instagram bằng Facebook. Sẽ chạy cào ẩn danh hoặc thử lại sau.")
        page.close()
        return False
    except Exception as e:
        p_log(profile_name, f"[{profile_name}] Lỗi khi đăng nhập Instagram: {e}")
        try: page.close()
        except: pass
        return False

def check_and_login_threads_playwright(context, profile_name) -> bool:
    """
    Truy cập Threads, nếu chưa đăng nhập thì click 'Đăng nhập bằng Instagram'.
    Do context đã đăng nhập Instagram trước đó, Threads sẽ tự động login thành công.
    """
    page = context.new_page()
    try:
        p_log(profile_name, f"[{profile_name}] Kiểm tra đăng nhập Threads...")
        page.goto("https://www.threads.net/", timeout=45000)
        page.wait_for_timeout(4000)
        
        # Click Escape để đóng popup nếu có
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        
        # Kiểm tra đã đăng nhập chưa hoặc có cảnh báo chưa đăng nhập
        is_logged_in = False
        
        # Nếu thấy cảnh báo "Say more with Threads" hoặc "Join Threads" thì chắc chắn chưa đăng nhập
        has_warning = False
        for msg in ["Say more with Threads", "Join Threads to share thoughts", "Join Threads"]:
            try:
                # Dùng selector text hoặc contains text
                if page.locator(f'text="{msg}"').first.count() > 0 or page.locator(f'*:has-text("{msg}")').first.count() > 0:
                    has_warning = True
                    p_log(profile_name, f"[{profile_name}] Phát hiện cảnh báo chưa đăng nhập Threads: '{msg}'")
                    break
            except:
                pass
                
        if not has_warning:
            for sel in ['a[href*="/activity"]', 'svg[aria-label="Create thread"]', 'a[href*="/@"]']:
                try:
                    if page.locator(sel).first.count() > 0:
                        is_logged_in = True
                        break
                except:
                    pass
                
        if is_logged_in:
            p_log(profile_name, f"[{profile_name}] Threads đã được đăng nhập từ trước.")
            page.close()
            return True
            
        p_log(profile_name, f"[{profile_name}] Phát hiện Threads chưa đăng nhập. Thử click 'Đăng nhập bằng Instagram'...")
        
        # Tìm nút Log in with Instagram hoặc Đăng nhập
        insta_btn = None
        for sel in [
            'div:has-text("Log in with Instagram")',
            'button:has-text("Log in with Instagram")',
            'span:has-text("Log in with Instagram")',
            'div:has-text("Continue with Instagram")',
            'button:has-text("Continue with Instagram")',
            'span:has-text("Continue with Instagram")',
            'div:has-text("Tiếp tục bằng Instagram")',
            'button:has-text("Tiếp tục bằng Instagram")',
            'div:has-text("Đăng nhập bằng Instagram")',
            'button:has-text("Đăng nhập bằng Instagram")',
            'div[role="button"]:has-text("Instagram")',
            'div[role="button"]:has-text("Log in")',
            'div[role="button"]:has-text("Đăng nhập")',
            'button:has-text("Log in")',
            'button:has-text("Đăng nhập")',
            'div:has-text("Log in")',
            'div:has-text("Đăng nhập")',
            'a:has-text("Log in")',
            'a:has-text("Đăng nhập")'
        ]:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible():
                    insta_btn = loc
                    p_log(profile_name, f"[{profile_name}] Tìm thấy nút đăng nhập: '{sel}'")
                    break
            except:
                pass
                
        if insta_btn:
            insta_btn.click()
            p_log(profile_name, f"[{profile_name}] Đã click liên kết đăng nhập Instagram trên Threads. Đang chờ 10s...")
            page.wait_for_timeout(10000)
            
            # Threads đôi khi hỏi xác nhận ủy quyền Instagram
            try:
                approve_btn = page.locator('button:has-text("Allow"), button:has-text("Approve"), button:has-text("Cho phép"), button:has-text("Xác nhận")').first
                if approve_btn.count() > 0 and approve_btn.is_visible():
                    approve_btn.click()
                    p_log(profile_name, f"[{profile_name}] Đã click Cho phép liên kết Instagram với Threads.")
                    page.wait_for_timeout(8000)
            except:
                pass
                
            # Kiểm tra lại đăng nhập
            is_logged_in = False
            for sel in ['a[href*="/activity"]', 'svg[aria-label="Create thread"]', 'a[href*="/@"]']:
                try:
                    if page.locator(sel).first.count() > 0:
                        is_logged_in = True
                        break
                except:
                    pass
            if is_logged_in:
                p_log(profile_name, f"[{profile_name}] Đăng nhập Threads bằng Instagram thành công!")
                page.close()
                return True
                
        p_log(profile_name, f"[{profile_name}] Không thể tự động đăng nhập Threads bằng Instagram. Sẽ chạy cào ẩn danh hoặc thử lại sau.")
        page.close()
        return False
    except Exception as e:
        p_log(profile_name, f"[{profile_name}] Lỗi khi đăng nhập Threads: {e}")
        try: page.close()
        except: pass
        return False

def check_and_login_facebook_playwright(context, profile_name, fb_account_str) -> bool:
    parts = [p.strip() for p in fb_account_str.split('|')]
    uid = parts[0] if len(parts) > 0 else ""
    password = parts[1] if len(parts) > 1 else ""
    two_factor_secret = parts[2] if len(parts) > 2 else ""
    mail = parts[3] if len(parts) > 3 else ""
    
    if not uid or not password:
        db_manager.log_msg(profile_name, f"[{profile_name}] Thieu UID hoac Mat khau Facebook trong cau hinh.")
        return False

    page = context.new_page()
    try:
        db_manager.log_msg(profile_name, f"[{profile_name}] Dang kiem tra session Facebook da luu...")
        page.goto("https://www.facebook.com/", timeout=45000)
        page.wait_for_timeout(3000)
        
        if check_is_logged_in_playwright(page):
            db_manager.log_msg(profile_name, f"[{profile_name}] Dang nhap thanh cong tu session da luu.")
            return True
            
        try:
            page.goto("https://business.facebook.com/latest/home", timeout=45000)
            page.wait_for_timeout(4000)
            if "login" not in page.url and ("business.facebook.com" in page.url or page.locator(".meta-business-suite").first.is_visible() or "latest/home" in page.url):
                db_manager.log_msg(profile_name, f"[{profile_name}] Dang nhap thanh cong tu session da luu (Business Suite).")
                return True
        except Exception:
            pass

        db_manager.log_msg(profile_name, f"[{profile_name}] Phat hien chua dang nhap. Dang truy cap Facebook login...")
        page.goto("https://www.facebook.com/login", timeout=45000)
        page.wait_for_timeout(2000)
        
        page.wait_for_selector("input[name='email']", timeout=15000)
        page.fill("input[name='email']", uid)
        page.fill("input[name='pass']", password)
        page.wait_for_timeout(1000)
        page.keyboard.press("Enter")
        
        page.wait_for_timeout(5000)
        
        # Check CAPTCHA
        captcha_wait = 0
        while captcha_wait < 120:
            if "login" not in page.url:
                break
            try:
                recaptcha = page.locator("//iframe[contains(@src,'recaptcha') or contains(@title,'reCAPTCHA')]")
                if recaptcha.first.is_visible():
                    if captcha_wait == 0:
                        db_manager.log_msg(profile_name, f"[{profile_name}] Phat hien CAPTCHA. Hay giai thu cong trong 120s...")
                    page.wait_for_timeout(5000)
                    captcha_wait += 5
                    continue
            except Exception:
                pass
            break
            
        # Check checkpoint / 2FA
        is_2fa_page = False
        for _ in range(15):
            url = page.url
            if "checkpoint" in url or "two_step" in url or "confirm" in url or page.locator("input#approvals_code").first.is_visible() or page.locator("input[autocomplete='one-time-code']").first.is_visible():
                is_2fa_page = True
                break
            page.wait_for_timeout(1000)

        if is_2fa_page:
            p_log(profile_name, f"[{profile_name}] Phat hien man hinh xac thuc 2FA...")
            
            try:
                os.makedirs("scratch", exist_ok=True)
                page.screenshot(path=f"scratch/fb_2fa_{profile_name}.png")
            except Exception:
                pass

            if not two_factor_secret:
                p_log(profile_name, f"[{profile_name}] Loi: Yeu cau 2FA nhung cau hinh thieu Secret Key.")
                return False

            otp_selectors = [
                "input#approvals_code",
                "input[name='approvals_code']",
                "input[autocomplete='one-time-code']",
                "input[inputmode='numeric']",
                "input[type='tel']",
                "input[type='number']",
                "input[aria-label*='digit']",
                "input[aria-label*='code']",
                "input[aria-label*='Ma']",
                "input[aria-label*='xac thuc']",
                "//input[@type='text' and not(@name='email') and not(@name='pass')]"
            ]
            
            otp_field = None
            for sel in otp_selectors:
                try:
                    loc = page.locator(sel).first
                    if loc.is_visible() and loc.is_enabled():
                        otp_field = loc
                        p_log(profile_name, f"[{profile_name}] Tim thay o OTP.")
                        break
                except:
                    pass

            if not otp_field:
                p_log(profile_name, f"[{profile_name}] Chua thay o OTP. Thu click de mo...")
                try:
                    try_other_xpath = "//span[contains(text(),'Thu cach khac') or contains(text(),'Try another way') or contains(text(),'Use a different method')]/.. | //a[contains(text(),'Thu cach khac') or contains(text(),'Try another way')] | //div[@role='button'][contains(.,'Thu cach khac') or contains(.,'Try another way')]"
                    for _ in range(10):
                        try_other = page.locator(try_other_xpath).first
                        if try_other.is_visible():
                            try_other.click()
                            page.wait_for_timeout(2500)
                            break
                        page.wait_for_timeout(500)
                except Exception:
                    pass
                    
                try:
                    auth_app_xpath = "//span[contains(text(),'Ung dung xac thuc') or contains(text(),'Authentication app') or contains(text(),'Authenticator app')]/.. | //div[@role='radio'][.//*[contains(text(),'Ung dung xac thuc') or contains(text(),'Authentication app')]] | //label[.//*[contains(text(),'Ung dung xac thuc') or contains(text(),'Authentication app')]]"
                    for _ in range(10):
                        auth_app = page.locator(auth_app_xpath).first
                        if auth_app.is_visible():
                            auth_app.click()
                            page.wait_for_timeout(1000)
                            
                            continue_xpath = "//span[contains(text(),'Tiep tuc') or contains(text(),'Continue')]/.. | //button[contains(text(),'Tiep tuc') or contains(text(),'Continue')] | //div[@role='button'][.//*[contains(text(),'Tiep tuc') or contains(text(),'Continue')]]"
                            continue_btn = page.locator(continue_xpath).first
                            if continue_btn.is_visible():
                                continue_btn.click()
                                page.wait_for_timeout(3000)
                            break
                        page.wait_for_timeout(500)
                except Exception:
                    pass

                end_time = time.time() + 15
                while time.time() < end_time:
                    for sel in otp_selectors:
                        try:
                            loc = page.locator(sel).first
                            if loc.is_visible() and loc.is_enabled():
                                otp_field = loc
                                break
                        except:
                            pass
                    if otp_field:
                        break
                    page.wait_for_timeout(500)
                
            if otp_field:
                code = get_totp_code(two_factor_secret)
                if not code:
                    p_log(profile_name, f"[{profile_name}] Khong sinh duoc OTP.")
                    return False
                    
                p_log(profile_name, f"[{profile_name}] Da sinh ma OTP: {code}. Dang nhap...")
                try:
                    otp_field.click()
                    page.wait_for_timeout(500)
                    otp_field.fill("")
                    page.wait_for_timeout(1000)
                    page.keyboard.type(code)
                    page.wait_for_timeout(1000)
                    page.keyboard.press("Enter")
                except Exception as fill_err:
                    try:
                        page.keyboard.type(code)
                        page.keyboard.press("Enter")
                    except:
                        pass
                
                submit_selectors = [
                    "button#checkpointSubmitButton",
                    "button[type='submit']",
                    "//button[contains(.,'Tiep tuc') or contains(.,'Continue') or contains(.,'Submit')]",
                    "//span[text()='Tiep tuc' or text()='Continue' or text()='Submit']/..",
                    "input[type='submit']"
                ]
                submit_btn = None
                for sel in submit_selectors:
                    try:
                        loc = page.locator(sel).first
                        if loc.is_visible():
                            submit_btn = loc
                            break
                    except:
                        pass
                        
                if submit_btn:
                    try:
                        submit_btn.click(force=True, timeout=5000)
                    except:
                        try:
                            page.evaluate("el => el.click()", submit_btn.element_handle())
                        except:
                            page.keyboard.press("Enter")
                
                page.wait_for_timeout(8000)
            else:
                p_log(profile_name, f"[{profile_name}] Khong tim thay o nhap ma 2FA.")
                return False

        p_log(profile_name, f"[{profile_name}] Dang kiem tra trang thai login...")
        page.goto("https://www.facebook.com/", timeout=45000)
        page.wait_for_timeout(5000)
        
        if check_is_logged_in_playwright(page):
            p_log(profile_name, f"[{profile_name}] Dang nhap Facebook thanh cong.")
            return True
            
        try:
            page.goto("https://business.facebook.com/latest/home", timeout=45000)
            page.wait_for_timeout(5000)
            if "login" not in page.url and ("business.facebook.com" in page.url or page.locator(".meta-business-suite").first.is_visible() or "latest/home" in page.url):
                p_log(profile_name, f"[{profile_name}] Dang nhap Facebook thanh cong (Business Suite).")
                return True
        except Exception:
            pass
            
        p_log(profile_name, f"[{profile_name}] Dang nhap Facebook that bai.")
        return False
    except Exception as e:
        db_manager.log_msg(profile_name, f"[{profile_name}] Loi khi dang nhap Facebook: {e}")
        return False
    finally:
        try:
            page.close()
        except:
            pass

# Load global config
import json

def load_global_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

config = load_global_config()

def cleanup_chrome(profile_name):
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
        db_manager.log_msg(profile_name, f"[{profile_name}] Da don dep {count} Chrome bi ket.")

def p_log(profile_name, msg):
    print(msg)
    db_manager.log_msg(profile_name, msg)

def main(profile_name, current_loop, manual_platform=None, manual_post_id=None, bypass_ai=False):
    db_manager.set_status(profile_name, "Initializing")
    p_log(profile_name, f"[{profile_name}] Worker process started (PID: {os.getpid()})")

    import ai_generator
    import social_poster
    import profile_manager
    
    has_error = False
    p_log(profile_name, f"\n--- Bat dau vong {current_loop} ---")
    
    global_cfg = db_manager.get_global_config()
    profile_cfg = db_manager.get_profile_config(profile_name)

    # VALIDATION
    ai_source = profile_cfg.get("ai_source", "google").strip()
    status_base = profile_cfg.get("status_base", "").strip()
    prompt_base = profile_cfg.get("prompt_base", "").strip()
    output_txt_dir = profile_cfg.get("output_txt_dir", "").strip()
    
    input_img_dir = profile_cfg.get("input_img_dir", "").strip()
    prompt_img = profile_cfg.get("prompt_img", "").strip()
    output_img_dir = profile_cfg.get("output_img_dir", "").strip()
    
    fanpage_url = profile_cfg.get("fanpage_url", config.get("fanpage_url", "")).strip()

    missing_fields = []
    if not profile_cfg.get("instagram_urls") and not profile_cfg.get("x_urls"): missing_fields.append("Link Nguon (Instagram/X)")
    if not prompt_base: missing_fields.append("Prompt viet status")
    if not output_txt_dir: missing_fields.append("Thu muc luu Text")
    if not input_img_dir: missing_fields.append("Thu muc anh goc tam thoi")
    if not output_img_dir: missing_fields.append("Thu muc luu Anh ket qua")
    if not fanpage_url: missing_fields.append("Link Fanpage")

    if missing_fields:
        err_msg = f"[{profile_name}] KHONG THE CHAY. Thieu thong tin: " + ", ".join(missing_fields)
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

    # Check FB account configuration
    use_fb_global = global_cfg.get("apply_fb_global", False)
    if use_fb_global:
        fb_account = global_cfg.get("global_facebook_account", "").strip()
        p_log(profile_name, f"[{profile_name}] Su dung tai khoan FB chung.")
    else:
        fb_account = profile_cfg.get("facebook_account", "").strip()
        p_log(profile_name, f"[{profile_name}] Su dung tai khoan FB rieng.")

    # Instagram, X, & Threads sources
    instagram_urls = profile_cfg.get("instagram_urls", [])
    x_urls = profile_cfg.get("x_urls", [])
    threads_urls = profile_cfg.get("threads_urls", [])
    
    # Prepare Fanpage list
    import urllib.parse
    raw_urls = [u.strip() for u in re.split(r'[\n,]+', fanpage_url) if u.strip()]
    if not raw_urls:
        raw_urls = [fanpage_url]
        
    urls = []
    seen_ids = set()
    for u in raw_urls:
        asset_id = ""
        try:
            parsed_url = urllib.parse.urlparse(u)
            params = urllib.parse.parse_qs(parsed_url.query)
            if "asset_id" in params and params["asset_id"]:
                asset_id = params["asset_id"][0]
            elif "page_id" in params and params["page_id"]:
                asset_id = params["page_id"][0]
            elif "id" in params and params["id"]:
                asset_id = params["id"][0]
            else:
                path_parts = parsed_url.path.strip("/").split("/")
                if path_parts:
                    asset_id = path_parts[-1]
        except Exception:
            pass
        
        identifier = asset_id if asset_id else u
        if identifier not in seen_ids:
            seen_ids.add(identifier)
            urls.append(u)

    # Launch browser once for all tasks
    db_manager.set_status(profile_name, "Starting Browser")
    p_log(profile_name, f"[{profile_name}] Khoi dong trinh duyet cho tac vu reup...")
    
    try:
        with sync_playwright() as p:
            pm = profile_manager.ProfileManager(config.get("profiles_dir", "profiles"))
            context = pm.launch_browser_for_profile(p, profile_name, headless=config.get("headless_mode", False))
            
            # 1. Login FB if configured
            if fb_account:
                p_log(profile_name, f"[{profile_name}] Kiem tra dang nhap Facebook...")
                db_manager.set_status(profile_name, "Checking FB Login")
                fb_login_success = check_and_login_facebook_playwright(context, profile_name, fb_account)
                if not fb_login_success:
                    p_log(profile_name, f"[{profile_name}] Canh bao: Dang nhap Facebook that bai.")
            
            # Tự động đồng bộ đăng nhập sang Instagram & Threads bằng session Facebook (chạy cho mọi trường hợp)
            try:
                check_and_login_instagram_playwright(context, profile_name)
            except Exception as ig_login_err:
                p_log(profile_name, f"[{profile_name}] Cảnh báo lỗi đăng nhập Instagram: {ig_login_err}")
            try:
                check_and_login_threads_playwright(context, profile_name)
            except Exception as th_login_err:
                p_log(profile_name, f"[{profile_name}] Cảnh báo lỗi đăng nhập Threads: {th_login_err}")
            
            # Create page to crawl
            page = context.new_page()
            
            # Đọc cấu hình chế độ test (chỉ quét không đăng) và số lượng quét
            manual_mode = (manual_platform is not None and manual_post_id is not None)
            if manual_mode:
                only_scrape = ("--test-mode" in sys.argv)
            else:
                try:
                    global_cfg = db_manager.get_global_config()
                    only_scrape = (global_cfg.get("only_scrape_no_post") == "true" or global_cfg.get("only_scrape_no_post") is True)
                except:
                    only_scrape = False

            try:
                scan_limit = int(profile_cfg.get("scan_limit", 10))
            except:
                scan_limit = 10
            if scan_limit < 1:
                scan_limit = 10

            manual_mode = (manual_platform is not None and manual_post_id is not None)
            
            # List of new posts to process
            new_posts_found = []
            
            if manual_mode:
                # Tạo URL bài viết gốc
                if manual_platform == "instagram":
                    post_url = f"https://www.instagram.com/p/{manual_post_id}/"
                elif manual_platform == "threads":
                    post_url = f"https://www.threads.net/t/{manual_post_id}"
                else: # manual_platform == "x"
                    post_url = f"https://x.com/x/status/{manual_post_id}"
                
                new_posts_found = [{
                    "platform": manual_platform,
                    "id": manual_post_id,
                    "url": post_url
                }]
                p_log(profile_name, f"[{profile_name}] ⚡ CHẠY THỦ CÔNG (ĐĂNG THẲNG): Nền tảng={manual_platform.upper()}, ID={manual_post_id}")
                # Bắt buộc chuyển only_scrape thành False để đăng thật bất chấp config hệ thống (nếu không có --test-mode)
                if not ("--test-mode" in sys.argv):
                    only_scrape = False
            else:
                # A. Scan Instagram
                if instagram_urls:
                    db_manager.set_status(profile_name, "Scanning Instagram")
                    for insta_url in instagram_urls:
                        if not insta_url.strip():
                            continue
                        if "instagram.com" not in insta_url.lower():
                            p_log(profile_name, f"[{profile_name}] Nguon Instagram khong hop le (khong co 'instagram.com'): {insta_url}. Bo qua.")
                            continue
                        p_log(profile_name, f"[{profile_name}] Quet nguon Instagram: {insta_url} (lay {scan_limit} bai moi nhat)")
                        posts = scraper.scrape_instagram_profile(page, insta_url, num_posts=scan_limit, profile_name=profile_name)
                        count_added = 0
                        for post in posts:
                            is_proc = db_manager.is_post_processed(profile_name, 'instagram', post['id'])
                            if is_proc:
                                p_log(profile_name, f"[{profile_name}] ⏭️ Bài viết INSTAGRAM ID: {post['id']} đã được xử lý/đăng trước đó. Bỏ qua.")
                            else:
                                new_posts_found.append({
                                    "platform": "instagram",
                                    "id": post['id'],
                                    "url": post['url']
                                })
                                count_added += 1
                                if not only_scrape and count_added >= 3:
                                    break
                                
                # B. Scan X (Twitter)
                if x_urls:
                    db_manager.set_status(profile_name, "Scanning X / Twitter")
                    for x_url in x_urls:
                        if not x_url.strip():
                            continue
                        if "x.com" not in x_url.lower() and "twitter.com" not in x_url.lower():
                            p_log(profile_name, f"[{profile_name}] Nguon X khong hop le (khong co 'x.com' hoặc 'twitter.com'): {x_url}. Bo qua.")
                            continue
                        p_log(profile_name, f"[{profile_name}] Quet nguon X: {x_url} (lay {scan_limit} bai moi nhat)")
                        tweets = scraper.scrape_x_profile(page, x_url, num_posts=scan_limit, profile_name=profile_name)
                        count_added = 0
                        for tweet in tweets:
                            is_proc = db_manager.is_post_processed(profile_name, 'x', tweet['id'])
                            if is_proc:
                                p_log(profile_name, f"[{profile_name}] ⏭️ Bài viết X (Twitter) ID: {tweet['id']} đã được xử lý/đăng trước đó. Bỏ qua.")
                            else:
                                new_posts_found.append({
                                    "platform": "x",
                                    "id": tweet['id'],
                                    "url": tweet['url'],
                                    "caption": tweet['caption'],
                                    "media_type": tweet['media_type'],
                                    "media_url": tweet['media_url']
                                })
                                count_added += 1
                                if not only_scrape and count_added >= 3:
                                    break
                                
                # C. Scan Threads
                if threads_urls:
                    db_manager.set_status(profile_name, "Scanning Threads")
                    for threads_url in threads_urls:
                        threads_url = threads_url.strip()
                        if not threads_url:
                            continue
                        if "threads.com" in threads_url.lower():
                            threads_url = threads_url.replace("threads.com", "threads.net")
                            
                        if "threads.net" not in threads_url.lower():
                            p_log(profile_name, f"[{profile_name}] Nguon Threads khong hop le (khong co 'threads.net'): {threads_url}. Bo qua.")
                            continue
                        p_log(profile_name, f"[{profile_name}] Quet nguon Threads: {threads_url} (lay {scan_limit} bai moi nhat)")
                        posts = scraper.scrape_threads_profile(page, threads_url, num_posts=scan_limit, profile_name=profile_name)
                        count_added = 0
                        for post in posts:
                            is_proc = db_manager.is_post_processed(profile_name, 'threads', post['id'])
                            if is_proc:
                                p_log(profile_name, f"[{profile_name}] ⏭️ Bài viết THREADS ID: {post['id']} đã được xử lý/đăng trước đó. Bỏ qua.")
                            else:
                                new_posts_found.append({
                                    "platform": "threads",
                                    "id": post['id'],
                                    "url": post['url']
                                })
                                count_added += 1
                                if not only_scrape and count_added >= 3:
                                    break
                                 
                p_log(profile_name, f"[{profile_name}] Tong so bai viet moi phat hien: {len(new_posts_found)}")
            
            # Process reup for each new post
            processed_count = 0
            
            for item in new_posts_found:
                platform = item["platform"]
                post_id = item["id"]
                post_url = item["url"]
                
                p_log(profile_name, f"[{profile_name}] Dang xu ly bai viet moi ({platform.upper()} ID: {post_id})...")
                db_manager.set_status(profile_name, f"Processing {platform.upper()}:{post_id}")
                
                caption = ""
                media_type = "text"
                media_url = ""
                
                # Scrape details if Instagram/Threads
                if platform == "instagram":
                    details = scraper.scrape_instagram_post(page, post_url, profile_name=profile_name)
                    if not details:
                        p_log(profile_name, f"[{profile_name}] Khong the cao chi tiet bai Instagram {post_id}. Bo qua.")
                        continue
                    caption = details["caption"]
                    media_type = details["media_type"]
                    media_url = details["media_url"]
                elif platform == "threads":
                    details = scraper.scrape_threads_post(page, post_url, profile_name=profile_name)
                    if not details:
                        p_log(profile_name, f"[{profile_name}] Khong the cao chi tiet bai Threads {post_id}. Bo qua.")
                        continue
                    caption = details["caption"]
                    media_type = details["media_type"]
                    media_url = details["media_url"]
                else: # platform == "x"
                    if manual_mode:
                        details = scraper.scrape_x_post(page, post_url, profile_name=profile_name)
                        if not details:
                            p_log(profile_name, f"[{profile_name}] Khong the cao chi tiet tweet X {post_id}. Bo qua.")
                            continue
                        caption = details["caption"]
                        media_type = details["media_type"]
                        media_url = details["media_url"]
                    else:
                        caption = item["caption"]
                        media_type = item["media_type"]
                        media_url = item["media_url"]
                    
                p_log(profile_name, f"[{profile_name}] Caption goc: '{caption[:100]}...'")
                p_log(profile_name, f"[{profile_name}] Loai media: {media_type}")
                
                # Download media
                temp_media_path = None
                if media_type != "text" and media_url:
                    ext = "mp4" if media_type == "video" else "png"
                    temp_filename = f"temp_{platform}_{post_id}.{ext}"
                    temp_media_path = os.path.abspath(os.path.join(input_img_dir, temp_filename))
                    
                    success = scraper.download_media_file(page, media_url, temp_media_path, media_type, post_url)
                    if not success:
                        p_log(profile_name, f"[{profile_name}] Tai file media that bai. Bo qua.")
                        continue
                    p_log(profile_name, f"[{profile_name}] Da tai file media goc ve: {temp_media_path}")
                
                # === LOC TRUNG NOI DUNG ===
                try:
                    new_fp = content_deduplicator.compute_fingerprints(caption, temp_media_path, media_type)
                    existing_fps = db_manager.get_content_fingerprints(profile_name, limit=300)
                    is_dup, dup_reason = content_deduplicator.is_duplicate(new_fp, existing_fps)
                    if is_dup:
                        if not manual_mode:
                            p_log(profile_name, f"[{profile_name}] ⚠️ SKIP: Bai viet {post_id} bi loc trung - {dup_reason}. Danh dau da xu ly.")
                            db_manager.mark_post_processed(profile_name, platform, post_id)
                            # Don dep file tam neu co
                            if temp_media_path and os.path.exists(temp_media_path):
                                try: os.remove(temp_media_path)
                                except: pass
                            continue
                        else:
                            p_log(profile_name, f"[{profile_name}] ℹ️ Bài viết {post_id} bị trùng lặp ({dup_reason}) nhưng bỏ qua kiểm tra vì chạy thủ công (Đăng thẳng).")
                    else:
                        p_log(profile_name, f"[{profile_name}] ✅ Noi dung bai viet {post_id} chua trung. Tien hanh reup...")
                except Exception as dup_err:
                    p_log(profile_name, f"[{profile_name}] Canh bao: Loi kiem tra trung ({dup_err}). Tiep tuc reup.")
                
                # AI rewrite
                txt_path, img_path = None, None
                
                # Xay dung prompt ro rang, co cau truc
                caption_clean = caption.strip() if caption and caption.strip() else ""
                if caption_clean:
                    prompt_base_full = f"Status goc tu bai dang [{platform.upper()}]:\n\"\"\"\n{caption_clean}\n\"\"\"\n\nYeu cau: {prompt_base}"
                else:
                    # Neu khong co caption (video khong co chu, anh khong co chu)
                    prompt_base_full = f"Day la bai dang [{platform.upper()}] khong co chu thich (chi co media).\n\nYeu cau: {prompt_base}"

                
                if only_scrape or bypass_ai:
                    txt_path = os.path.join(output_txt_dir, f"{profile_name}_{int(time.time())}.txt")
                    with open(txt_path, "w", encoding="utf-8") as f:
                        f.write(caption or "")
                    img_path = temp_media_path
                    if bypass_ai:
                        p_log(profile_name, f"[{profile_name}] ⚡ [BYPASS AI] Đăng reup không qua AI. Dùng caption và media gốc 100%.")
                    else:
                        p_log(profile_name, f"[{profile_name}] 🧪 [TEST MODE] Bỏ qua AI. Dùng caption và media gốc để lưu fingerprint.")
                else:
                    # AI rewrite với cơ chế tự động thử lại tối đa 3 lần đối với lỗi chính sách hoặc lỗi kết nối
                    ai_attempts = 0
                    max_ai_attempts = 3
                    ai_success = False
                    
                    while ai_attempts < max_ai_attempts:
                        ai_attempts += 1
                        db_manager.set_status(profile_name, f"Rewriting via AI (Lần {ai_attempts}/{max_ai_attempts})")
                        try:
                            ai_gen = ai_generator.AIGenerator(context, config.get("ai_studio_url", "https://aistudio.google.com/prompts/new_chat"))
                            
                            if media_type == "image" and temp_media_path:
                                txt_path, img_path = ai_gen.generate_content(
                                    profile_name, 
                                    prompt_base_full, 
                                    status_base, 
                                    temp_media_path, 
                                    prompt_img, 
                                    output_txt_dir, 
                                    output_img_dir,
                                    ai_source
                                )
                            else:
                                txt_path, _ = ai_gen.generate_content(
                                    profile_name, 
                                    prompt_base_full, 
                                    status_base, 
                                    temp_media_path if temp_media_path else "dummy.png", 
                                    "", 
                                    output_txt_dir, 
                                    output_img_dir,
                                    ai_source
                                )
                                img_path = temp_media_path
                                
                            p_log(profile_name, f"[{profile_name}] AI Text da luu: {txt_path}")
                            if img_path:
                                p_log(profile_name, f"[{profile_name}] AI Media da luu: {img_path}")
                            ai_success = True
                            break
                        except Exception as ai_err:
                            err_str = str(ai_err)
                            is_policy = any(x in err_str.lower() for x in ["policy_violation", "violate", "guardrails", "content policies"])
                            
                            if is_policy:
                                p_log(profile_name, f"[{profile_name}] ⚠️ Lỗi vi phạm chính sách AI (Lần {ai_attempts}/{max_ai_attempts}): {ai_err}")
                                if ai_attempts < max_ai_attempts:
                                    p_log(profile_name, f"[{profile_name}] Chờ 10 giây trước khi thử lại lần {ai_attempts + 1}...")
                                    time.sleep(10)
                                    continue
                                else:
                                    p_log(profile_name, f"[{profile_name}] ❌ Đã thử lại {max_ai_attempts} lần lỗi chính sách. Đánh dấu đã xử lý và bỏ qua bài viết này.")
                                    db_manager.mark_post_processed(profile_name, platform, post_id)
                                    break
                            else:
                                p_log(profile_name, f"[{profile_name}] ⚠️ Lỗi xử lý AI (Lần {ai_attempts}/{max_ai_attempts}): {ai_err}")
                                if "free plan limit" in err_str.lower() or "limit resets" in err_str.lower():
                                    # Lỗi hết hạn GPT thì raise luôn để thoát tiến trình và chờ đợi lâu theo thiết lập
                                    raise ai_err
                                    
                                if ai_attempts < max_ai_attempts:
                                    p_log(profile_name, f"[{profile_name}] Chờ 5 giây trước khi thử lại lần {ai_attempts + 1}...")
                                    time.sleep(5)
                                    continue
                                else:
                                    raise ai_err
                                    
                    if not ai_success:
                        # Dọn dẹp media tạm thời
                        if temp_media_path and os.path.exists(temp_media_path):
                            try: os.remove(temp_media_path)
                            except: pass
                        continue
                    
                # Post to FB Fanpage
                post_success = False
                if txt_path:
                    # Lấy khóa đăng FB độc quyền để tránh xung đột session
                    lock_acquired = acquire_fb_lock(profile_name)
                    try:
                        # Kiểm tra chế độ test (chỉ quét không đăng)
                        if not manual_mode:
                            try:
                                global_cfg = db_manager.get_global_config()
                                only_scrape = (global_cfg.get("only_scrape_no_post") == "true" or global_cfg.get("only_scrape_no_post") is True)
                            except Exception as e:
                                only_scrape = False

                        success_count = 0
                        errors = []

                        db_manager.set_status(profile_name, "Posting to Fanpage" if not only_scrape else "Testing Posting to Fanpage")
                        for idx, url in enumerate(urls):
                            is_last = (idx == len(urls) - 1)
                            if only_scrape:
                                p_log(profile_name, f"[{profile_name}] 🧪 [TEST MODE] Đang upload thử nghiệm lên Fanpage {idx+1}/{len(urls)}: {url} (KHÔNG ĐĂNG THẬT)")
                            else:
                                p_log(profile_name, f"[{profile_name}] Dang dang bai len Fanpage {idx+1}/{len(urls)}: {url}")
                            
                            try:
                                poster = social_poster.SocialPoster(context, url)
                                # Nếu only_scrape là True thì truyền publish=False
                                success = poster.post_to_fanpage(profile_name, txt_path, img_path, cleanup=False, publish=(not only_scrape))
                                if success:
                                    success_count += 1
                                    if only_scrape:
                                        p_log(profile_name, f"[{profile_name}] 🧪 [TEST MODE] Đã tải lên và điền status thử nghiệm thành công lên Fanpage {idx+1}/{len(urls)}")
                                    else:
                                        p_log(profile_name, f"[{profile_name}] Dang thanh cong len Fanpage {idx+1}/{len(urls)}")
                                    
                                    # CHẠY ĐẾN ĐÂU LƯU ĐẾN ĐÂY: Lưu ngay khi bài viết đã được đăng/upload thử nghiệm thành công
                                    db_manager.mark_post_processed(profile_name, platform, post_id)
                                    try:
                                        saved_fp = content_deduplicator.compute_fingerprints(caption, img_path if img_path and img_path != temp_media_path else temp_media_path, media_type)
                                        db_manager.save_content_fingerprint(
                                            profile_name, platform, post_id,
                                            saved_fp["text_simhash"],
                                            saved_fp["media_hash"],
                                            saved_fp["media_type"]
                                        )
                                    except Exception as fp_err:
                                        p_log(profile_name, f"[{profile_name}] Canh bao: Khong the luu fingerprint ({fp_err}).")
                                    
                                    if not is_last:
                                        time.sleep(5)
                            except Exception as pe:
                                err_msg = f"Loi dang Fanpage {url}: {pe}"
                                p_log(profile_name, f"[{profile_name}] {err_msg}")
                                errors.append(err_msg)
                                
                        # Cleanup
                        try:
                            temp_poster = social_poster.SocialPoster(context, "")
                            temp_poster._cleanup_output_files(profile_name, txt_path, img_path)
                        except Exception as cl_err:
                            p_log(profile_name, f"[{profile_name}] Loi khi don dep file output: {cl_err}")
                            
                        if temp_media_path and os.path.exists(temp_media_path):
                            try: os.remove(temp_media_path)
                            except: pass
                            
                        if success_count > 0:
                            post_success = True
                            p_log(profile_name, f"[{profile_name}] Da reup thanh cong bai viet {post_id} cua {platform.upper()}")
                            processed_count += 1
                        else:
                            if errors:
                                raise Exception("Dang bai that bai tren tat ca Fanpage: " + " | ".join(errors))
                    finally:
                        if lock_acquired:
                            release_fb_lock()
                            
                # Sleep briefly
                time.sleep(5)
                
            p_log(profile_name, f"[{profile_name}] Hoan thanh vong quet. Da reup {processed_count} bai viet.")
            context.close()
    except Exception as e:
        err_msg = str(e)
        if "free plan limit" in err_msg.lower() or "limit resets" in err_msg.lower():
            search_area = err_msg
            match_resets = re.search(r'resets?\s+in\s+(.*)', err_msg, re.IGNORECASE)
            if match_resets:
                search_area = match_resets.group(1)
                
            hours = 0
            minutes = 0
            seconds = 0
            
            h_match = re.search(r'(\d+)\s*(?:hours?|h\b)', search_area, re.IGNORECASE)
            if h_match:
                hours = int(h_match.group(1))
                
            m_match = re.search(r'(\d+)\s*(?:minutes?|mins?|m\b)', search_area, re.IGNORECASE)
            if m_match:
                minutes = int(m_match.group(1))
                
            s_match = re.search(r'(\d+)\s*(?:seconds?|secs?|s\b)', search_area, re.IGNORECASE)
            if s_match:
                seconds = int(s_match.group(1))
                
            if hours > 0 or minutes > 0 or seconds > 0:
                wait_seconds = (hours * 3600 + minutes * 60 + seconds) + 10 * 60
            else:
                wait_seconds = 24 * 3600 + 10 * 60
                
            p_log(profile_name, f"[{profile_name}] Loi het han GPT: {err_msg} -> Tu dong nghi cho thu lai trong {wait_seconds}s.")
            
            try:
                p_cfg = db_manager.get_profile_config(profile_name)
                p_cfg["gpt_retry_wait_seconds"] = wait_seconds
                db_manager.save_profile_config(profile_name, p_cfg)
            except Exception as save_err:
                pass
                
            db_manager.set_status(profile_name, "Cho thu lai (Het han GPT)")
            sys.exit(3)

        if "policy_violation" in err_msg.lower() or "violate" in err_msg.lower() or "guardrails" in err_msg.lower() or "content policies" in err_msg.lower():
            p_log(profile_name, f"[{profile_name}] Loi Policy: {err_msg} -> Tu dong nghi 10s.")
            db_manager.set_status(profile_name, "Loi Policy (Thu lai sau 10s)")
            sys.exit(2)
            
        if "Target page, context or browser has been closed" in err_msg or "Execution context was destroyed" in err_msg or "Timeout" in err_msg:
            p_log(profile_name, f"[{profile_name}] Loi Trinh duyet Crash/Timeout: {err_msg} -> Tu dong nghi 10s.")
            db_manager.set_status(profile_name, "Loi Browser/Timeout (Thu lai sau 10s)")
            sys.exit(2)

        if "tat ca cac nguon ai deu that bai" in err_msg.lower() or "khong tao duoc anh/text" in err_msg.lower():
            p_log(profile_name, f"[{profile_name}] AI that bai: {err_msg[:200]} -> Tu dong nghi 10s.")
            db_manager.set_status(profile_name, "AI that bai (Thu lai sau 10s)")
            sys.exit(2)
            
        bug_tracker.log_bug(
            feature="worker_process",
            step="main",
            exc=e,
            context={"profile_name": profile_name}
        )
            
        p_log(profile_name, f"[{profile_name}] Loi Runtime: {err_msg} -> Tu dong nghi 10s.")
        db_manager.set_status(profile_name, f"Loi: {err_msg[:60]} (Thu lai sau 10s)")
        sys.exit(2)
        
    db_manager.set_status(profile_name, "Completed Task")
    sys.exit(0)

if __name__ == "__main__":
    try:
        if len(sys.argv) > 2:
            profile_name = sys.argv[1]
            current_loop = int(sys.argv[2])
            manual_platform = None
            manual_post_id = None
            if len(sys.argv) > 5 and sys.argv[3] == "--manual":
                manual_platform = sys.argv[4]
                manual_post_id = sys.argv[5]
            bypass_ai = "--bypass-ai" in sys.argv
            main(profile_name, current_loop, manual_platform, manual_post_id, bypass_ai)
        else:
            print("Usage: python worker_process.py <Profile_Name> <Current_Loop> [--manual <platform> <post_id>] [--bypass-ai]")
            sys.exit(1)
    except Exception as e:
        import traceback
        print("\n" + "="*50)
        print("CRASH ERROR:")
        print(traceback.format_exc())
        print("="*50)
        sys.exit(1)
