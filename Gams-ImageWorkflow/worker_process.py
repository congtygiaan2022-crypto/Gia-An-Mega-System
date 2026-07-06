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

def get_totp_code(secret: str) -> str:
    try:
        secret = secret.replace(" ", "").replace("-", "").upper()
        # Thêm padding nếu thiếu chiều dài base32
        missing_padding = len(secret) % 8
        if missing_padding:
            secret += '=' * (8 - missing_padding)
        totp = pyotp.TOTP(secret)
        return totp.now()
    except Exception as e:
        print(f"Lỗi sinh mã 2FA: {e}")
        return ""

def check_is_logged_in_playwright(page) -> bool:
    try:
        url = page.url
        if "facebook.com" not in url or "login" in url or "checkpoint" in url or "two_step" in url:
            return False
        
        # Một số selector đặc trưng khi đã đăng nhập thành công
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

def check_and_login_facebook_playwright(context, profile_name, fb_account_str) -> bool:
    # Phân tích UID|Pass|2FA|Mail
    parts = [p.strip() for p in fb_account_str.split('|')]
    uid = parts[0] if len(parts) > 0 else ""
    password = parts[1] if len(parts) > 1 else ""
    two_factor_secret = parts[2] if len(parts) > 2 else ""
    mail = parts[3] if len(parts) > 3 else ""
    
    if not uid or not password:
        db_manager.log_msg(profile_name, f"[{profile_name}] Thiếu UID hoặc Mật khẩu Facebook trong cấu hình.")
        return False

    page = context.new_page()
    try:
        # Bước 1: Vào trang chủ kiểm tra xem có session cũ không
        db_manager.log_msg(profile_name, f"[{profile_name}] Đang kiểm tra session Facebook đã lưu...")
        page.goto("https://www.facebook.com/", timeout=45000)
        page.wait_for_timeout(3000)
        
        if check_is_logged_in_playwright(page):
            db_manager.log_msg(profile_name, f"[{profile_name}] Đăng nhập thành công từ session đã lưu (bỏ qua bước đăng nhập).")
            return True
            
        # Thử kiểm tra qua business.facebook.com
        try:
            page.goto("https://business.facebook.com/latest/home", timeout=45000)
            page.wait_for_timeout(4000)
            if "login" not in page.url and ("business.facebook.com" in page.url or page.locator(".meta-business-suite").first.is_visible() or "latest/home" in page.url):
                db_manager.log_msg(profile_name, f"[{profile_name}] Đăng nhập thành công từ session đã lưu (xác minh qua Business Suite).")
                return True
        except Exception:
            pass

        # Bước 2: Chưa đăng nhập, đi tới trang login
        db_manager.log_msg(profile_name, f"[{profile_name}] Phát hiện chưa đăng nhập. Đang truy cập trang đăng nhập Facebook...")
        page.goto("https://www.facebook.com/login", timeout=45000)
        page.wait_for_timeout(2000)
        
        # Đảm bảo các trường email và pass hiển thị
        page.wait_for_selector("input[name='email']", timeout=15000)
        page.fill("input[name='email']", uid)
        page.fill("input[name='pass']", password)
        page.wait_for_timeout(1000)
        page.keyboard.press("Enter")
        
        # Đợi 5 giây xem có chuyển hướng hoặc chuyển trang không
        page.wait_for_timeout(5000)
        
        # Bước 3: Kiểm tra CAPTCHA
        captcha_wait = 0
        while captcha_wait < 120:
            if "login" not in page.url:
                break
            try:
                recaptcha = page.locator("//iframe[contains(@src,'recaptcha') or contains(@title,'reCAPTCHA')]")
                if recaptcha.first.is_visible():
                    if captcha_wait == 0:
                        db_manager.log_msg(profile_name, f"[{profile_name}] ⚠️ PHÁT HIỆN CAPTCHA FACEBOOK. Hãy giải thủ công trên cửa sổ Chrome trong 120 giây...")
                    page.wait_for_timeout(5000)
                    captcha_wait += 5
                    continue
            except Exception:
                pass
            break
            
        # Bước 4: Kiểm tra checkpoint / 2FA
        is_2fa_page = False
        for _ in range(15):
            url = page.url
            if "checkpoint" in url or "two_step" in url or "confirm" in url or page.locator("input#approvals_code").first.is_visible() or page.locator("input[autocomplete='one-time-code']").first.is_visible():
                is_2fa_page = True
                break
            page.wait_for_timeout(1000)

        if is_2fa_page:
            p_log(profile_name, f"[{profile_name}] Phát hiện màn hình xác thực 2FA của Facebook...")
            
            # Chụp ảnh màn hình 2FA để debug
            try:
                os.makedirs("scratch", exist_ok=True)
                page.screenshot(path=f"scratch/fb_2fa_{profile_name}.png")
                p_log(profile_name, f"[{profile_name}] Đã chụp ảnh màn hình 2FA tại scratch/fb_2fa_{profile_name}.png")
            except Exception as ss_err:
                p_log(profile_name, f"[{profile_name}] Không thể chụp ảnh màn hình 2FA: {ss_err}")

            if not two_factor_secret:
                p_log(profile_name, f"[{profile_name}] ❌ LỖI: Yêu cầu 2FA nhưng cấu hình không có Secret Key 2FA.")
                return False

            # Tìm xem có sẵn ô điền OTP không
            otp_selectors = [
                "input#approvals_code",
                "input[name='approvals_code']",
                "input[autocomplete='one-time-code']",
                "input[inputmode='numeric']",
                "input[type='tel']",
                "input[type='number']",
                "input[aria-label*='digit']",
                "input[aria-label*='code']",
                "input[aria-label*='Mã']",
                "input[aria-label*='xác thực']",
                "//input[@type='text' and not(@name='email') and not(@name='pass')]"
            ]
            
            otp_field = None
            for sel in otp_selectors:
                try:
                    loc = page.locator(sel).first
                    if loc.is_visible() and loc.is_enabled():
                        otp_field = loc
                        p_log(profile_name, f"[{profile_name}] Tìm thấy ô OTP ngay lập tức.")
                        break
                except:
                    pass

            # Nếu KHÔNG có sẵn ô điền OTP (đang bị kẹt ở màn hình phê duyệt thiết bị khác)
            if not otp_field:
                p_log(profile_name, f"[{profile_name}] Chưa thấy ô nhập OTP. Đang click các bước phụ...")
                
                # Đợi và Click "Thử cách khác" nếu có
                try:
                    try_other_xpath = "//span[contains(text(),'Thử cách khác') or contains(text(),'Try another way') or contains(text(),'Use a different method')]/.. | //a[contains(text(),'Thử cách khác') or contains(text(),'Try another way')] | //div[@role='button'][contains(.,'Thử cách khác') or contains(.,'Try another way')]"
                    for _ in range(10):
                        try_other = page.locator(try_other_xpath).first
                        if try_other.is_visible():
                            try_other.click()
                            p_log(profile_name, f"[{profile_name}] Đã click 'Thử cách khác'")
                            page.wait_for_timeout(2500)
                            break
                        page.wait_for_timeout(500)
                except Exception:
                    pass
                    
                # Đợi và Chọn "Ứng dụng xác thực" nếu có
                try:
                    auth_app_xpath = "//span[contains(text(),'Ứng dụng xác thực') or contains(text(),'Authentication app') or contains(text(),'Authenticator app')]/.. | //div[@role='radio'][.//*[contains(text(),'Ứng dụng xác thực') or contains(text(),'Authentication app')]] | //label[.//*[contains(text(),'Ứng dụng xác thực') or contains(text(),'Authentication app')]]"
                    for _ in range(10):
                        auth_app = page.locator(auth_app_xpath).first
                        if auth_app.is_visible():
                            auth_app.click()
                            p_log(profile_name, f"[{profile_name}] Đã chọn 'Ứng dụng xác thực'")
                            page.wait_for_timeout(1000)
                            
                            continue_xpath = "//span[contains(text(),'Tiếp tục') or contains(text(),'Continue')]/.. | //button[contains(text(),'Tiếp tục') or contains(text(),'Continue')] | //div[@role='button'][.//*[contains(text(),'Tiếp tục') or contains(text(),'Continue')]]"
                            continue_btn = page.locator(continue_xpath).first
                            if continue_btn.is_visible():
                                continue_btn.click()
                                p_log(profile_name, f"[{profile_name}] Đã click 'Tiếp tục' sau khi chọn App xác thực")
                                page.wait_for_timeout(3000)
                            break
                        page.wait_for_timeout(500)
                except Exception:
                    pass

                # Tìm lại ô OTP sau khi click các bước phụ
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
                    p_log(profile_name, f"[{profile_name}] ❌ Không sinh được mã OTP từ Secret Key 2FA.")
                    return False
                    
                p_log(profile_name, f"[{profile_name}] Đã sinh mã OTP: {code}. Đang nhập...")
                try:
                    # Tập trung vào ô input bằng cách click trước
                    otp_field.click()
                    page.wait_for_timeout(500)
                    otp_field.fill("")
                    page.wait_for_timeout(1000)
                    page.keyboard.type(code)
                    page.wait_for_timeout(1000)
                    page.keyboard.press("Enter") # Gửi mã sớm bằng Enter
                    p_log(profile_name, f"[{profile_name}] Đã gõ mã OTP và nhấn Enter.")
                except Exception as fill_err:
                    p_log(profile_name, f"[{profile_name}] Cảnh báo lỗi fill OTP: {fill_err}, thử type trực tiếp...")
                    try:
                        page.keyboard.type(code)
                        page.keyboard.press("Enter")
                    except:
                        pass
                
                # Tìm nút gửi mã (submit)
                submit_selectors = [
                    "button#checkpointSubmitButton",
                    "button[type='submit']",
                    "//button[contains(.,'Tiếp tục') or contains(.,'Continue') or contains(.,'Submit')]",
                    "//span[text()='Tiếp tục' or text()='Continue' or text()='Submit']/..",
                    "input[type='submit']" # Đưa xuống cuối cùng
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
                    p_log(profile_name, f"[{profile_name}] Đang click nút Tiếp tục 2FA...")
                    try:
                        submit_btn.click(force=True, timeout=5000)
                    except Exception as click_err:
                        p_log(profile_name, f"[{profile_name}] Click thường lỗi ({click_err}), thử click bằng JS...")
                        try:
                            page.evaluate("el => el.click()", submit_btn.element_handle())
                        except Exception as js_err:
                            p_log(profile_name, f"[{profile_name}] Click JS lỗi ({js_err}), gửi Enter lần nữa...")
                            page.keyboard.press("Enter")
                else:
                    p_log(profile_name, f"[{profile_name}] Không tìm thấy nút Tiếp tục cụ thể, dựa vào phím Enter đã nhấn.")
                
                p_log(profile_name, f"[{profile_name}] Đã gửi mã OTP. Đang chờ chuyển hướng...")
                page.wait_for_timeout(8000)
            else:
                p_log(profile_name, f"[{profile_name}] ❌ Không tìm thấy ô nhập mã 2FA trên trang sau 15 giây.")
                # Chụp thêm ảnh màn hình lỗi
                try:
                    page.screenshot(path=f"scratch/fb_2fa_error_{profile_name}.png")
                    p_log(profile_name, f"[{profile_name}] Đã chụp ảnh lỗi 2FA tại scratch/fb_2fa_error_{profile_name}.png")
                except:
                    pass
                return False

        # Bước 5: Xác nhận kết quả đăng nhập
        p_log(profile_name, f"[{profile_name}] Đang truy cập facebook.com để xác nhận trạng thái login...")
        page.goto("https://www.facebook.com/", timeout=45000)
        page.wait_for_timeout(5000)
        
        if check_is_logged_in_playwright(page):
            p_log(profile_name, f"[{profile_name}] Đăng nhập Facebook thành công.")
            return True
            
        try:
            p_log(profile_name, f"[{profile_name}] Kiểm tra qua Business Suite...")
            page.goto("https://business.facebook.com/latest/home", timeout=45000)
            page.wait_for_timeout(5000)
            if "login" not in page.url and ("business.facebook.com" in page.url or page.locator(".meta-business-suite").first.is_visible() or "latest/home" in page.url):
                p_log(profile_name, f"[{profile_name}] Đăng nhập Facebook thành công (xác minh qua Business Suite).")
                return True
        except Exception as bus_err:
            p_log(profile_name, f"[{profile_name}] Lỗi khi kiểm tra qua Business Suite: {bus_err}")
            
        p_log(profile_name, f"[{profile_name}] Đăng nhập thất bại (vẫn ở màn hình đăng nhập hoặc checkpoint).")
        # Chụp ảnh kết quả thất bại
        try:
            page.screenshot(path=f"scratch/fb_login_fail_{profile_name}.png")
            p_log(profile_name, f"[{profile_name}] Đã chụp ảnh lỗi đăng nhập thất bại tại scratch/fb_login_fail_{profile_name}.png")
        except:
            pass
        return False
    except Exception as e:
        db_manager.log_msg(profile_name, f"[{profile_name}] Lỗi xảy ra khi đăng nhập Facebook: {e}")
        return False
    finally:
        try:
            page.close()
        except:
            pass

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

    # CHECK & LOGIN FACEBOOK IF CONFIGURED BEFORE TASKS
    use_fb_global = global_cfg.get("apply_fb_global", False)
    if use_fb_global:
        fb_account = global_cfg.get("global_facebook_account", "").strip()
        p_log(profile_name, f"[{profile_name}] Sử dụng cấu hình tài khoản Facebook chung của hệ thống.")
    else:
        fb_account = profile_cfg.get("facebook_account", "").strip()
        p_log(profile_name, f"[{profile_name}] Sử dụng cấu hình tài khoản Facebook riêng của Profile.")

    if fb_account:
        p_log(profile_name, f"[{profile_name}] Bắt đầu kiểm tra trạng thái đăng nhập Facebook...")
        db_manager.set_status(profile_name, "Checking FB Login")
        try:
            with sync_playwright() as p:
                pm = profile_manager.ProfileManager(config.get("profiles_dir", "profiles"))
                context = pm.launch_browser_for_profile(p, profile_name, headless=config.get("headless_mode", False))
                fb_login_success = check_and_login_facebook_playwright(context, profile_name, fb_account)
                context.close()
                
            if fb_login_success:
                p_log(profile_name, f"[{profile_name}] Trạng thái đăng nhập Facebook: OK")
            else:
                p_log(profile_name, f"[{profile_name}] Cảnh báo: Tự động đăng nhập Facebook thất bại.")
        except Exception as fb_err:
            p_log(profile_name, f"[{profile_name}] Lỗi trong tiến trình kiểm tra đăng nhập Facebook: {fb_err}")

    images = [os.path.join(input_img_dir, f) for f in os.listdir(input_img_dir) if os.path.isfile(os.path.join(input_img_dir, f))]
    if not images:
        err_msg = f"[{profile_name}] LỖI: Thư mục ảnh ({input_img_dir}) trống! Không có ảnh đầu vào."
        p_log(profile_name, err_msg)
        db_manager.set_status(profile_name, "Missing Input Images")
        sys.exit(1)
        
    input_img = random.choice(images)
    
    txt_path, img_path = None, None
    attempt = 0
    max_attempts = 3
    
    try:
        while attempt < max_attempts:
            attempt += 1
            try:
                db_manager.set_status(profile_name, f"Generating Content (Lượt {attempt})")
                p_log(profile_name, f"[{profile_name}] Khởi động trình duyệt tạo nội dung AI (Lượt {attempt})...")
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
                # Thành công thì thoát khỏi vòng lặp thử lại
                break
                
            except Exception as e:
                err_msg = str(e)
                is_limit = "free plan limit" in err_msg.lower() or "limit resets" in err_msg.lower()
                is_not_logged_in = "chatgpt_not_logged_in" in err_msg.lower() or "please log in" in err_msg.lower() or "need to be logged in" in err_msg.lower() or "log in to use" in err_msg.lower()
                
                # Đọc cấu hình gpt_limit_action theo nút bật/tắt áp dụng cho tất cả profile
                use_global_limit = global_cfg.get("apply_gpt_limit_global", True)
                if use_global_limit:
                    limit_action = global_cfg.get("gpt_limit_action", "wait_limit")
                else:
                    limit_action = profile_cfg.get("gpt_limit_action")
                    if not limit_action:
                        limit_action = global_cfg.get("gpt_limit_action", "wait_limit")
                    
                should_register = is_not_logged_in or (is_limit and limit_action == "change_account")
                if should_register and attempt < max_attempts:
                    reason = "chưa đăng nhập GPT" if is_not_logged_in else "limit GPT"
                    p_log(profile_name, f"[{profile_name}] Phát hiện {reason} -> Đang khởi chạy tự động tạo tài khoản mới để tiếp tục...")
                    db_manager.set_status(profile_name, "Đang đổi tài khoản GPT")
                    
                    # Gọi script gpt_register.py và đợi cho đến khi hoàn thành
                    import subprocess
                    try:
                        subprocess.run(
                            [sys.executable, "-u", "gpt_register.py", profile_name, "--auto"],
                            cwd=os.getcwd(),
                            check=True
                        )
                        p_log(profile_name, f"[{profile_name}] Đã đổi tài khoản mới xong. Đang thử lại lượt {attempt + 1}...")
                        continue
                    except Exception as reg_err:
                        p_log(profile_name, f"[{profile_name}] Lỗi khi chạy kịch bản đổi tài khoản: {reg_err}")
                        raise e
                else:
                    # Nếu không phải lỗi limit hoặc cấu hình không đổi tài khoản, hoặc quá số lượt thử
                    raise e
        
        # 2. Posting
        if txt_path and img_path:
            db_manager.set_status(profile_name, "Posting to Fanpage")
            
            # Phân tách các link Fanpage theo dòng hoặc dấu phẩy và loại bỏ trùng lặp qua Asset ID
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
                else:
                    p_log(profile_name, f"[{profile_name}] Bỏ qua link Fanpage trùng lặp Asset ID / Định danh ({identifier}): {u}")
                
            p_log(profile_name, f"[{profile_name}] Khởi động trình duyệt đăng bài Fanpage ({len(urls)} trang)...")
            context = None
            try:
                with sync_playwright() as p:
                    pm = profile_manager.ProfileManager(config.get("profiles_dir", "profiles"))
                    context = pm.launch_browser_for_profile(p, profile_name, headless=config.get("headless_mode", False))
                    
                    success_count = 0
                    errors = []
                    for idx, url in enumerate(urls):
                        is_last = (idx == len(urls) - 1)
                        p_log(profile_name, f"[{profile_name}] Đang đăng bài lên Fanpage {idx+1}/{len(urls)}: {url}")
                        db_manager.set_status(profile_name, f"Posting {idx+1}/{len(urls)}")
                        
                        try:
                            poster = social_poster.SocialPoster(context, url)
                            # Đặt cleanup=False để không xóa file tạm giữa chừng
                            success = poster.post_to_fanpage(profile_name, txt_path, img_path, cleanup=False)
                            if success:
                                success_count += 1
                                p_log(profile_name, f"[{profile_name}] ✅ Đăng bài thành công lên Fanpage {idx+1}/{len(urls)}")
                                try:
                                    post_id = os.path.splitext(os.path.basename(txt_path))[0] if txt_path else f"Post_{int(time.time())}"
                                    db_manager.mark_post_processed(profile_name, 'facebook', post_id)
                                except Exception as db_err:
                                    p_log(profile_name, f"[{profile_name}] Cảnh báo: Lỗi khi lưu lịch sử đăng vào DB: {db_err}")
                                if not is_last:
                                    p_log(profile_name, f"[{profile_name}] Chờ 5 giây trước khi đăng trang tiếp theo...")
                                    time.sleep(5)
                        except Exception as pe:
                            err_msg = f"Lỗi đăng Fanpage {url}: {pe}"
                            p_log(profile_name, f"[{profile_name}] {err_msg}")
                            errors.append(err_msg)
                    
                    # Dọn dẹp file output sau khi đã hoàn thành thử tất cả các trang
                    if success_count > 0 or not errors:
                        p_log(profile_name, f"[{profile_name}] Đang dọn dẹp các file output tạm sau khi hoàn tất đăng...")
                        try:
                            temp_poster = social_poster.SocialPoster(context, "")
                            temp_poster._cleanup_output_files(profile_name, txt_path, img_path)
                        except Exception as cl_err:
                            p_log(profile_name, f"[{profile_name}] Lỗi khi dọn dẹp file: {cl_err}")
                    
                    if errors:
                        if success_count == 0:
                            # Nếu tất cả các trang đều lỗi, ném ngoại lệ để retry
                            raise Exception(" | ".join(errors))
                        else:
                            p_log(profile_name, f"[{profile_name}] Cảnh báo: Có {len(errors)}/{len(urls)} Fanpage lỗi khi đăng bài, nhưng có {success_count} trang thành công nên bỏ qua retry.")
                    
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
            # Parse wait time from error message
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
                # Add 10 minutes buffer (600 seconds)
                wait_seconds = (hours * 3600 + minutes * 60 + seconds) + 10 * 60
            else:
                # Default fallback (24 hours + 10 minutes)
                wait_seconds = 24 * 3600 + 10 * 60
                
            p_log(profile_name, f"[{profile_name}] Lỗi hết hạn GPT: {err_msg} -> Tự động chuyển sang nghỉ chờ thử lại trong {wait_seconds} giây.")
            
            try:
                p_cfg = db_manager.get_profile_config(profile_name)
                p_cfg["gpt_retry_wait_seconds"] = wait_seconds
                db_manager.save_profile_config(profile_name, p_cfg)
            except Exception as save_err:
                p_log(profile_name, f"[{profile_name}] Lỗi khi lưu gpt_retry_wait_seconds vào config: {save_err}")
                
            db_manager.set_status(profile_name, "Chờ thử lại (Hết hạn GPT)")
            sys.exit(3)

        if "policy_violation" in err_msg.lower() or "violate" in err_msg.lower() or "guardrails" in err_msg.lower() or "content policies" in err_msg.lower():
            p_log(profile_name, f"[{profile_name}] Lỗi Policy: {err_msg} -> Tự động chuyển sang nghỉ 10s chờ chạy lại vòng này.")
            db_manager.set_status(profile_name, "Lỗi Policy (Thử lại sau 10s)")
            sys.exit(2)
            
        if "Target page, context or browser has been closed" in err_msg or "Execution context was destroyed" in err_msg or "Timeout" in err_msg:
            p_log(profile_name, f"[{profile_name}] Lỗi Trình duyệt Crash/Timeout: {err_msg} -> Hệ thống sẽ tự động chạy lại vòng này.")
            db_manager.set_status(profile_name, "Lỗi Browser/Timeout (Thử lại sau 10s)")
            sys.exit(2)

        if "tất cả các nguồn ai đều thất bại" in err_msg.lower() or "không tạo được ảnh/text" in err_msg.lower():
            p_log(profile_name, f"[{profile_name}] Tất cả nguồn AI thất bại: {err_msg[:200]} -> Tự động thử lại vòng này sau 10s.")
            db_manager.set_status(profile_name, "AI thất bại (Thử lại sau 10s)")
            sys.exit(2)
            
        # BUG TRACKER: Ghi lại lỗi cấu trúc thông qua bug_tracker
        bug_tracker.log_bug(
            feature="worker_process",
            step="main",
            exc=e,
            context={"profile_name": profile_name}
        )
            
        p_log(profile_name, f"[{profile_name}] Lỗi Runtime: {err_msg} -> Hệ thống sẽ tự động chạy lại vòng này sau 10s.")
        db_manager.set_status(profile_name, f"Lỗi: {err_msg[:60]} (Thử lại sau 10s)")
        sys.exit(2)
        
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
