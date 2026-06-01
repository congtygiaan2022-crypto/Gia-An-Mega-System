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


def build_driver(profile_dir: str = None) -> webdriver.Chrome:
    cfg = CONFIG["selenium"]
    options = Options()
    binary = _chrome_binary()
    if binary and os.path.exists(binary):
        options.binary_location = binary
        log.info(f"Using Chrome binary: {binary}")
    if cfg["headless"]:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
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
    url = driver.current_url
    if "facebook.com" not in url or "login" in url or "checkpoint" in url or "two_step" in url:
        return False
    return bool(driver.find_elements(By.CSS_SELECTOR,
        "[data-pagelet='LeftRail'], [aria-label='Your profile'], [data-testid='royal_blue_bar'], [aria-label='Facebook'][role='navigation']"))


def login(driver: webdriver.Chrome) -> bool:
    fb = CONFIG["facebook"]

    # Kiểm tra xem đã login chưa (dùng cookies từ profile đã lưu)
    log.info("Kiểm tra session đã lưu...")
    driver.get("https://www.facebook.com/")
    
    try:
        # Chờ tối đa 5 giây xem trang chủ Facebook load xong hoặc có biểu hiện đã đăng nhập
        WebDriverWait(driver, 5).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, "[aria-label='Facebook'][role='navigation'], [data-pagelet='LeftRail'], [aria-label='Your profile'], [data-testid='royal_blue_bar']") or 
                      "login" in d.current_url or "checkpoint" in d.current_url
        )
    except Exception:
        pass

    if _is_logged_in(driver):
        log.info("Đã đăng nhập từ session đã lưu — bỏ qua bước login")
        return True

    log.info("Đang mở trang đăng nhập Facebook...")
    driver.get("https://www.facebook.com/login")
    wait = WebDriverWait(driver, 15)

    try:
        try:
            email_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='email']")))
        except Exception:
            # Maybe already logged in and redirected
            if _is_logged_in(driver):
                log.info("Đã đăng nhập thành công (tự động chuyển hướng)")
                return True
            raise

        email_field.click()
        email_field.clear()
        email_field.send_keys(fb["email"])

        pass_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='pass'], input[id='pass']")))
        pass_field.click()
        pass_field.clear()
        pass_field.send_keys(fb["password"])

        pass_field.send_keys("\n")
        
        # Chờ chuyển hướng sau khi đăng nhập mật khẩu
        try:
            WebDriverWait(driver, 10).until(
                lambda d: "login" not in d.current_url or 
                          d.find_elements(By.CSS_SELECTOR, "[aria-label='Facebook'][role='navigation'], [data-pagelet='LeftRail'], [aria-label='Your profile']") or
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
