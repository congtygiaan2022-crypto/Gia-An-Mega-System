import json
import os
import sys
import logging
import random
import time
import re
import psutil
import subprocess
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger("GamsUtils")
logger.setLevel(logging.INFO)

class DataManager:
    def __init__(self, data_file):
        self.data_file = data_file
        self.links = self.load_links()

    def load_links(self):
        if not os.path.exists(self.data_file):
            return []
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading data: {e}")
            return []

    def save_links(self):
        for idx, link in enumerate(self.links):
            link['stt'] = idx + 1
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.links, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Error saving data: {e}")

    def update_link_status(self, index, status, data=None):
        if 0 <= index < len(self.links):
            self.links[index]['status'] = status
            if data:
                self.links[index]['data'] = data
                if 'total_followers' in data and data['total_followers']:
                     self.links[index]['total_followers'] = data['total_followers']
            
            # Update last scanned time
            self.links[index]['last_scanned'] = datetime.datetime.now().strftime("%H:%M %d/%m/%Y")
            self.save_links()

    def update_latest_post_info(self, index, date_val, title_val):
        if 0 <= index < len(self.links):
            self.links[index]['latest_post_date'] = date_val
            self.links[index]['latest_post_title'] = title_val
            self.save_links()

    def update_insight_and_post(self, index, status, data=None, post_info=None):
        if 0 <= index < len(self.links):
            self.links[index]['status'] = status
            if data:
                self.links[index]['data'] = data
                if 'total_followers' in data and data['total_followers']:
                     self.links[index]['total_followers'] = data['total_followers']
            if status == "Xong":
                if post_info:
                    self.links[index]['latest_post_date'] = post_info.get("date", "")
                    self.links[index]['latest_post_title'] = post_info.get("title", "")
                else:
                    self.links[index]['latest_post_date'] = "-"
                    self.links[index]['latest_post_title'] = "-"
            elif post_info:
                self.links[index]['latest_post_date'] = post_info.get("date", "")
                self.links[index]['latest_post_title'] = post_info.get("title", "")
            
            # Update last scanned time
            self.links[index]['last_scanned'] = datetime.datetime.now().strftime("%H:%M %d/%m/%Y")
            self.save_links()


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
            logger.info(f"Resolved chromedriver binary: {candidate}")
            return candidate

        # Also do a recursive walk limited to 2 levels deep
        for root, _dirs, files in os.walk(directory):
            depth = root[len(directory):].count(os.sep)
            if depth > 2:
                continue
            if exe_name in files:
                found = os.path.join(root, exe_name)
                logger.info(f"Resolved chromedriver binary (walk): {found}")
                return found

    # Fall back to the original path and let Selenium raise a meaningful error.
    logger.warning(
        f"Could not resolve a valid chromedriver binary from '{raw_path}'. "
        "Using original path as fallback."
    )
    return raw_path


