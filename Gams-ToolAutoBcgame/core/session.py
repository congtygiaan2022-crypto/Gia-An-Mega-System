"""
Session Manager - Quản lý đăng nhập và phiên làm việc BCGame
"""
import json
import os
import re
import time
import requests
from typing import Optional, Callable
from loguru import logger

from core.browser import BrowserController
from core.bug_tracker import report_bug

try:
    from selenium.webdriver.common.by import By
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


COOKIES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cookies.json")
LOGIN_URL = "https://bcvn2.com/vi"
SPORTS_URL = "https://bcvn2.com/vi/sports/soccer-1"


class SessionManager:
    """Quản lý phiên đăng nhập BCGame"""

    def __init__(self, browser: BrowserController, log_callback: Optional[Callable] = None):
        self.browser = browser
        self.log_callback = log_callback
        self.is_logged_in = False
        self.username = ""

    def _log(self, message: str, level: str = "INFO"):
        logger.info(message)
        if self.log_callback:
            self.log_callback(message, level)

    def login_with_password(self, phone: str, password: str, two_fa_key: str = None, country_code: str = "+84") -> bool:
        """Đăng nhập bằng số điện thoại, mật khẩu và 2FA (nếu có)"""
        self._log(f"🔐 Đang đăng nhập với số điện thoại: {phone[:4]}****")

        # Mở trang chủ
        if not self.browser.navigate(LOGIN_URL):
            self._log("❌ Không thể mở trang BCGame", "ERROR")
            return False

        # Đợi hệ thống chuyển hướng và chống DDoS ổn định
        self._wait_for_domain_stabilization(timeout=60, stable_time=5)

        # Kiểm tra xem có bị nhảy domain không
        current_url = self.browser.current_url
        if "bcvn2.com" not in current_url:
            self._log(f"🔄 Đã bị nhảy domain sang {current_url}. Đang quay lại domain gốc...")
            self.browser.navigate(LOGIN_URL)
            time.sleep(3)

        # Click nút Đăng Nhập
        login_btn = self.browser.find_element(
            By.XPATH,
            "//button[contains(text(), 'Đăng Nhập') or contains(text(), 'Login') or contains(@class, 'login')]"
        )
        if not login_btn:
            login_btn = self.browser.find_element(By.CSS_SELECTOR, "[data-testid='login-btn'], .login-btn, button.login")

        if login_btn:
            self.browser.click_element(login_btn)
            time.sleep(1.5)

        # Xử lý nhập form có thể bị chuyển hướng (stale element)
        login_success = False
        for attempt in range(3):
            # Nhập số điện thoại
            phone_input = self._find_phone_input()
            if not phone_input:
                time.sleep(2)
                continue
                
            _stripped = phone.lstrip("+")
            _cc = country_code.lstrip("+")
            if _cc and _stripped.startswith(_cc):
                _stripped = _stripped[len(_cc):]
            clean_phone = _stripped.lstrip("0")
            if not self.browser.type_text(phone_input, clean_phone, clear_first=True):
                time.sleep(1)
                continue

            # Nhập mật khẩu
            password_input = self.browser.find_element(By.CSS_SELECTOR, "input[type='password']")
            if not password_input or not self.browser.type_text(password_input, password, clear_first=True):
                time.sleep(1)
                continue

            # Click nút Đăng Nhập trong form
            submit_btn = self.browser.find_element(
                By.XPATH,
                "//button[@type='submit' or contains(@class, 'submit') or contains(text(), 'Đăng Nhập')]"
            )
            if submit_btn:
                if self.browser.click_element(submit_btn):
                    self._log("🔄 Đang xử lý đăng nhập...")
                    time.sleep(3)
                    login_success = True
                    break
            
            time.sleep(2)
            
        if not login_success:
            self._log("❌ Không thể điền form đăng nhập sau nhiều lần thử", "ERROR")
            report_bug(
                exc=RuntimeError("Không thể điền form đăng nhập sau nhiều lần thử"),
                module="core.session",
                task="login_with_password",
                context={"phone": phone[:4] + "****", "url": self.browser.current_url},
                severity="CRITICAL",
            )
            return False

        # --- XỬ LÝ 2FA ---
        if two_fa_key and len(two_fa_key.strip()) > 5:
            time.sleep(2)
            # Thử tìm ô nhập OTP
            otp_selectors = [
                "input[placeholder*='2FA']",
                "input[placeholder*='Google Authenticator']",
                "input[placeholder*='mã']",
                "input[maxlength='6']"
            ]
            otp_input = None
            for sel in otp_selectors:
                otp_input = self.browser.find_element(By.CSS_SELECTOR, sel, timeout=2)
                if otp_input: break
                
            if otp_input:
                self._log("🛡️ Hệ thống yêu cầu mã 2FA. Đang lấy mã từ 2fa.live...")
                otp_code = self._get_2fa_code(two_fa_key)
                if otp_code:
                    self.browser.type_text(otp_input, otp_code)
                    self._log(f"✅ Đã nhập mã 2FA: {otp_code}")
                    time.sleep(1.5)
                    
                    # Bấm nút Xác nhận nếu cần
                    confirm_btn = self.browser.find_element(By.XPATH, "//button[contains(text(), 'Xác nhận') or contains(text(), 'Confirm') or contains(text(), 'Xác minh')]")
                    if confirm_btn:
                        self.browser.click_element(confirm_btn)
                        time.sleep(3)
                else:
                    self._log("❌ Không lấy được mã 2FA. Vui lòng kiểm tra lại Key!", "ERROR")
                    return False

        # Kiểm tra đăng nhập thành công
        if self._check_logged_in():
            self._log("✅ Đăng nhập thành công!", "SUCCESS")
            self.is_logged_in = True
            self.save_cookies()
            return True
        else:
            self._log("❌ Đăng nhập thất bại. Kiểm tra lại thông tin!", "ERROR")
            report_bug(
                exc=RuntimeError("Đăng nhập thất bại sau khi submit form"),
                module="core.session",
                task="login_with_password",
                context={"url": self.browser.current_url},
                severity="CRITICAL",
            )
            return False

    def _wait_for_domain_stabilization(self, timeout=60, stable_time=5):
        """Chờ cho đến khi URL ngừng chuyển hướng liên tục (Cloudflare/DDoS check)"""
        self._log("⏳ Đang chờ hệ thống kiểm tra bảo mật (chống DDoS/Bot)...")
        start_time = time.time()
        
        try:
            last_url = self.browser.current_url
        except Exception:
            last_url = ""
            
        last_change_time = time.time()
        
        while time.time() - start_time < timeout:
            time.sleep(1)
            try:
                current_url = self.browser.current_url
                if current_url != last_url:
                    if last_url:
                        self._log("🔄 Đang chuyển hướng...")
                    last_url = current_url
                    last_change_time = time.time()
                    
                # Nếu URL không đổi trong 'stable_time' giây, coi như đã qua bước bảo mật
                if time.time() - last_change_time >= stable_time:
                    self._log(f"✅ Tên miền đã ổn định: {current_url}")
                    return True
            except Exception:
                pass
                
        self._log("⚠️ Hết thời gian chờ nhưng trang web vẫn đang chuyển hướng. Tiếp tục...", "WARNING")
        return False

    def _get_2fa_code(self, key: str) -> Optional[str]:
        """Lấy mã OTP 6 số từ 2fa.live (API của 2fa.vn tương đương)"""
        try:
            key = key.replace(" ", "")
            url = f"https://2fa.live/tok/{key}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("token")
        except Exception as e:
            logger.error(f"Lỗi lấy 2FA: {e}")
        return None

    def login_with_cookies(self, cookies_file: str = None) -> bool:
        """Đăng nhập bằng cookies đã lưu"""
        file_path = cookies_file or COOKIES_FILE

        if not os.path.exists(file_path):
            self._log(f"⚠️ Không tìm thấy file cookies: {file_path}", "WARNING")
            return False

        try:
            with open(file_path, "r") as f:
                cookies = json.load(f)

            self._log("🍪 Đang tải cookies...")
            self.browser.navigate(LOGIN_URL)
            time.sleep(2)

            for cookie in cookies:
                try:
                    self.browser.driver.add_cookie(cookie)
                except Exception as e:
                    self._log(f"⚠️ Bỏ qua cookie lỗi '{cookie.get('name','?')}': {e}", "DEBUG")

            self.browser.navigate(LOGIN_URL)
            time.sleep(2)

            if self._check_logged_in():
                self._log("✅ Đăng nhập bằng cookies thành công!", "SUCCESS")
                self.is_logged_in = True
                return True
            else:
                self._log("⚠️ Cookies đã hết hạn, cần đăng nhập lại", "WARNING")
                return False

        except Exception as e:
            self._log(f"❌ Lỗi tải cookies: {str(e)}", "ERROR")
            report_bug(exc=e, module="core.session", task="login_with_cookies",
                       context={"cookies_file": file_path})
            return False

    def save_cookies(self):
        """Lưu cookies hiện tại"""
        if not self.browser.driver:
            return
        try:
            cookies = self.browser.driver.get_cookies()
            os.makedirs(os.path.dirname(COOKIES_FILE), exist_ok=True)
            with open(COOKIES_FILE, "w") as f:
                json.dump(cookies, f, indent=2)
            self._log("💾 Đã lưu cookies", "INFO")
        except Exception as e:
            self._log(f"⚠️ Không thể lưu cookies: {str(e)}", "WARNING")

    def logout(self):
        """Đăng xuất"""
        self.is_logged_in = False
        self._log("👋 Đã đăng xuất")

    def ensure_on_sports_page(self) -> bool:
        """Đảm bảo đang ở trang cá cược thể thao"""
        current = self.browser.current_url
        if "sports/soccer" not in current:
            return self.browser.navigate(SPORTS_URL)
        return True

    def _find_phone_input(self):
        """Tìm ô nhập số điện thoại"""
        selectors = [
            "input[type='tel']",
            "input[placeholder*='Điện Thoại']",
            "input[placeholder*='điện thoại' i]",
            "input[placeholder*='Email' i]",
            "input[placeholder*='phone' i]",
            "input[name='phone']",
            "input[name='mobile']",
            "input:not([type='password'])", # Fallback to any non-password input
        ]
        for selector in selectors:
            el = self.browser.find_element(By.CSS_SELECTOR, selector, timeout=3)
            if el:
                return el
        return None

    def _check_logged_in(self) -> bool:
        """Kiểm tra xem đã đăng nhập chưa"""
        try:
            # Tìm element chỉ xuất hiện khi đã đăng nhập
            logged_indicators = [
                "//div[contains(@class, 'user-balance')]",
                "//div[contains(@class, 'avatar')]",
                "//span[contains(@class, 'username')]",
                "//*[contains(@class, 'user-info')]",
                "//*[@data-testid='user-menu']",
            ]
            for xpath in logged_indicators:
                el = self.browser.find_element(By.XPATH, xpath, timeout=3)
                if el:
                    return True

            # Kiểm tra nút Đăng Nhập còn không
            login_buttons = self.browser.find_elements(
                By.XPATH,
                "//button[contains(text(), 'Đăng Nhập')]",
                timeout=2
            )
            return len(login_buttons) == 0

        except Exception:
            return False

    def get_balance(self) -> float:
        """Lấy số dư tài khoản dưới dạng số thực (Xuyên qua Shadow DOM)"""
        js_get_balance = """
            function findBalance(root, balances) {
                // 1. Ưu tiên các phần tử là VÍ (Wallet) hiển thị ở header
                let selectors = [
                    '[data-testid="balance-amount"]', 
                    '[class*="balance-value"]', 
                    '.wallet-balance', 
                    '.user-balance',
                    '[class*="WalletContainer"] [class*="Amount"]'
                ];
                selectors.forEach(s => {
                    root.querySelectorAll(s).forEach(el => {
                        let t = (el.innerText || '').trim();
                        if (t.match(/[0-9]/)) balances.push({text: t, weight: 100});
                    });
                });
                
                // 2. Quét các thẻ có chứa ký hiệu tiền tệ (Trọng số thấp hơn)
                root.querySelectorAll('div, span, p, b').forEach(el => {
                    let text = (el.innerText || '').trim();
                    if(text.length > 0 && text.length < 30 && /[0-9]/.test(text)) {
                        let hasCurrency = text.includes('VND') || text.includes('₫') || text.includes('USDT') || text.includes('JB') || text.includes('VNDK');
                        if(hasCurrency) {
                            balances.push({text: text, weight: 10});
                        }
                    }
                });
                
                let allNodes = root.querySelectorAll('*');
                for (let i = 0; i < allNodes.length; i++) {
                    if (allNodes[i].shadowRoot) findBalance(allNodes[i].shadowRoot, balances);
                }
                return balances;
            }
            return findBalance(document, []);
        """
        try:
            candidates = self.browser.driver.execute_script(js_get_balance)
            if not candidates: return 0.0

            # Phân loại và xử lý ứng viên
            valid_balances = []
            for item in candidates:
                text = item.get('text', '')
                weight = item.get('weight', 1)

                # Làm sạch chuỗi số
                raw = re.sub(r'[^\d.,]', '', text).strip().strip('.,')
                if not raw: continue

                processed_raw = raw
                if raw.count('.') >= 2:
                    processed_raw = raw.replace('.', '')
                elif '.' in raw:
                    parts = raw.split('.')
                    if len(parts[-1]) == 3: # 1.131 -> 1131
                        processed_raw = raw.replace('.', '')
                
                processed_raw = processed_raw.replace(',', '')
                
                try:
                    val = float(processed_raw)
                    if 'VNDK' in text.upper(): val *= 1000
                    valid_balances.append({"val": val, "text": text, "weight": weight})
                except Exception: continue
            
            if not valid_balances: return 0.0
            
            # Log tất cả để debug tìm con số gây nhiễu 25250
            debug_str = " | ".join([f"'{b['text']}'->{b['val']} (w:{b['weight']})" for b in valid_balances[:10]])
            self._log(f"📊 Debug Balance List: {debug_str}", "DEBUG")
            
            # Chọn số dư: Ưu tiên trọng số cao nhất (Wallet Container)
            valid_balances.sort(key=lambda x: x['weight'], reverse=True)
            best_balance = valid_balances[0]['val']
            
            return best_balance


        except Exception as e:
            self._log(f"⚠️ Lỗi lấy số dư: {e}", "DEBUG")
            report_bug(exc=e, module="core.session", task="get_balance",
                       severity="WARNING")
            return 0.0
