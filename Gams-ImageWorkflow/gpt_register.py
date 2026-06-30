import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
import time
import psutil
import os
import json
import random
import string
import re
from playwright.sync_api import sync_playwright
import db_manager

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

def generate_random_password(length=14):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(random.choice(chars) for _ in range(length))

def generate_random_birthdate():
    day = random.randint(1, 28)
    month = random.randint(1, 12)
    year = random.randint(1985, 2003) # Age 23 - 41
    return day, month, year

def find_continue_button(page):
    """
    Tìm nút Continue/Submit mà không bị nhầm sang nút mạng xã hội (Google, Apple, Microsoft, v.v.)
    """
    locators = [
        'button[type="submit"]',
        'button:has-text("Continue")',
        'button:has-text("Tiếp tục")',
        'button:has-text("Agree")',
        'button:has-text("Chấp nhận")',
        'button:has-text("Submit")',
        'button:has-text("Verify")',
        'button:has-text("Xác minh")',
        'button:has-text("Finish")',
        'button:has-text("Hoàn thành")'
    ]
    for loc in locators:
        try:
            buttons = page.locator(loc).all()
            for btn in buttons:
                if btn.is_visible():
                    txt = btn.inner_text().lower()
                    # Loại bỏ các nút mạng xã hội
                    if any(x in txt for x in ["google", "apple", "microsoft", "auth0", "facebook"]):
                        continue
                    return btn
        except:
            pass
    return None

def p_log(profile_name, msg):
    print(msg)
    try:
        db_manager.log_msg(profile_name, msg)
    except Exception:
        pass

def sleep_with_countdown(profile_name, seconds, action):
    p_log(profile_name, f"[{profile_name}] Bắt đầu chờ {seconds} giây để {action}...")
    for i in range(seconds, 0, -1):
        print(f"-> Đang chờ {i}s... để {action}", end="\r", flush=True)
        time.sleep(1)
    print(" " * 60, end="\r")  # Clear the line on console

