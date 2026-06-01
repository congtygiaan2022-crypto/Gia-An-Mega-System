"""
Browser Controller - Quản lý Selenium WebDriver với undetected-chromedriver
"""
import time
import random
import threading
import os
from typing import Optional, Callable
from loguru import logger
from core.bug_tracker import report_bug

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        TimeoutException,
        WebDriverException, ElementClickInterceptedException
    )
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium/undetected-chromedriver chưa được cài đặt")


class BrowserController:
    """Điều khiển trình duyệt Chrome để tương tác với BCGame"""

    BASE_URL = "https://bcvn2.com/vi/sports/soccer-1"

    def __init__(self, headless: bool = False, proxy: Optional[str] = None, log_callback: Optional[Callable] = None):
        self.headless = headless
        self.proxy = proxy
        self.log_callback = log_callback
        self.driver: Optional[object] = None
        self.wait: Optional[object] = None
        self._lock = threading.Lock()
        self.is_running = False

    def _log(self, message: str, level: str = "INFO"):
        logger.info(message)
        if self.log_callback:
            self.log_callback(message, level)

    def start(self) -> bool:
        """Khởi động trình duyệt (Luôn làm mới)"""
        if not SELENIUM_AVAILABLE:
            self._log("❌ Selenium chưa được cài đặt. Chạy: pip install -r requirements.txt", "ERROR")
            return False

        try:
            self._log("🌐 Đang khởi động trình duyệt Chrome...")
            
            # Luôn dọn dẹp tiến trình cũ trước khi mở mới theo yêu cầu của bác
            self._kill_existing_chrome("chrome.exe") 
            
            options = uc.ChromeOptions()
            if self.headless:
                options.add_argument("--headless=new")
            if self.proxy:
                self._log(f"🔌 Sử dụng Proxy: {self.proxy}")
                options.add_argument(f'--proxy-server={self.proxy}')


            # Các options để giả lập người dùng thực
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--window-size=1366,768")
            options.add_argument("--lang=vi-VN")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-crash-reporter")
            options.add_argument("--disable-breakpad")
            options.add_argument("--disable-logging")
            options.add_argument("--log-level=3")
            options.add_argument("--disable-features=RendererCodeIntegrity")



            # User agent thực (Bỏ để uc tự quản lý tốt hơn)
            # options.add_argument("--user-agent=...")


            # Đường dẫn đến bản Chrome portable và thư mục profile
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            profile_dir = os.path.join(current_dir, "data", "chrome_profile_v2")
            os.makedirs(profile_dir, exist_ok=True)
            
            # Xóa các file LOCK cũ để tránh lỗi "chrome not reachable" do bị khóa profile
            try:
                import glob
                for lock_file in glob.glob(os.path.join(profile_dir, "**/LOCK"), recursive=True):
                    try:
                        os.remove(lock_file)
                    except Exception:
                        pass
            except Exception:
                pass
            
            # Nạp Profile mới (v2) để tránh kẹt profile cũ
            self._log("🌐 Đang mở Chrome với Profile mới (v2)...")
            chrome_version = None
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                version, _ = winreg.QueryValueEx(key, "version")
                chrome_version = int(version.split('.')[0])
                self._log(f"🔎 Đã phát hiện phiên bản Chrome: {chrome_version}")
            except Exception as ev:
                self._log(f"⚠️ Không thể phát hiện phiên bản Chrome từ registry: {ev}", "DEBUG")

            self.driver = uc.Chrome(
                options=options,
                version_main=chrome_version,
                user_data_dir=profile_dir,
                use_subprocess=True,
                suppress_welcome=True
            )

            try:
                self.wait = WebDriverWait(self.driver, 20)
            except Exception as e:
                self.driver.quit()
                self.driver = None
                raise e

            self.is_running = True

            self._log("✅ Trình duyệt đã khởi động thành công", "SUCCESS")
            return True

        except Exception as e:
            self._log(f"❌ Lỗi khởi động trình duyệt: {str(e)}", "ERROR")
            report_bug(exc=e, module="core.browser", task="start",
                       context={"headless": self.headless, "proxy": self.proxy or "none"},
                       severity="CRITICAL")
            return False

    def _kill_existing_chrome(self, executable_path: str):
        """Dọn dẹp tiến trình Chrome của riêng profile này để tránh kẹt Profile mà không ảnh hưởng Chrome khác"""
        try:
            import psutil
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            profile_dir = os.path.abspath(os.path.join(current_dir, "data", "chrome_profile_v2")).lower()
            
            count = 0
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        cmdline = proc.info['cmdline']
                        if cmdline:
                            cmd_str = " ".join(cmdline).lower()
                            if profile_dir in cmd_str:
                                proc.kill()
                                count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            import subprocess
            subprocess.run('taskkill /F /IM chromedriver.exe /T', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if count > 0:
                self._log(f"🧹 Đã dọn dẹp {count} tiến trình Chrome cũ đang mở profile của ToolAutoBcgame.")
            time.sleep(2)
        except Exception as e:
            self._log(f"⚠️ Lỗi khi dọn dẹp tiến trình Chrome: {e}", "DEBUG")



    def stop(self):
        """Đóng trình duyệt"""
        if self.driver:
            try:
                self.driver.quit()
                self._log("🔴 Trình duyệt đã đóng")
            except Exception:
                pass
            self.driver = None
            self.is_running = False

    def navigate(self, url: str) -> bool:
        """Điều hướng đến URL"""
        if not self.driver:
            return False
        try:
            self.driver.get(url)
            self._random_delay(1.5, 3.0)
            return True
        except WebDriverException as e:
            self._log(f"❌ Lỗi điều hướng: {str(e)}", "ERROR")
            return False

    def find_element(self, by: str, value: str, timeout: int = 10):
        """Tìm element với timeout"""
        if not self.driver:
            return None
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            return None
        except Exception:
            return None

    def find_elements(self, by: str, value: str, timeout: int = 10) -> list:
        """Tìm nhiều elements"""
        if not self.driver:
            return []
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return self.driver.find_elements(by, value)
        except Exception:
            return []

    def click_element(self, element, use_js: bool = False) -> bool:
        """Click vào element"""
        if not element:
            return False
        try:
            if use_js:
                self.driver.execute_script("arguments[0].click();", element)
            else:
                element.click()
            self._random_delay(0.3, 0.8)
            return True
        except ElementClickInterceptedException:
            try:
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except Exception:
                return False
        except Exception:
            return False

    def type_text(self, element, text: str, clear_first: bool = True, paste: bool = True):
        """Nhập text vào input field (mặc định gửi toàn bộ chuỗi ngay lập tức)"""
        if not element:
            return False
        try:
            from selenium.webdriver.common.keys import Keys
            if clear_first:
                try:
                    element.clear()
                except Exception: pass
                # Đảm bảo input đã được dọn sạch trong các trang React/Vue
                element.send_keys(Keys.CONTROL + "a")
                element.send_keys(Keys.DELETE)
            
            if paste:
                # Copy - Paste vật lý thật 100% bằng Clipboard của hệ điều hành
                try:
                    import pyperclip
                    pyperclip.copy(text)
                except ImportError:
                    import subprocess
                    # Fallback cho Windows nếu thiếu pyperclip
                    subprocess.run("clip", input=text.encode("utf-16"), check=True)
                
                # Bấm Ctrl + V để dán
                element.send_keys(Keys.CONTROL + 'v')
            else:
                # Giả lập gõ từng phím (dự phòng)
                for char in text:
                    element.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
            return True
        except Exception as e:
            self._log(f"❌ Lỗi nhập text: {str(e)}", "ERROR")
            return False

    def execute_script(self, script: str, *args):
        """Thực thi JavaScript"""
        if not self.driver:
            return None
        try:
            return self.driver.execute_script(script, *args)
        except Exception:
            return None

    def get_page_source(self) -> str:
        """Lấy source code trang hiện tại"""
        if not self.driver:
            return ""
        try:
            return self.driver.page_source
        except Exception:
            return ""

    def scroll_to_element(self, element):
        """Cuộn đến element"""
        if element and self.driver:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                element
            )
            self._random_delay(0.5, 1.0)

    def wait_for_element(self, by: str, value: str, timeout: int = 15):
        """Chờ element xuất hiện"""
        if not self.driver:
            return None
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
        except TimeoutException:
            return None

    def take_screenshot(self, filepath: str) -> bool:
        """Chụp screenshot"""
        if not self.driver:
            return False
        try:
            self.driver.save_screenshot(filepath)
            return True
        except Exception:
            return False

    def _random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """Delay ngẫu nhiên để giả lập người dùng"""
        time.sleep(random.uniform(min_sec, max_sec))

    @property
    def current_url(self) -> str:
        if not self.driver:
            return ""
        try:
            return self.driver.current_url
        except Exception:
            return ""

    @property
    def By(self):
        """Trả về By class từ Selenium"""
        from selenium.webdriver.common.by import By
        return By
