import os
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from modules.config_loader import CONFIG
from modules.logger import get_logger
from modules.two_factor import get_totp_code

log = get_logger(__name__)

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _chromedriver_path():
    """Return chromedriver path or None if not found locally."""
    # Vô hiệu hóa việc sử dụng chromedriver.exe trực tiếp tại thư mục gốc
    # để tránh lỗi WinError 740 (yêu cầu quyền Administrator).
    # Chương trình sẽ tự động sử dụng webdriver-manager để tải và cài đặt driver phù hợp.
    return None

def _chrome_binary() -> str:
    """
    Trả về Chrome binary path nếu user tự cấu hình trong config.json/selenium/chrome_binary.
    Trả về chuỗi rỗng để Selenium tự tìm Chrome (đây là cách hoạt động tốt nhất).
    """
    return CONFIG.get("selenium", {}).get("chrome_binary", "").strip()


def _resolve_chromedriver_path(raw_path: str) -> str:
    """
    webdriver_manager sometimes returns a path to a non-executable file
    (e.g. THIRD_PARTY_NOTICES.chromedriver) instead of the actual binary.
    This function validates the path and, if it is not a chromedriver
    executable, searches the same directory for the real binary.
    """
    exe_name = "chromedriver.exe" if sys.platform == "win32" else "chromedriver"

    # If the path already points to the correct executable, use it as-is.
    if os.path.basename(raw_path).lower() in ("chromedriver", "chromedriver.exe"):
        if os.path.isfile(raw_path):
            return raw_path

    # Search the directory (and one level up) for the actual binary.
    search_dirs = [os.path.dirname(raw_path)]
    parent = os.path.dirname(search_dirs[0])
    if parent not in search_dirs:
        search_dirs.append(parent)

    for directory in search_dirs:
        candidate = os.path.join(directory, exe_name)
        if os.path.isfile(candidate):
            log.info(f"Resolved chromedriver binary: {candidate}")
            return candidate

        # Also do a recursive walk limited to 2 levels deep
        for root, _dirs, files in os.walk(directory):
            depth = root[len(directory):].count(os.sep)
            if depth > 2:
                continue
            if exe_name in files:
                found = os.path.join(root, exe_name)
                log.info(f"Resolved chromedriver binary (walk): {found}")
                return found

    # Fall back to the original path and let Selenium raise a meaningful error.
    log.warning(
        f"Could not resolve a valid chromedriver binary from '{raw_path}'. "
        "Using original path as fallback."
    )
    return raw_path


def _build_service():
    """Build a Chrome Service, trying multiple strategies."""
    # Strategy 1: Try webdriver_manager if available
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        raw_path = ChromeDriverManager().install()
        driver_path = _resolve_chromedriver_path(raw_path)
        log.info(f"Using chromedriver from webdriver_manager: {driver_path}")
        return Service(executable_path=driver_path)
    except ImportError:
        log.debug("webdriver_manager not installed, trying other strategies.")
    except Exception as e:
        log.warning(f"webdriver_manager failed: {e}, trying other strategies.")

    # Strategy 2: Use local chromedriver if it exists
    local_path = _chromedriver_path()
    if local_path:
        log.info(f"Using local chromedriver: {local_path}")
        return Service(executable_path=local_path)

    # Strategy 3: Rely on chromedriver being in PATH
    log.info("No local chromedriver found, relying on PATH.")
    return Service()