def main(profile_name):
    cleanup_chrome(profile_name)
    p_log(profile_name, f"[{profile_name}] Bắt đầu tiến trình tạo/đổi tài khoản ChatGPT tự động...")
    
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        
    try:
        import profile_manager
        with sync_playwright() as p:
            pm = profile_manager.ProfileManager(config.get("profiles_dir", "profiles"))
            context = pm.launch_browser_for_profile(p, profile_name, headless=False)
            
            # --- TAB 1: Tạo email ảo tại 365gmail.com ---
            page_mail = context.pages[0] if context.pages else context.new_page()
            p_log(profile_name, f"[{profile_name}] Đang mở 365gmail.com để tạo email...")
            try:
                page_mail.goto("https://365gmail.com/", wait_until="commit", timeout=60000)
            except Exception as e:
                p_log(profile_name, f"[{profile_name}] Lỗi khi tải 365gmail.com: {e}")
                
            sleep_with_countdown(profile_name, 3, "tải trang 365gmail")
            # Click nút Random để sinh email mới
            try:
                page_mail.locator('#btn-random').click(timeout=10000)
                p_log(profile_name, f"[{profile_name}] Đã bấm nút tạo email Random.")
            except Exception as e:
                p_log(profile_name, f"[{profile_name}] Không tìm thấy nút #btn-random, thử tự điền...")
                
            sleep_with_countdown(profile_name, 2, "tạo email")
            
            # Lấy email đã tạo
            email = ""
            for attempt in range(10):
                email = page_mail.locator('#credentials').input_value().strip()
                if email and "@" in email:
                    break
                time.sleep(1)
                
            if not email or "@" not in email:
                p_log(profile_name, f"[{profile_name}] ❌ Không thể tạo email ngẫu nhiên từ 365gmail.com!")
                context.close()
                return
                
            p_log(profile_name, f"[{profile_name}] ✅ Tạo thành công email: {email}")
            
            # --- TAB 2: Đăng ký ChatGPT ---
            page_gpt = context.new_page()
            p_log(profile_name, f"[{profile_name}] Đang mở ChatGPT (https://chatgpt.com/)...")
            try:
                page_gpt.goto("https://chatgpt.com/", wait_until="commit", timeout=60000)
            except Exception as e:
                p_log(profile_name, f"[{profile_name}] Lỗi truy cập chatgpt.com: {e}")
                
            sleep_with_countdown(profile_name, 5, "tải trang ChatGPT")
            
            # Kiểm tra xem có đang đăng nhập sẵn tài khoản nào không
            is_logged_in = False
            if page_gpt.locator('#prompt-textarea').count() > 0 and page_gpt.locator('#prompt-textarea').is_visible():
                is_logged_in = True
            elif page_gpt.locator('div[data-testid="profile-button"]').count() > 0 and page_gpt.locator('div[data-testid="profile-button"]').is_visible():
                is_logged_in = True
            elif page_gpt.locator('button:has-text("Log in"), button:has-text("Sign up"), button:has-text("Đăng nhập"), button:has-text("Đăng ký")').count() == 0:
                is_logged_in = True
                
            if is_logged_in:
                p_log(profile_name, f"[{profile_name}] Phát hiện tài khoản GPT cũ đang đăng nhập. Tiến hành đăng xuất...")
                try:
                    context.clear_cookies()
                    page_gpt.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
                    page_gpt.goto("https://chatgpt.com/")
                    sleep_with_countdown(profile_name, 5, "đăng xuất tài khoản cũ")
                    p_log(profile_name, f"[{profile_name}] Đã đăng xuất thành công!")
                except Exception as e:
                    p_log(profile_name, f"[{profile_name}] Lỗi khi đăng xuất: {e}")
            
            # Tìm nút Đăng ký (Sign up)
            p_log(profile_name, f"[{profile_name}] Đang bấm đăng ký tài khoản GPT mới...")
            signup_clicked = False
            try:
                signup_btn = page_gpt.locator('button:has-text("Sign up"), a:has-text("Sign up"), button:has-text("Đăng ký"), a:has-text("Đăng ký")').first
                if signup_btn.count() > 0 and signup_btn.is_visible():
                    signup_btn.click()
                    signup_clicked = True
                    p_log(profile_name, f"[{profile_name}] Đã click nút Đăng ký trên trang chủ.")
            except:
                pass
                
            if not signup_clicked:
                p_log(profile_name, f"[{profile_name}] Chuyển hướng trực tiếp tới trang đăng ký...")
                page_gpt.goto("https://chatgpt.com/auth/login?screen_hint=signup")
                
            sleep_with_countdown(profile_name, 5, "tải trang đăng ký")
            
            # Chờ ô nhập email xuất hiện
            email_input = None
            for _ in range(30):
                for sel in ['input[type="email"]', 'input#email', 'input[name="email"]', 'input[name="username"]']:
                    try:
                        loc = page_gpt.locator(sel).first
                        if loc.count() > 0 and loc.is_visible():
                            email_input = loc
                            break
                    except:
                        pass
                if email_input:
                    break
                time.sleep(1)
                
            if not email_input:
                p_log(profile_name, f"[{profile_name}] ❌ Không tìm thấy ô nhập email trên trang đăng ký!")
                p_log(profile_name, f"[{profile_name}] Vui lòng tự tương tác trên trình duyệt. Tiến trình sẽ chờ...")
                email_input = page_gpt.locator('input[type="email"], input#email, input[name="username"]').first
                try:
                    email_input.wait_for(timeout=60000)
                except:
                    pass
            
            if email_input:
                email_input.fill(email)
                time.sleep(1)
                
                # Bấm Continue
                try:
                    continue_btn = find_continue_button(page_gpt)
                    if continue_btn:
                        continue_btn.click()
                        p_log(profile_name, f"[{profile_name}] Đã điền email và bấm Tiếp tục.")
                    else:
                        p_log(profile_name, f"[{profile_name}] Warning: Không tìm thấy nút Tiếp tục email, thử nhấn Enter.")
                        page_gpt.keyboard.press("Enter")
                except Exception as e:
                    p_log(profile_name, f"[{profile_name}] Lỗi click nút Tiếp tục: {e}")
                    
            sleep_with_countdown(profile_name, 3, "tải ô nhập mật khẩu")
            
            # Chờ và nhập mật khẩu
            password_input = None
            for _ in range(15):
                for sel in ['input[type="password"]', 'input#password', 'input[name="password"]']:
                    try:
                        loc = page_gpt.locator(sel).first
                        if loc.count() > 0 and loc.is_visible():
                            password_input = loc
                            break
                    except:
                        pass
                if password_input:
                    break
                time.sleep(1)
                
            password = generate_random_password()
            if password_input:
                password_input.fill(password)
                time.sleep(1)
                
                # Bấm Continue
                try:
                    continue_btn = find_continue_button(page_gpt)
                    if continue_btn:
                        continue_btn.click()
                        p_log(profile_name, f"[{profile_name}] Đã điền mật khẩu và bấm Tiếp tục.")
                    else:
                        p_log(profile_name, f"[{profile_name}] Warning: Không tìm thấy nút Tiếp tục mật khẩu, thử nhấn Enter.")
                        page_gpt.keyboard.press("Enter")
                except Exception as e:
                    p_log(profile_name, f"[{profile_name}] Lỗi click nút Tiếp tục mật khẩu: {e}")
            else:
                p_log(profile_name, f"[{profile_name}] Warning: Không thấy ô nhập mật khẩu. Có thể trang web yêu cầu CAPTCHA trước.")
                
            # Lưu tài khoản tạm thời để người dùng không bị mất
            acc_dir = os.path.join("profiles", profile_name)
            os.makedirs(acc_dir, exist_ok=True)
            acc_file = os.path.join(acc_dir, "gpt_account.txt")
            with open(acc_file, "w", encoding="utf-8") as f:
                f.write(f"Email: {email}\nPassword: {password}\nCreated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            p_log(profile_name, f"[{profile_name}] 📝 Đã lưu tài khoản vào file: {acc_file}")
            
            # --- Chờ mã xác minh ---
            p_log(profile_name, f"[{profile_name}] ⚠️ CHÚ Ý: Nếu gặp CAPTCHA/Cloudflare, hãy GIẢI THỦ CÔNG trên trình duyệt!")
            p_log(profile_name, f"[{profile_name}] Đang chờ màn hình nhập mã xác minh email (OTP)...")
            
            code_input = None
            for i in range(120): # Chờ tối đa 2 phút
                locators = [
                    'input[inputmode="numeric"]',
                    'input[placeholder*="code"]',
                    'input[name*="code"]',
                    'input[placeholder="XXXXXX"]',
                    'input[placeholder="xxxxxx"]'
                ]
                for loc in locators:
                    try:
                        candidate = page_gpt.locator(loc).first
                        if candidate.count() > 0 and candidate.is_visible():
                            code_input = candidate
                            break
                    except:
                        pass
                if code_input:
                    break
                if page_gpt.locator('#prompt-textarea').count() > 0 and page_gpt.locator('#prompt-textarea').is_visible():
                    break
                time.sleep(1)
                
            if page_gpt.locator('#prompt-textarea').count() > 0 and page_gpt.locator('#prompt-textarea').is_visible():
                p_log(profile_name, f"[{profile_name}] Đã bỏ qua bước xác minh email và vào thẳng ChatGPT.")
            elif not code_input:
                p_log(profile_name, f"[{profile_name}] ❌ Không phát hiện ô nhập mã xác minh. Hãy tự điền mã nếu có.")
            else:
                p_log(profile_name, f"[{profile_name}] Đã phát hiện ô nhập mã xác minh. Tiến hành kiểm tra hòm thư...")
                
                # Poll kiểm tra email từ 365gmail.com
                code = None
                for check_attempt in range(24): # Kiểm tra mỗi 5s, tổng cộng 2 phút
                    try:
                        page_mail.locator('#email-form button[type="submit"]').click()
                        time.sleep(3)
                        
                        li_elements = page_mail.locator('#email-list li').all()
                        for li in li_elements:
                            text = li.inner_text()
                            if "openai" in text.lower() or "chatgpt" in text.lower() or "verification" in text.lower() or "verify" in text.lower() or "code" in text.lower() or "xác minh" in text.lower():
                                li.click()
                                time.sleep(2)
                                
                                content = page_mail.locator('#email-content').inner_text()
                                matches = re.findall(r'\b\d{6}\b', content)
                                if matches:
                                    code = matches[0]
                                    p_log(profile_name, f"[{profile_name}] 📬 Tìm thấy mã xác minh OpenAI: {code}")
                                    break
                    except Exception as e:
                        pass
                        
                    if code:
                        break
                    p_log(profile_name, f"[{profile_name}] Chưa thấy mail xác minh, đang thử lại... (lượt {check_attempt+1}/24)")
                    time.sleep(2)
                    
                if code:
                    page_gpt.bring_to_front()
                    code_input.focus()
                    time.sleep(0.5)
                    page_gpt.keyboard.type(code, delay=100)
                    p_log(profile_name, f"[{profile_name}] Đã điền mã xác minh {code} thành công.")
                    time.sleep(2)
                    
                    try:
                        verify_btn = find_continue_button(page_gpt)
                        if verify_btn:
                            verify_btn.click()
                            p_log(profile_name, f"[{profile_name}] Đã bấm nút Tiếp tục xác nhận mã.")
                        else:
                            page_gpt.keyboard.press("Enter")
                            p_log(profile_name, f"[{profile_name}] Không thấy nút Tiếp tục mã, đã gửi phím Enter.")
                    except Exception as e:
                        p_log(profile_name, f"[{profile_name}] Lỗi khi xác nhận mã: {e}")
                        
                    sleep_with_countdown(profile_name, 5, "xác nhận mã OTP")
                else:
                    p_log(profile_name, f"[{profile_name}] ❌ Không tìm thấy mã xác minh từ 365gmail.com trong thời gian chờ!")
                    p_log(profile_name, f"[{profile_name}] Bạn hãy lấy mã xác minh điền thủ công từ tab 365gmail.")
            
            # --- Điền thông tin cá nhân (Họ tên, Ngày sinh/Tuổi) ---
            p_log(profile_name, f"[{profile_name}] Đang chờ màn hình thiết lập thông tin cá nhân (Họ tên, Ngày sinh/Tuổi)...")
            
            visible_inputs = []
            for _ in range(45):
                try:
                    if page_gpt.locator('#prompt-textarea').count() > 0 and page_gpt.locator('#prompt-textarea').is_visible():
                        break
                except:
                    pass
                
                try:
                    all_inputs = page_gpt.locator('input').all()
                    visible_inputs = []
                    for el in all_inputs:
                        if el.is_visible():
                            t_val = el.get_attribute("type") or ""
                            if t_val.lower() != "hidden":
                                visible_inputs.append(el)
                    if len(visible_inputs) >= 2:
                        break
                except:
                    pass
                time.sleep(1)
                
            if len(visible_inputs) >= 2:
                full_name_el = None
                first_name_el = None
                last_name_el = None
                age_el = None
                birthday_el = None
                
                for el in visible_inputs:
                    try:
                        name = (el.get_attribute("name") or "").lower()
                        placeholder = (el.get_attribute("placeholder") or "").lower()
                        label_text = page_gpt.evaluate("""(el) => {
                            const label = document.querySelector('label[for="' + el.id + '"]');
                            if (label) return label.innerText;
                            let parent = el.parentElement;
                            for (let i = 0; i < 3 && parent; i++) {
                                if (parent.innerText && parent.innerText.trim()) return parent.innerText;
                                parent = parent.parentElement;
                            }
                            return '';
                        }""", el).lower()
                        
                        if "age" in name or "age" in placeholder or "age" in label_text or "tuổi" in label_text:
                            age_el = el
                        elif "birth" in name or "birth" in placeholder or "birth" in label_text or "ngày sinh" in label_text or "yyyy" in placeholder:
                            birthday_el = el
                        elif "fullname" in name or "full name" in placeholder or "full name" in label_text or "họ và tên" in label_text or "họ tên" in label_text:
                            full_name_el = el
                        elif "firstname" in name or "given_name" in name or "first name" in placeholder or "tên" in label_text:
                            first_name_el = el
                        elif "lastname" in name or "family_name" in name or "last name" in placeholder or "họ" in label_text:
                            last_name_el = el
                    except:
                        pass
                
                first_names = ["Minh", "Tuan", "Hoang", "Nam", "An", "Binh", "Chinh", "Dung", "Hai", "Hung", "Khanh", "Linh", "Phong", "Quan", "Son", "Thao", "Trang", "Viet", "Anh", "Duc"]
                last_names = ["Nguyen", "Tran", "Le", "Pham", "Huynh", "Phan", "Vu", "Vo", "Dang", "Bui", "Do", "Hoang", "Ngo", "Duong", "Ly"]
                
                random_first = random.choice(first_names)
                random_last = random.choice(last_names)
                day, month, year = generate_random_birthdate()
                random_age = random.randint(22, 38)
                
                if full_name_el:
                    p_log(profile_name, f"[{profile_name}] Điền họ và tên: {random_last} {random_first}")
                    full_name_el.fill(f"{random_last} {random_first}")
                elif first_name_el:
                    p_log(profile_name, f"[{profile_name}] Điền tên: {random_first}")
                    first_name_el.fill(random_first)
                    if last_name_el:
                        p_log(profile_name, f"[{profile_name}] Điền họ: {random_last}")
                        last_name_el.fill(random_last)
                else:
                    if len(visible_inputs) == 2:
                        full_name_el = visible_inputs[0]
                        p_log(profile_name, f"[{profile_name}] (Fallback) Điền Họ và tên vào ô 1: {random_last} {random_first}")
                        full_name_el.fill(f"{random_last} {random_first}")
                    elif len(visible_inputs) >= 3:
                        first_name_el = visible_inputs[0]
                        last_name_el = visible_inputs[1]
                        p_log(profile_name, f"[{profile_name}] (Fallback) Điền Tên: {random_first} | Họ: {random_last} vào ô 1&2")
                        first_name_el.fill(random_first)
                        last_name_el.fill(random_last)
                
                time.sleep(0.5)
                
                if age_el:
                    p_log(profile_name, f"[{profile_name}] Điền tuổi: {random_age}")
                    age_el.fill(str(random_age))
                elif birthday_el:
                    placeholder = birthday_el.get_attribute("placeholder") or ""
                    if "YYYY-MM-DD" in placeholder or "yyyy-mm-dd" in placeholder.lower():
                        birthday_str = f"{year}-{month:02d}-{day:02d}"
                    elif "DD/MM/YYYY" in placeholder or "dd/mm/yyyy" in placeholder.lower():
                        birthday_str = f"{day:02d}/{month:02d}/{year}"
                    else:
                        birthday_str = f"{month:02d}/{day:02d}/{year}"
                    p_log(profile_name, f"[{profile_name}] Điền ngày sinh: {birthday_str}")
                    birthday_el.fill(birthday_str)
                else:
                    if len(visible_inputs) == 2:
                        age_el = visible_inputs[1]
                        p_log(profile_name, f"[{profile_name}] (Fallback) Điền tuổi vào ô 2: {random_age}")
                        age_el.fill(str(random_age))
                    elif len(visible_inputs) >= 3:
                        birthday_el = visible_inputs[2]
                        birthday_str = f"{month:02d}/{day:02d}/{year}"
                        p_log(profile_name, f"[{profile_name}] (Fallback) Điền ngày sinh vào ô 3: {birthday_str}")
                        birthday_el.fill(birthday_str)
                
                time.sleep(0.5)
                
                try:
                    submit_btn = find_continue_button(page_gpt)
                    if submit_btn:
                        submit_btn.click()
                        p_log(profile_name, f"[{profile_name}] Đã bấm nút hoàn thành thông tin cá nhân.")
                    else:
                        page_gpt.keyboard.press("Enter")
                        p_log(profile_name, f"[{profile_name}] Warning: Không tìm thấy nút hoàn tất, thử nhấn Enter.")
                except Exception as e:
                    p_log(profile_name, f"[{profile_name}] Lỗi click nút hoàn tất: {e}")
                    
                sleep_with_countdown(profile_name, 5, "hoàn tất thông tin cá nhân")
            else:
                p_log(profile_name, f"[{profile_name}] Bỏ qua điền thông tin cá nhân (không tìm thấy ô nhập hoặc đã vào thẳng).")
                
            # --- Bỏ qua popup chào mừng ---
            p_log(profile_name, f"[{profile_name}] Đang kiểm tra và đóng các hộp thoại chào mừng/hướng dẫn...")
            page_gpt.bring_to_front()
            sleep_with_countdown(profile_name, 5, "tải các popup chào mừng")
            
            for _ in range(15):
                dismiss_selectors = [
                    'button:has-text("Continue")',
                    'div[role="button"]:has-text("Continue")',
                    'span:has-text("Continue")',
                    'button:has-text("Next")',
                    'div[role="button"]:has-text("Next")',
                    'button:has-text("Tiếp tục")',
                    'div[role="button"]:has-text("Tiếp tục")',
                    'button:has-text("Done")',
                    'div[role="button"]:has-text("Done")',
                    'button:has-text("Xong")',
                    'button:has-text("OK")',
                    'button:has-text("Okay")',
                    'button:has-text("Okey")',
                    'button:has-text("Got it")',
                    'button:has-text("Let\'s go")',
                    'button:has-text("Bắt đầu")',
                    'button:has-text("Dismiss")',
                    'button:has-text("Close")',
                    'button:has-text("Đóng")',
                    'button:has-text("Skip")',
                    'button:has-text("Bỏ qua")',
                    'button:has-text("Tiếp theo")',
                    'button[aria-label="Close"]',
                    'button[aria-label="Đóng"]',
                    'div[role="dialog"] button:has-text("OK")',
                    'div[role="dialog"] button:has-text("Close")',
                    'div[role="dialog"] button',
                    'div[role="dialog"] div[role="button"]'
                ]
                clicked = False
                for sel in dismiss_selectors:
                    try:
                        elements = page_gpt.locator(sel).all()
                        for el in elements:
                            if el.is_visible():
                                el.click(timeout=1000)
                                p_log(profile_name, f"[{profile_name}] Đã đóng popup: {sel}")
                                clicked = True
                                time.sleep(1)
                                break
                    except:
                        pass
                    if clicked:
                        break
                        
                has_dialog = False
                for dialog_sel in ['div[role="dialog"]', '[class*="modal"]', '[class*="dialog"]', '[class*="overlay"]']:
                    try:
                        if page_gpt.locator(dialog_sel).count() > 0:
                            for dlg in page_gpt.locator(dialog_sel).all():
                                if dlg.is_visible():
                                    has_dialog = True
                                    break
                            if has_dialog:
                                break
                    except:
                        pass
                        
                if page_gpt.locator('#prompt-textarea').count() > 0 and page_gpt.locator('#prompt-textarea').is_visible() and not has_dialog and not clicked:
                    break
                time.sleep(1)
                
            p_log(profile_name, f"\n[{profile_name}] 🎉🎉 HOÀN THÀNH TẠO VÀ ĐỔI TÀI KHOẢN GPT!")
            p_log(profile_name, f"[{profile_name}] File lưu trữ: {acc_file}")
            p_log(profile_name, f"[{profile_name}] Bạn có thể kiểm tra và sử dụng ChatGPT ngay trên trình duyệt này.")
            
            if "--auto" in sys.argv:
                p_log(profile_name, f"[{profile_name}] Chạy ở chế độ tự động (Auto). Tự động đóng trình duyệt sau 3 giây...")
                time.sleep(3)
            else:
                p_log(profile_name, f"[{profile_name}] [!] VUI LÒNG ĐÓNG CỬA SỔ TRÌNH DUYỆT NÀY KHI ĐÃ HOÀN TẤT THỦ CÔNG!")
                page_gpt.wait_for_event("close", timeout=0)
            
    except Exception as e:
        import traceback
        p_log(profile_name, f"\n[{profile_name}] ❌ CÓ LỖI XẢY RA TRONG QUÁ TRÌNH TỰ ĐỘNG HÓA:")
        p_log(profile_name, traceback.format_exc())
        time.sleep(5)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("Thiếu tham số tên profile")
        time.sleep(3)