class BrowserManager:
    def __init__(self, portable_path):
        self.driver = None
        self.portable_path = portable_path
        
    def check_alive(self):
        if not self.driver: return False
        try:
            _ = self.driver.current_url
            return True
        except: return False

    def launch_browser(self):
        # Kill ONLY Chrome processes using this exact profile dir (psutil — không kill Chrome khác)
        user_data_dir = os.path.abspath(os.path.join(os.getcwd(), "plugins", "data", "gams_insight", "user_data"))
        try:
            profile_dir_norm = os.path.normcase(os.path.normpath(user_data_dir))
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    name = (proc.info["name"] or "").lower()
                    if "chrome" not in name:
                        continue
                    cmdline = proc.info["cmdline"] or []
                    for arg in cmdline:
                        arg_norm = os.path.normcase(os.path.normpath(arg.split("=", 1)[-1]))
                        if "user-data-dir" in arg and arg_norm == profile_dir_norm:
                            try:
                                proc.terminate()
                            except Exception:
                                pass
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            time.sleep(1.5)
        except Exception:
            pass

        options = Options()
        options.binary_location = self.portable_path
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--log-level=3")
        options.add_argument("--silent")
        
        user_data_dir = os.path.abspath(os.path.join(os.getcwd(), "plugins", "data", "gams_insight", "user_data"))
        options.add_argument(f"user-data-dir={user_data_dir}")

        try:
            driver_path = ChromeDriverManager().install()
            driver_path = _resolve_chromedriver_path(driver_path)
            service = ChromeService(driver_path)
            if sys.platform == "win32":
                import subprocess
                try: service.creationflags = subprocess.CREATE_NO_WINDOW
                except AttributeError: service.creation_flags = subprocess.CREATE_NO_WINDOW
            self.driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            logger.error(f"Failed to launch Chrome driver: {e}")
            raise e

    def close_browser(self):
        if self.driver:
            try: self.driver.quit()
            except: pass
            self.driver = None
        # Kill ONLY Chrome processes using this exact profile dir (psutil — không kill Chrome khác)
        user_data_dir = os.path.abspath(os.path.join(os.getcwd(), "plugins", "data", "gams_insight", "user_data"))
        try:
            profile_dir_norm = os.path.normcase(os.path.normpath(user_data_dir))
            to_kill = []
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    name = (proc.info["name"] or "").lower()
                    if "chrome" not in name:
                        continue
                    cmdline = proc.info["cmdline"] or []
                    for arg in cmdline:
                        arg_norm = os.path.normcase(os.path.normpath(arg.split("=", 1)[-1]))
                        if "user-data-dir" in arg and arg_norm == profile_dir_norm:
                            to_kill.append(proc)
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            for p in to_kill:
                try:
                    p.terminate()
                except Exception:
                    pass
            if to_kill:
                gone, alive = psutil.wait_procs(to_kill, timeout=3.0)
                for p in alive:
                    try: p.kill()
                    except Exception: pass
        except Exception:
            pass

    def relaunch_browser(self):
        self.close_browser()
        time.sleep(2)
        self.launch_browser()

    def dismiss_popups(self) -> bool:
        if not self.driver:
            return False
        script_dismiss = r"""
        try {
            let closed = false;
            
            // 1. Target "Nhìn lại tuần qua" (Weekly Review) popup specifically
            const headings = Array.from(document.querySelectorAll('h1, h2, h3, div, span')).filter(el => {
                const text = el.innerText || "";
                return text.includes("Nhìn lại tuần qua") || text.includes("Look back at last week");
            });
            
            if (headings.length > 0) {
                let parent = headings[0];
                for (let depth = 0; depth < 5; depth++) {
                    if (!parent) break;
                    const xBtns = Array.from(parent.querySelectorAll('[aria-label*="Đóng" i], [aria-label*="Close" i], button, [role="button"], div, span'));
                    for (let x of xBtns) {
                        const aria = (x.getAttribute('aria-label') || "").toLowerCase();
                        const text = (x.innerText || "").trim().toLowerCase();
                        if (aria === "đóng" || aria === "close" || text === "x" || text === "đóng" || text === "close" || aria.includes("đóng") || aria.includes("close")) {
                            x.click();
                            closed = true;
                            break;
                        }
                    }
                    if (closed) break;
                    parent = parent.parentElement;
                }
            }
            
            // 2. Try to find popups by typical modal roles and classes
            if (!closed) {
                const popups = Array.from(document.querySelectorAll('[role="dialog"], .role-dialog, [role="alertdialog"], .modal, .dialog, [aria-modal="true"]'));
                for (let popup of popups) {
                    const buttons = Array.from(popup.querySelectorAll('button, div[role="button"], span[role="button"], a[role="button"]'));
                    for (let btn of buttons) {
                        const text = (btn.innerText || "").trim().toLowerCase();
                        const ariaLabel = (btn.getAttribute("aria-label") || "").trim().toLowerCase();
                        if (["đóng", "close", "hủy", "cancel", "bỏ qua", "skip", "dismiss", "x", "ok", "đã hiểu", "got it", "not now", "lúc khác"].includes(text) ||
                            ["close", "đóng", "dismiss", "x"].includes(ariaLabel)) {
                            btn.click();
                            closed = true;
                            break;
                        }
                    }
                    if (!closed) {
                        const xBtns = Array.from(popup.querySelectorAll('[aria-label*="Close" i], [aria-label*="Đóng" i], [aria-label*="Dismiss" i], .close-button, .close, [class*="close" i]'));
                        for (let xBtn of xBtns) {
                            if (xBtn.offsetWidth > 0 && xBtn.offsetHeight > 0) {
                                xBtn.click();
                                closed = true;
                                break;
                            }
                        }
                    }
                }
            }
            
            // 3. Global check for close elements (aria-labels)
            if (!closed) {
                const closeSelectors = [
                    '[aria-label="Đóng"]',
                    '[aria-label="Close"]',
                    '[aria-label="Dismiss"]',
                    '[aria-label*="Đóng" i]',
                    '[aria-label*="Close" i]',
                    '.close',
                    '[class*="close-button"]'
                ];
                for (let sel of closeSelectors) {
                    const elements = Array.from(document.querySelectorAll(sel));
                    for (let el of elements) {
                        if (el.offsetWidth > 0 && el.offsetHeight > 0) {
                            el.click();
                            closed = true;
                            break;
                        }
                    }
                    if (closed) break;
                }
            }
            
            // 4. Global check for buttons with close labels
            if (!closed) {
                const globalCloseTexts = ["đóng", "close", "bỏ qua", "skip", "đã hiểu", "got it", "not now", "lúc khác"];
                const allButtons = Array.from(document.querySelectorAll('button, [role="button"], span[role="button"]'));
                for (let btn of allButtons) {
                    const text = (btn.innerText || "").trim().toLowerCase();
                    if (globalCloseTexts.includes(text) && btn.offsetWidth > 0 && btn.offsetHeight > 0) {
                        btn.click();
                        closed = true;
                        break;
                    }
                }
            }
            return closed;
        } catch(e) { return false; }
        """
        try:
            any_closed = False
            for _ in range(3):
                res = self.driver.execute_script(script_dismiss)
                if res:
                    any_closed = True
                    logger.info("Dismissed a popup on Facebook.")
                    time.sleep(1.0)
                else:
                    break
            return any_closed
        except Exception as e:
            logger.warning(f"Lỗi khi kiểm tra/tắt popup: {e}")
            return False

    def navigate_to(self, url):
        if not self.check_alive(): self.launch_browser()
        try:
            self.driver.get(url)
            time.sleep(2)
            self.dismiss_popups()
            return True
        except:
            self.relaunch_browser()
            try:
                self.driver.get(url)
                time.sleep(2)
                self.dismiss_popups()
                return True
            except: return False

    def scroll_page(self):
        if not self.driver: return
        total_height = int(self.driver.execute_script("return document.body.scrollHeight"))
        for i in range(1, min(total_height, 3000), 500):
            self.driver.execute_script(f"window.scrollTo(0, {i});")
            time.sleep(0.2)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

    def localize_facebook_date(self, date_str):
        if not date_str:
            return ""
        import datetime
        import re

        s = date_str.strip()
        s_clean = re.sub(r'\s+', ' ', s).lower()

        # Remove day of week to avoid relative time conflicts (e.g. "thứ 3 ngày 6" -> "ngày 6")
        s_clean = re.sub(r'\bthứ\s+\d+\b', '', s_clean)
        s_clean = re.sub(r'\bthứ\s+(?:hai|ba|tư|năm|sáu|bảy)\b', '', s_clean)
        s_clean = re.sub(r'\bchủ\s+nhật\b', '', s_clean)

        now = datetime.datetime.now()
        year = now.year

        # Check relative hours
        m = re.search(r'(\d+)\s*(?:giờ|h|hrs|hours?)\b', s_clean)
        if m:
            h = int(m.group(1))
            val = now - datetime.timedelta(hours=h)
            return val.strftime("%H:%M %d/%m/%Y")

        # Check relative days
        m = re.search(r'(\d+)\s*(?:ngày|d|days?)\b', s_clean)
        if m:
            d = int(m.group(1))
            val = now - datetime.timedelta(days=d)
            return val.strftime("%H:%M %d/%m/%Y")

        if any(k in s_clean for k in ["vừa xong", "vừa mới", "just now", "vài giây"]):
            return now.strftime("%H:%M %d/%m/%Y")

        # Extract time
        time_match = re.search(r'(\d{1,2}):(\d{2})', s_clean)
        hours = 0
        mins = 0
        if time_match:
            hours = int(time_match.group(1))
            mins = int(time_match.group(2))
            if "pm" in s_clean and hours < 12:
                hours += 12
            if "am" in s_clean and hours == 12:
                hours = 0

        # Extract year
        yr_match = re.search(r'\b(20\d{2})\b', s_clean)
        if yr_match:
            year = int(yr_match.group(1))

        # Extract month
        months_en = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        month = now.month
        
        m_vn = re.search(r'(?:tháng|thg)\s*(\d{1,2})', s_clean)
        if m_vn:
            month = int(m_vn.group(1))
        else:
            for idx, m_en in enumerate(months_en):
                if m_en in s_clean:
                    month = idx + 1
                    break

        # Extract day
        day = now.day
        s_temp = s_clean
        if yr_match:
            s_temp = s_temp.replace(yr_match.group(1), "")
        if time_match:
            s_temp = s_temp.replace(time_match.group(0), "")
            
        m_vn_full = re.search(r'(?:tháng|thg)\s*\d{1,2}', s_temp)
        if m_vn_full:
            s_temp = s_temp.replace(m_vn_full.group(0), "")
        else:
            for m_en in months_en:
                s_temp = s_temp.replace(m_en, "")
                
        day_match = re.search(r'\b(\d{1,2})\b', s_temp)
        if day_match:
            day = int(day_match.group(1))
        else:
            all_nums = re.findall(r'\b(\d{1,2})\b', s_clean)
            for num in all_nums:
                val = int(num)
                if 1 <= val <= 31 and val != month:
                    day = val
                    break

        try:
            dt = datetime.datetime(year, month, day, hours, mins)
            if dt > now and not yr_match:
                dt = dt.replace(year=year - 1)
            return dt.strftime("%H:%M %d/%m/%Y")
        except:
            return s

    def extract_latest_post_date(self):
        if not self.driver: return None
        script = r"""
        try {
            // Find "Nội dung mới đây" or "Recent content" header
            const headers = Array.from(document.querySelectorAll('*')).filter(el => {
                const text = el.innerText || "";
                return (text === "Nội dung mới đây" || text === "Recent content" || text === "Nội dung mới nhất") && el.children.length === 0;
            });
            
            let header = headers[0];
            if (!header) {
                const fallbackHeaders = Array.from(document.querySelectorAll('*')).filter(el => {
                    const text = (el.textContent || "").trim();
                    return text === "Nội dung mới đây" || text === "Recent content";
                });
                if (fallbackHeaders.length === 0) {
                    return null;
                }
                header = fallbackHeaders[0];
            }
            
            // Walk up to find the card container
            let card = header;
            while (card && card.parentElement && card.innerText.length < 150) {
                card = card.parentElement;
            }
            if (!card) return null;
            
            // Find all leaf elements in this card
            const elements = Array.from(card.querySelectorAll('*')).filter(el => el.children.length === 0 && (el.innerText || "").trim().length > 0);
            
            // Look for first date-like element
            const dateRegex = /(tháng|thg|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{1,2}\s*(?:giờ|ngày|phút|h|d|min|ago|y|m))/i;
            let dateIdx = -1;
            for (let i = 0; i < elements.length; i++) {
                const text = elements[i].innerText || "";
                if (dateRegex.test(text) && text.match(/\d/)) {
                    if (text.includes(':') || text.match(/(tháng|thg|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/i)) {
                        dateIdx = i;
                        break;
                    }
                }
            }
            if (dateIdx === -1) return null;
            
            let dateVal = elements[dateIdx].innerText.trim();
            let titleVal = "";
            for (let i = dateIdx - 1; i >= 0; i--) {
                const text = elements[i].innerText.trim();
                if (text.length > 5 && text !== "Xem tất cả nội dung" && text !== "Nội dung mới đây" && text !== "Recent content" && !text.match(/^[\d\.,\+%-]+[KMB]?$/)) {
                    titleVal = text;
                    break;
                }
            }
            return {date: dateVal, title: titleVal};
        } catch(e) { return null; }
        """
        res = self.driver.execute_script(script)
        if res and res.get("date"):
            res["date"] = self.localize_facebook_date(res["date"])
            return res
        return None

    def localize_time_range(self, range_str):
        if not range_str: return ""
        import re
        result = range_str.strip()
        result = re.sub(r'\s+', ' ', result)
        result = re.sub(r'\s*[–-]\s*', ' – ', result)
        
        months_map = {
            "january": "thg 1", "february": "thg 2", "march": "thg 3", "april": "thg 4",
            "may": "thg 5", "june": "thg 6", "july": "thg 7", "august": "thg 8",
            "september": "thg 9", "october": "thg 10", "november": "thg 11", "december": "thg 12",
            "jan": "thg 1", "feb": "thg 2", "mar": "thg 3", "apr": "thg 4",
            "may": "thg 5", "jun": "thg 6", "jul": "thg 7", "aug": "thg 8",
            "sep": "thg 9", "oct": "thg 10", "nov": "thg 11", "dec": "thg 12",
            "tháng 1": "thg 1", "tháng 2": "thg 2", "tháng 3": "thg 3", "tháng 4": "thg 4",
            "tháng 5": "thg 5", "tháng 6": "thg 6", "tháng 7": "thg 7", "tháng 8": "thg 8",
            "tháng 9": "thg 9", "tháng 10": "thg 10", "tháng 11": "thg 11", "tháng 12": "thg 12"
        }
        
        result_lower = result.lower()
        for m_en, m_vi in months_map.items():
            result_lower = re.sub(r'\b' + m_en + r'\s+(\d{1,2})\b', r'\1 ' + m_vi, result_lower)
            result_lower = re.sub(r'\b(\d{1,2})\s+' + m_en + r'\b', r'\1 ' + m_vi, result_lower)
            
        return result_lower.strip()

    def extract_insight_data(self):
        if not self.driver: return {}
        self.dismiss_popups()
        self.scroll_page()
        self.dismiss_popups()
        try:
            body_text = ""
            for attempt in range(2):
                body_text = self.driver.find_element(By.TAG_NAME, "body").text
                
                # Check for Facebook Business Suite loading errors
                error_keywords = [
                    "Rất tiếc, đã xảy ra lỗi",
                    "Vui lòng tải lại trang",
                    "Something went wrong",
                    "Please reload the page",
                    "Trang này hiện không hiển thị được",
                    "This page isn't available right now"
                ]
                
                has_error = any(k in body_text for k in error_keywords)
                is_short = len(body_text.strip()) < 100
                
                if has_error or is_short:
                    if attempt == 0:
                        reason = "lỗi tải trang Facebook" if has_error else "trang quá ngắn"
                        logger.warning(f"Phát hiện {reason}. Đang thử làm mới trang (refresh)...")
                        self.driver.refresh()
                        time.sleep(10)
                        self.scroll_page()
                        continue
                    else:
                        if has_error:
                            raise ValueError("Phát hiện lỗi tải trang của Facebook Business Suite (Rất tiếc, đã xảy ra lỗi / Something went wrong).")
                        else:
                            raise ValueError("Trang tải về rỗng hoặc quá ngắn (có thể chưa tải xong).")
                break
                
            lines = body_text.split('\n')
            data = {}
            # 1. Extract Time Range
            time_range = ""
            for line in lines:
                line = line.strip()
                if "–" in line or " - " in line or " – " in line:
                    if any(m in line.lower() for m in ["thg", "tháng", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec", "202"]):
                        parts = line.split(":")
                        candidate = parts[-1].strip()
                        if len(candidate) >= 10 and ("–" in candidate or "-" in candidate):
                            time_range = self.localize_time_range(candidate)
                            break
                            
            if not time_range:
                regex_list = [
                    r"(\d{1,2}\s+(?:thg|tháng)\s+\d{1,2}\s*[–-]\s*\d{1,2}\s+(?:thg|tháng)\s+\d{1,2},\s*\d{4})",
                    r"([A-Za-z]{3,}\s+\d{1,2}\s*[–-]\s*[A-Za-z]{3,}\s+\d{1,2},\s*\d{4})",
                    r"(\d{1,2}\s+(?:thg|tháng)\s+\d{1,2},\s*\d{4}\s*[–-]\s*\d{1,2}\s+(?:thg|tháng)\s+\d{1,2},\s*\d{4})",
                    r"([A-Za-z]{3,}\s+\d{1,2},\s*\d{4}\s*[–-]\s*[A-Za-z]{3,}\s+\d{1,2},\s*\d{4})",
                    r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\s*[–-]\s*\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
                    r"(\d{1,2}\s+(?:thg|tháng)\s+\d{1,2}\s*[–-]\s*\d{1,2}\s+(?:thg|tháng)\s+\d{1,2})",
                    r"([A-Za-z]{3,}\s+\d{1,2}\s*[–-]\s*[A-Za-z]{3,}\s+\d{1,2})"
                ]
                for rg in regex_list:
                    m = re.search(rg, body_text)
                    if m:
                        time_range = self.localize_time_range(m.group(1))
                        break
            
            if not time_range:
                if "Last 28 days" in body_text: time_range = "Last 28 days"
                elif "28 ngày qua" in body_text: time_range = "28 ngày qua"
                elif "Last 7 days" in body_text: time_range = "Last 7 days"
                elif "7 ngày qua" in body_text: time_range = "7 ngày qua"

            if time_range:
                data["Thời gian"] = time_range

            # 2. Extract Metrics
            key_map = {
                # English keys
                "Content interactions": "Lượt tương tác",
                "Facebook visits": "Lượt xem trang",
                "Views": "Lượt xem",
                "Follows": "Lượt theo dõi",
                "New contacts": "Liên hệ mới",
                "Reach": "Số người tiếp cận",
                # Vietnamese keys
                "Lượt tương tác": "Lượt tương tác",
                "Lượt tương tác với nội dung": "Lượt tương tác",
                "Số lượt xem trang": "Lượt xem trang",
                "Lượt xem trang": "Lượt xem trang",
                "Lượt truy cập trên Facebook": "Lượt xem trang",
                "Lượt truy cập": "Lượt xem trang",
                "Lượt xem": "Lượt xem",
                "Lượt theo dõi": "Lượt theo dõi",
                "Số người tiếp cận": "Số người tiếp cận",
                "Lượt bắt đầu cuộc trò chuyện": "Lượt tương tác",
                "Người liên hệ mới": "Liên hệ mới"
            }
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line in key_map:
                    target_key = key_map[line]
                    if i + 1 < len(lines):
                        val_line = lines[i+1].strip()
                        # Match numbers, K, M, B, dots, commas OR hyphens/dashes, including Vietnamese scale words
                        if re.match(r'^([+-]?[\d\.,\s]+(?:triệu|tỷ|nghìn|ngàn|K|M|B)?|‑‑|--|-)$', val_line, re.IGNORECASE):
                            val = val_line
                            if val in ["‑‑", "--", "-"]:
                                val = "0"
                            # Check for percentage change line (+5% or -10%)
                            elif i + 2 < len(lines) and "%" in lines[i+2]:
                                 val += f" ({lines[i+2].strip()})"
                            data[target_key] = val
            
            # Extract total followers
            followers_match = re.search(r"([\d\.,]+[KMB]?)\s+(followers|người theo dõi|Followers|Người theo dõi)", body_text)
            if followers_match:
                data["total_followers"] = followers_match.group(1)
                
            return data
        except Exception as e:
            logger.error(f"Error extracting data: {e}")
            return {}

    def get_totp_code(self, secret: str) -> str:
        import pyotp
        secret = secret.replace(" ", "").replace("-", "").upper()
        totp = pyotp.TOTP(secret)
        return totp.now()

    def _is_logged_in(self) -> bool:
        if not self.driver:
            return False
        url = self.driver.current_url
        if "facebook.com" not in url or "login" in url or "checkpoint" in url or "two_step" in url:
            return False
        # Look for typical logged in elements
        elements = self.driver.find_elements(By.CSS_SELECTOR,
            "[data-pagelet='LeftRail'], [aria-label='Your profile'], [data-testid='royal_blue_bar'], [aria-label='Facebook'][role='navigation']")
        return len(elements) > 0

    def _handle_2fa(self, two_factor_secret: str) -> bool:
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        if not two_factor_secret:
            logger.warning("Trang 2FA xuất hiện nhưng không có secret key")
            return False

        try:
            code = self.get_totp_code(two_factor_secret)
            logger.info(f"2FA code generated: {code} — xử lý trang 2FA...")

            # Nếu trang hiện "Kiểm tra thông báo thiết bị khác" → click "Thử cách khác"
            try:
                try_other = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH,
                        "//span[contains(text(),'Thử cách khác') or contains(text(),'Try another way') "
                        "or contains(text(),'Use a different method')]/.."
                        "|//a[contains(text(),'Thử cách khác') or contains(text(),'Try another way')]"
                        "|//div[@role='button'][contains(.,'Thử cách khác') or contains(.,'Try another way')]"
                    ))
                )
                try_other.click()
                logger.info("Đã click 'Thử cách khác'")
                WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, "//*"))
                )
            except Exception:
                pass

            # Chọn "Ứng dụng xác thực" / Authenticator App nếu có menu lựa chọn
            try:
                auth_app_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH,
                        "//span[contains(text(),'Ứng dụng xác thực') or contains(text(),'Authentication app') "
                        "or contains(text(),'Authenticator app')]/.."
                        "|//div[@role='radio'][.//*[contains(text(),'Ứng dụng xác thực') or contains(text(),'Authentication app')]]"
                        "|//label[.//*[contains(text(),'Ứng dụng xác thực') or contains(text(),'Authentication app')]]"
                    ))
                )
                auth_app_btn.click()
                logger.info("Đã chọn 'Ứng dụng xác thực'")
                
                try:
                    continue_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH,
                            "//span[contains(text(),'Tiếp tục') or contains(text(),'Continue')]/.."
                            "|//button[contains(text(),'Tiếp tục') or contains(text(),'Continue')]"
                            "|//div[@role='button'][.//*[contains(text(),'Tiếp tục') or contains(text(),'Continue')]]"
                        ))
                    )
                    continue_btn.click()
                    logger.info("Đã click 'Tiếp tục'")
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//input"))
                    )
                except Exception:
                    pass
            except Exception:
                pass

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
            
            self.driver.implicitly_wait(0)
            end_time = time.time() + 15
            while time.time() < end_time:
                for sel_type, sel_val in selectors:
                    try:
                        elements = self.driver.find_elements(sel_type, sel_val)
                        for el in elements:
                            if el.is_displayed() and el.is_enabled():
                                otp_field = el
                                logger.info(f"Tìm thấy 2FA input: {sel_val[:60]}")
                                break
                        if otp_field: break
                    except Exception:
                        pass
                if otp_field: break
                time.sleep(0.5)
                
            self.driver.implicitly_wait(10)

            if otp_field is None:
                logger.error("Không tìm thấy ô nhập mã 2FA")
                return False

            code = self.get_totp_code(two_factor_secret)
            otp_field.click()
            otp_field.clear()
            otp_field.send_keys(code)
            logger.info(f"Đã nhập mã 2FA: {code}")

            submit = None
            submit_selectors = [
                "//button[@id='checkpointSubmitButton']",
                "//button[@type='submit']",
                "//input[@type='submit']",
                "//span[text()='Tiếp tục' or text()='Continue' or text()='Submit']/..",
                "//div[@role='button'][.//*[text()='Tiếp tục' or text()='Continue']]",
                "//button[contains(.,'Tiếp tục') or contains(.,'Continue') or contains(.,'Submit')]",
            ]
            
            self.driver.implicitly_wait(0)
            end_time = time.time() + 5
            while time.time() < end_time:
                for sel in submit_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, sel)
                        for el in elements:
                            if el.is_displayed() and el.is_enabled():
                                submit = el
                                logger.info(f"Tìm thấy submit button: {sel[:50]}")
                                break
                        if submit: break
                    except Exception:
                        pass
                if submit: break
                time.sleep(0.5)
                
            self.driver.implicitly_wait(10)

            if submit is None:
                otp_field.send_keys("\n")
                logger.info("Không tìm thấy submit button — dùng Enter")
            else:
                submit.click()
            
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda d: "checkpoint" not in d.current_url and "two_step" not in d.current_url
                )
            except Exception:
                pass
            return True
        except Exception as e:
            logger.error(f"Lỗi khi nhập 2FA: {e}")
            return False

    def login_facebook(self, username, password, two_factor_secret) -> bool:
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        if not self.driver:
            self.launch_browser()

        logger.info("Kiểm tra session Facebook đã lưu...")
        self.driver.get("https://www.facebook.com/")
        
        try:
            WebDriverWait(self.driver, 5).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, "[aria-label='Facebook'][role='navigation'], [data-pagelet='LeftRail'], [aria-label='Your profile'], [data-testid='royal_blue_bar']") or 
                          "login" in d.current_url or "checkpoint" in d.current_url
            )
        except Exception:
            pass

        if self._is_logged_in():
            logger.info("Đã đăng nhập từ session đã lưu — bỏ qua bước login")
            return True

        logger.info("Đang mở trang đăng nhập Facebook...")
        self.driver.get("https://www.facebook.com/login")
        wait = WebDriverWait(self.driver, 15)

        try:
            try:
                email_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='email']")))
            except Exception:
                if self._is_logged_in():
                    logger.info("Đã đăng nhập thành công (tự động chuyển hướng)")
                    return True
                raise

            email_field.click()
            email_field.clear()
            email_field.send_keys(username)

            pass_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='pass'], input[id='pass']")))
            pass_field.click()
            pass_field.clear()
            pass_field.send_keys(password)

            pass_field.send_keys("\n")
            
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda d: "login" not in d.current_url or 
                              d.find_elements(By.CSS_SELECTOR, "[aria-label='Facebook'][role='navigation'], [data-pagelet='LeftRail'], [aria-label='Your profile']") or
                              "checkpoint" in d.current_url or "two_step" in d.current_url
                )
            except Exception:
                pass

            captcha_wait = 0
            while captcha_wait < 120:
                url = self.driver.current_url
                if "login" not in url:
                    break
                try:
                    recaptcha_frames = self.driver.find_elements(By.XPATH,
                        "//iframe[contains(@src,'recaptcha') or contains(@title,'reCAPTCHA')]"
                    )
                    if recaptcha_frames:
                        if captcha_wait == 0:
                            logger.warning("Facebook hiển thị CAPTCHA — hãy giải thủ công trong cửa sổ Chrome (tối đa 120s)...")
                        time.sleep(5)
                        captcha_wait += 5
                        continue
                except Exception:
                    pass
                break

            if "checkpoint" in self.driver.current_url or "two_step" in self.driver.current_url:
                logger.info("Facebook yêu cầu xác thực 2FA...")
                if not self._handle_2fa(two_factor_secret):
                    return False
                
                try:
                    WebDriverWait(self.driver, 10).until(
                        lambda d: "checkpoint" not in d.current_url and "two_step" not in d.current_url
                    )
                except Exception:
                    pass

            try:
                WebDriverWait(self.driver, 15).until(
                    lambda d: "facebook.com" in d.current_url and "login" not in d.current_url and "two_step" not in d.current_url and "checkpoint" not in d.current_url
                )
            except Exception:
                pass

            if self._is_logged_in() or ("facebook.com" in self.driver.current_url and "login" not in self.driver.current_url and "two_step" not in self.driver.current_url):
                logger.info(f"Đăng nhập thành công — URL: {self.driver.current_url}")
                return True
            else:
                logger.error(f"Đăng nhập thất bại — URL: {self.driver.current_url}")
                return False
        except Exception as e:
            logger.error(f"Lỗi đăng nhập: {e}")
            return False