def configure_window_layout(driver: webdriver.Chrome, is_mobile: bool, window_index: int, grid_rows: int, grid_cols: int):
    """
    Sắp xếp cửa sổ trình duyệt theo dạng lưới trên màn hình nếu ở chế độ Mobile.
    Mặc định tỉ lệ dọc (9:16 - mô phỏng 1080x1900).
    """
    if not is_mobile:
        return

    # Tỉ lệ dọc 9:16 (ví dụ 1080:1900)
    aspect_ratio = 9.0 / 16.0

    try:
        import ctypes
        user32 = ctypes.windll.user32
        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)
    except Exception:
        # Fallback nếu lỗi hoặc không ở Windows
        screen_w = 1920
        screen_h = 1080

    # Tính kích thước ô trong lưới
    cell_w = screen_w // grid_cols
    cell_h = screen_h // grid_rows

    # Trừ bớt padding cho thanh tác vụ và viền cửa sổ
    max_win_h = cell_h - 60
    max_win_w = cell_w - 20

    # Tính kích thước cửa sổ theo tỉ lệ dọc
    win_h = max_win_h
    win_w = int(win_h * aspect_ratio)

    if win_w > max_win_w:
        win_w = max_win_w
        win_h = int(win_w / aspect_ratio)

    win_w = max(320, min(win_w, screen_w))
    win_h = max(480, min(win_h, screen_h))

    # Tính toạ độ hiển thị (X, Y) ở trung tâm ô lưới
    row = window_index // grid_cols
    col = window_index % grid_cols

    x = col * cell_w + (cell_w - win_w) // 2
    y = row * cell_h + (cell_h - win_h) // 2

    try:
        log.info(f"Mobile Window positioning: index={window_index}, grid={grid_rows}x{grid_cols}, pos=({x},{y}), size=({win_w}x{win_h})")
        driver.set_window_rect(x, y, win_w, win_h)
    except Exception as e:
        log.warning(f"Failed to set window position/size: {e}")


def build_driver(profile_dir: str = None) -> webdriver.Chrome:
    cfg = CONFIG["selenium"]
    options = Options()
    binary = _chrome_binary()
    if binary and os.path.exists(binary):
        options.binary_location = binary
        log.info(f"Using Chrome binary: {binary}")
    if cfg["headless"]:
        options.add_argument("--headless=new")
    
    mobile_cfg = CONFIG.get("mobile_settings", {})
    is_mobile = False # Luôn khởi động ở chế độ PC để đăng nhập ổn định
    if is_mobile:
        log.info("Mobile mode enabled, skipping start-maximized options.")
        user_agents = mobile_cfg.get("user_agents", [])
        if not user_agents:
            user_agents = [
                "Mozilla/5.0 (iPhone; CPU iPhone OS 19_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/130.0.0.0 Mobile/15E148 Safari/604.1"
            ]
        window_idx = mobile_cfg.get("window_index", 0)
        mobile_ua = user_agents[window_idx % len(user_agents)]
        options.add_argument(f"--user-agent={mobile_ua}")
        log.info(f"Loaded Mobile User Agent for Chrome startup: {mobile_ua}")
    else:
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")

    options.add_argument("--disable-hang-monitor")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-crash-reporter")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-session-crashed-bubble")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    if not profile_dir:
        profile_dir = os.path.join(_BASE_DIR, "chrome_profile", "default")
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_experimental_option("useAutomationExtension", False)

    service = _build_service()
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(cfg["implicit_wait"])
    driver.set_page_load_timeout(cfg["page_load_timeout"])
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    if is_mobile:
        window_index = mobile_cfg.get("window_index", 0)
        grid_rows = mobile_cfg.get("grid_rows", 1)
        grid_cols = mobile_cfg.get("grid_cols", 1)
        configure_window_layout(driver, is_mobile, window_index, grid_rows, grid_cols)

    log.info(f"Chrome driver initialized (profile: {profile_dir})")
    return driver


def _handle_2fa(driver: webdriver.Chrome, wait: WebDriverWait) -> bool:
    """Nhập mã 2FA nếu Facebook yêu cầu sau khi đăng nhập mật khẩu."""
    secret = CONFIG["facebook"].get("2fa_secret", "").strip()
    if not secret:
        log.warning("Trang 2FA xuất hiện nhưng chưa cài 2fa_secret trong config.json")
        return False

    try:
        code = get_totp_code(secret)
        log.info(f"2FA code: {code} — xử lý trang 2FA...")

        # Nếu trang hiện "Kiểm tra thông báo thiết bị khác" → click "Thử cách khác"
        try:
            try_other = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH,
                    "//span[contains(text(),'Thử cách khác') or contains(text(),'Try another way') "
                    "or contains(text(),'Use a different method')]/.."
                    "|//a[contains(text(),'Thử cách khác') or contains(text(),'Try another way')]"
                    "|//div[@role='button'][contains(.,'Thử cách khác') or contains(.,'Try another way')]"
                ))
            )
            try_other.click()
            log.info("Đã click 'Thử cách khác'")
            # Chờ ngắn để menu tùy chọn mở ra
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//*"))
            )
        except Exception:
            pass

        # Chọn "Ứng dụng xác thực" / Authenticator App nếu có menu lựa chọn
        try:
            auth_app_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH,
                    "//span[contains(text(),'Ứng dụng xác thực') or contains(text(),'Authentication app') "
                    "or contains(text(),'Authenticator app')]/.."
                    "|//div[@role='radio'][.//*[contains(text(),'Ứng dụng xác thực') or contains(text(),'Authentication app')]]"
                    "|//label[.//*[contains(text(),'Ứng dụng xác thực') or contains(text(),'Authentication app')]]"
                ))
            )
            auth_app_btn.click()
            log.info("Đã chọn 'Ứng dụng xác thực'")
            
            # Click "Tiếp tục" / Continue button
            try:
                continue_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH,
                        "//span[contains(text(),'Tiếp tục') or contains(text(),'Continue')]/.."
                        "|//button[contains(text(),'Tiếp tục') or contains(text(),'Continue')]"
                        "|//div[@role='button'][.//*[contains(text(),'Tiếp tục') or contains(text(),'Continue')]]"
                    ))
                )
                continue_btn.click()
                log.info("Đã click 'Tiếp tục'")
                # Chờ form nhập OTP xuất hiện
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//input"))
                )
            except Exception:
                pass
        except Exception:
            pass

        # Thử nhiều selector cho OTP input, tránh chờ tuần tự với implicit wait
        otp_field = None
        selectors = [
            (By.XPATH, "//input[@id='approvals_code' or @name='approvals_code']"),
            (By.XPATH, "//input[@autocomplete='one-time-code']"),
            (By.XPATH, "//input[@inputmode='numeric']"),
            (By.XPATH, "//input[@type='tel' or @type='number']"),
            (By.XPATH, "//input[contains(@aria-label,'digit') or contains(@aria-label,'code') "
                       "or contains(@aria-label,'Mã') or contains(@aria-label,'xác thực')]"),
            (By.XPATH, "//input[@type='text' and not(@name='email') and not(@name='pass')]"),
        ]
        
        driver.implicitly_wait(0)
        end_time = time.time() + 15
        while time.time() < end_time:
            for sel_type, sel_val in selectors:
                try:
                    elements = driver.find_elements(sel_type, sel_val)
                    for el in elements:
                        if el.is_displayed() and el.is_enabled():
                            otp_field = el
                            log.info(f"Tìm thấy 2FA input: {sel_val[:60]}")
                            break
                    if otp_field: break
                except Exception:
                    pass
            if otp_field: break
            time.sleep(0.5)
            
        driver.implicitly_wait(CONFIG["selenium"].get("implicit_wait", 10))

        if otp_field is None:
            try:
                driver.save_screenshot("debug_2fa_page.png")
                log.warning("Không tìm thấy input 2FA — đã chụp debug_2fa_page.png")
            except Exception:
                pass
            log.error("Không tìm thấy ô nhập mã 2FA")
            return False

        # Tạo lại code ngay trước khi nhập (tránh hết hạn sau 30s)
        code = get_totp_code(secret)
        otp_field.click()
        otp_field.clear()
        otp_field.send_keys(code)
        log.info(f"Đã nhập mã 2FA: {code}")

        # Chụp screenshot để debug nếu cần
        try:
            driver.save_screenshot("debug_2fa_otp.png")
        except Exception:
            pass

        # Tìm submit button với nhiều selector bằng vòng lặp nhanh
        submit = None
        submit_selectors = [
            "//button[@id='checkpointSubmitButton']",
            "//button[@type='submit']",
            "//input[@type='submit']",
            "//span[text()='Tiếp tục' or text()='Continue' or text()='Submit']/..",
            "//div[@role='button'][.//*[text()='Tiếp tục' or text()='Continue']]",
            "//button[contains(.,'Tiếp tục') or contains(.,'Continue') or contains(.,'Submit')]",
        ]
        
        driver.implicitly_wait(0)
        end_time = time.time() + 5
        while time.time() < end_time:
            for sel in submit_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, sel)
                    for el in elements:
                        if el.is_displayed() and el.is_enabled():
                            submit = el
                            log.info(f"Tìm thấy submit button: {sel[:50]}")
                            break
                    if submit: break
                except Exception:
                    pass
            if submit: break
            time.sleep(0.5)
            
        driver.implicitly_wait(CONFIG["selenium"].get("implicit_wait", 10))

        if submit is None:
            # Thử nhấn Enter thay vì click button
            otp_field.send_keys("\n")
            log.info("Không tìm thấy submit button — dùng Enter")
        else:
            submit.click()
        
        # Chờ chuyển hướng sau khi nhập OTP
        try:
            WebDriverWait(driver, 10).until(
                lambda d: "checkpoint" not in d.current_url and "two_step" not in d.current_url
            )
        except Exception:
            pass
        return True
    except Exception as e:
        log.error(f"Lỗi khi nhập 2FA: {e}")
        return False


def _is_logged_in(driver: webdriver.Chrome) -> bool:
    url = driver.current_url or ""
    if "facebook.com" not in url or "login" in url or "checkpoint" in url or "two_step" in url:
        return False

    # 1. Kiểm tra qua Javascript Environment variables của Facebook
    try:
        uid = driver.execute_script(
            "return (window.Env && window.Env.userid) ? window.Env.userid.toString() : '';"
        )
        if uid and uid.isdigit():
            return True
    except Exception:
        pass

    # 2. Kiểm tra qua Cookies
    try:
        for cookie in driver.get_cookies():
            if cookie.get('name') == 'c_user' and str(cookie.get('value', '')).isdigit():
                return True
    except Exception:
        pass

    # 3. Kiểm tra qua UI elements
    desktop_ok = bool(driver.find_elements(By.CSS_SELECTOR,
        "[data-pagelet='LeftRail'], [aria-label='Your profile'], [data-testid='royal_blue_bar'], [aria-label='Facebook'][role='navigation']"))
    mobile_ok = bool(driver.find_elements(By.CSS_SELECTOR,
        "header[data-sigil='MBasicHeader'], [data-sigil='m-header-search-link'], a[href*='/notifications'], a[href*='/logout.php'], .m-home-header, [aria-label='Facebook Menu'], [aria-label='Search Facebook']"))
    return desktop_ok or mobile_ok or ("home.php" in url or "home" in url or "feed" in url or "watch" in url)



def login(driver: webdriver.Chrome) -> bool:
    fb = CONFIG["facebook"]
    mobile_cfg = CONFIG.get("mobile_settings", {})
    is_mobile = False # Luôn khởi động ở chế độ PC để đăng nhập ổn định

    base_url = "https://m.facebook.com" if is_mobile else "https://www.facebook.com"

    # Kiểm tra xem đã login chưa (dùng cookies từ profile đã lưu)
    log.info("Kiểm tra session đã lưu...")
    driver.get(base_url + "/")
    
    try:
        # Chờ tối đa 5 giây xem trang chủ Facebook load xong hoặc có biểu hiện đã đăng nhập
        WebDriverWait(driver, 5).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, "[aria-label='Facebook'][role='navigation'], [data-pagelet='LeftRail'], [aria-label='Your profile'], [data-testid='royal_blue_bar'], header[data-sigil='MBasicHeader'], a[href*='/logout.php'], .m-home-header") or 
                      "login" in d.current_url or "checkpoint" in d.current_url
        )
    except Exception:
        pass

    if _is_logged_in(driver):
        log.info("Đã đăng nhập từ session đã lưu — bỏ qua bước login")
        return True

    log.info("Đang mở trang đăng nhập Facebook...")
    driver.get(base_url + "/login")
    wait = WebDriverWait(driver, 15)

    try:
        try:
            email_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='email'], input#m_login_email, input[id='m_login_email']")))
        except Exception:
            # Maybe already logged in and redirected
            if _is_logged_in(driver):
                log.info("Đã đăng nhập thành công (tự động chuyển hướng)")
                return True
            raise

        email_field.click()
        email_field.clear()
        email_field.send_keys(fb["email"])

        pass_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='pass'], input[id='pass'], input#m_login_password, input[id='m_login_password']")))
        pass_field.click()
        pass_field.clear()
        pass_field.send_keys(fb["password"])

        # Thử click nút Đăng nhập / Log In
        try:
            login_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[name='login'], button[type='submit'], input[type='submit'], button[id='loginbutton']")))
            login_btn.click()
            log.info("Đã click nút Đăng nhập")
        except Exception:
            pass_field.send_keys("\n")
            log.info("Không tìm thấy nút đăng nhập — gửi phím Enter")
        
        # Chờ chuyển hướng sau khi đăng nhập mật khẩu
        try:
            WebDriverWait(driver, 10).until(
                lambda d: "login" not in d.current_url or 
                          d.find_elements(By.CSS_SELECTOR, "[aria-label='Facebook'][role='navigation'], [data-pagelet='LeftRail'], [aria-label='Your profile'], header[data-sigil='MBasicHeader'], a[href*='/logout.php'], .m-home-header") or
                          "checkpoint" in d.current_url or "two_step" in d.current_url
            )
        except Exception:
            pass

        # Xử lý CAPTCHA — chỉ detect khi URL vẫn ở /login (chưa redirect)
        # Dùng iframe reCAPTCHA làm tín hiệu, không dùng page source (dễ false positive)
        captcha_wait = 0
        while captcha_wait < 120:
            url = driver.current_url
            # Nếu đã redirect khỏi login → không phải CAPTCHA nữa
            if "login" not in url:
                break
            # Kiểm tra reCAPTCHA iframe thực sự
            try:
                recaptcha_frames = driver.find_elements(By.XPATH,
                    "//iframe[contains(@src,'recaptcha') or contains(@title,'reCAPTCHA')]"
                )
                if recaptcha_frames:
                    if captcha_wait == 0:
                        log.warning("Facebook hiển thị CAPTCHA — hãy giải thủ công trong cửa sổ Chrome (tối đa 120s)...")
                    time.sleep(5)
                    captcha_wait += 5
                    continue
            except Exception:
                pass
            break

        # Kiểm tra nếu Facebook yêu cầu 2FA
        if "checkpoint" in driver.current_url or "two_step" in driver.current_url:
            log.info("Facebook yêu cầu xác thực 2FA...")
            if not _handle_2fa(driver, wait):
                return False
            
            # Chờ chuyển hướng sau 2FA
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: "checkpoint" not in d.current_url and "two_step" not in d.current_url
                )
            except Exception:
                pass

        # Chờ thêm nếu đang redirect về trang chủ
        try:
            WebDriverWait(driver, 15).until(
                lambda d: "facebook.com" in d.current_url and "login" not in d.current_url and "two_step" not in d.current_url and "checkpoint" not in d.current_url
            )
        except Exception:
            pass

        if _is_logged_in(driver) or ("facebook.com" in driver.current_url and "login" not in driver.current_url
                                      and "two_step" not in driver.current_url):
            log.info(f"Đăng nhập thành công — URL: {driver.current_url}")
            return True
        else:
            log.error(f"Đăng nhập thất bại — URL: {driver.current_url}")
            return False
    except Exception as e:
        log.error(f"Lỗi đăng nhập: {e}")
        return False
