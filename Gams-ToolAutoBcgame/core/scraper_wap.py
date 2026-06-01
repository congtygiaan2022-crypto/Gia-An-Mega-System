from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from loguru import logger
import json
import os
import re
import time

class WapScraper:
    """Module A: Quét dữ liệu từ bongda.wap.vn bằng Selenium"""
    
    URL = "https://bongda.wap.vn/nhan-dinh-bong-da.html"
    
    def __init__(self, browser: object = None, log_callback: Optional[callable] = None):
        self.browser = browser
        self.log_callback = log_callback

    def _log(self, message: str, level: str = "INFO"):
        if self.log_callback: self.log_callback(message, level)
        else: logger.info(message)

    def get_tai_matches(self) -> List[Dict]:
        """Lấy danh sách các trận có chữ 'TAI' (Gỡ bộ lọc thời gian ban đầu)"""
        self._log("🔍 Module A: Đang quét nhận định TÀI từ Wap.vn...")
        
        if not self.browser or not self.browser.driver:
            self._log("❌ Lỗi: Trình duyệt chưa khởi động!", "ERROR")
            return []

        try:
            # Đồng bộ giờ chuẩn từ time.is (Optionally)
            now = datetime.now()
            
            # Điều hướng tới Wap.vn
            self.browser.driver.get(self.URL)
            time.sleep(4) 
            
            html_content = self.browser.get_page_source()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            rows = soup.find_all('tr', class_='waptip3')
            matches = []
            
            for row in rows:
                cols = row.find_all('td', recursive=False)
                if len(cols) < 5: continue
                
                row_text = row.get_text().upper()
                if "TAI" in row_text or "TÀI" in row_text:
                    try:
                        time_str = cols[0].text.strip()
                        home_elem = cols[1].find('a')
                        away_elem = cols[3].find('a')
                        home = home_elem.text.strip() if home_elem else cols[1].get_text(separator=" ").strip()
                        away = away_elem.text.strip() if away_elem else cols[3].get_text(separator=" ").strip()
                        
                        home = re.sub(r'[\d\.\-]+$', '', home).strip()
                        away = re.sub(r'[\d\.\-]+$', '', away).strip()
                        
                        _font = cols[4].find('font') if len(cols) > 4 else None
                        tx_val = _font.text.strip() if _font else ""
                        
                        # Lấy Link Xem (Tìm trong tất cả thẻ <a>)
                        detail_url = ""
                        links = row.find_all('a')
                        for lnk in links:
                            if "XEM" in lnk.get_text().upper():
                                detail_url = lnk.get('href', '')
                                break
                        
                        if not detail_url:
                            # Không có link Xem -> kiểm tra có tỷ số không
                            row_text = row.get_text()
                            score_in_row = re.findall(r'\b(\d{1,2})\s*:\s*(\d{1,2})\b', row_text)
                            for s1, s2 in score_in_row:
                                h1, h2 = int(s1), int(s2)
                                is_clock = (h1 <= 23 and h2 <= 59 and h2 % 5 == 0)
                                if not is_clock and h1 <= 20 and h2 <= 20:
                                    self._log(f"⚠️ Hàng '{home}' không có link Xem + có tỷ số {s1}:{s2} -> Bỏ qua", "DEBUG")
                                    detail_url = "SKIP"  # Đánh dấu để bỏ qua
                                    break
                        
                        if detail_url == "SKIP":
                            continue

                        if not detail_url:
                            continue

                        if not detail_url.startswith('http'):
                            if detail_url.startswith('/'):
                                detail_url = "https://bongda.wap.vn" + detail_url
                            else:
                                detail_url = "https://bongda.wap.vn/" + detail_url

                        # BỎ BỘ LỌC THỜI GIAN - Lấy tất cả theo yêu cầu
                        display_text = f"{time_str} | {home} vs {away} - TÀI {tx_val}".strip()
                        matches.append({
                            "time_str": time_str,
                            "home": home,
                            "away": away,
                            "tx_val": tx_val,
                            "detail_url": detail_url,
                            "raw_line": display_text,
                            "date_scraped": now.strftime("%Y-%m-%d")
                        })
                    except Exception as e:
                        self._log(f"⚠️ Lỗi parse hàng trận: {e}", "DEBUG")
                        continue
            
            self._log(f"✅ Module A: Tìm thấy {len(matches)} trận TÀI (Đã gỡ lọc time).")
            self._save_to_database(matches)
            return matches

        except Exception as e:
            self._log(f"❌ Module A Lỗi: {str(e)}", "ERROR")
            return self._load_from_database()

    def check_match_status(self, detail_url: str, time_str: str = None) -> bool:
        """
        Kiểm tra xem trận đấu có CHƯA ĐÁ không.
        - Ưu tiên 1: So sánh time_str (giờ từ trang danh sách) với giờ hiện tại
        - Ưu tiên 2: Nếu không có link Xem → đã có tỷ số → bỏ qua
        - Ưu tiên 3: Mở trang chi tiết chỉ khi thời gian chưa rõ ràng
        """
        # Kiểm tra 1: Dùng time_str từ trang danh sách (Đáng tin cậy nhất)
        if time_str:
            now = datetime.now()
            match_dt = self._parse_time(time_str, now)
            if match_dt:
                if match_dt > (now + timedelta(minutes=10)):
                    # Chắc chắn chưa đá (còn hơn 10p nữa mới bắt đầu)
                    self._log(f"✅ Trận {time_str} chưa đá (còn {int((match_dt-now).total_seconds()//60)}p)", "DEBUG")
                    return True
                elif match_dt < (now - timedelta(minutes=90)):
                    # Chắc chắn đã đá xong (đá hơn 90p trước)
                    self._log(f"⚠️ Trận {time_str} đã đá xong (hơn 90p trước).", "WARNING")
                    return False
                # Nếu trong khoảng -90p đến +10p: cần check trang chi tiết

        # Kiểm tra 2: Không có link Xem = đã có tỷ số trên trang danh sách
        if not detail_url:
            self._log("⚠️ Không có link Xem -> Trận có tỷ số rồi, Bỏ qua.", "WARNING")
            return False
        
        # Kiểm tra 3: Mở trang chi tiết để xác nhận (chỉ khi thời gian mơ hồ)
        self._log(f"🔗 Đang kiểm tra chi tiết tại Wap.vn: {detail_url}")
        original_window = None
        _new_tab_opened = False
        try:
            try:
                original_window = self.browser.driver.current_window_handle
            except Exception:
                self._log("⚠️ Session trình duyệt lỗi. Cho qua.", "ERROR")
                return True  # Lỗi session → không biết → cho qua để BCGame kiểm tra tiếp

            self.browser.execute_script("window.open('');")
            _new_tab_opened = True
            self.browser.driver.switch_to.window(self.browser.driver.window_handles[-1])
            
            self.browser.driver.get(detail_url)
            time.sleep(3)
            
            soup = BeautifulSoup(self.browser.get_page_source(), 'html.parser')
            
            # Chỉ kiểm tra từ khóa rất đặc trưng (không có trong lịch sử phong độ)
            page_text = soup.get_text().lower()
            definitive_live_kw = ['đang diễn ra', 'đang thi đấu', 'hiệp 1:', 'hiệp 2:']
            if any(kw in page_text for kw in definitive_live_kw):
                self._log("⚠️ Xác nhận trận đang LIVE từ trang chi tiết.", "WARNING")
                try:
                    self.browser.driver.close()
                except Exception:
                    pass
                self.browser.driver.switch_to.window(original_window)
                return False

            try:
                self.browser.driver.close()
            except Exception:
                pass
            self.browser.driver.switch_to.window(original_window)
            return True  # Không có dấu hiệu live → coi là chưa đá

        except Exception as e:
            self._log(f"⚠️ Lỗi check detail: {e}", "DEBUG")
            try:
                if _new_tab_opened and len(self.browser.driver.window_handles) > 1:
                    self.browser.driver.close()
                if original_window:
                    self.browser.driver.switch_to.window(original_window)
            except Exception:
                pass
            return True  # Lỗi → cho qua, BCGame sẽ kiểm tra status thêm


    def _save_to_database(self, matches: List[Dict]):
        try:
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "matches_db.json")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(matches, f, ensure_ascii=False, indent=4)
        except Exception: pass

    def _load_from_database(self) -> List[Dict]:
        try:
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "matches_db.json")
            if os.path.exists(db_path):
                with open(db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception: pass
        return []

    def _parse_time(self, time_str: str, base_time: datetime = None) -> Optional[datetime]:
        try:
            if not base_time: base_time = datetime.now()
            h, m = map(int, time_str.split(':'))
            dt = base_time.replace(hour=h, minute=m, second=0, microsecond=0)
            if h < 6 and base_time.hour > 18:
                dt += timedelta(days=1)
            elif h > 18 and base_time.hour < 6:
                dt -= timedelta(days=1)
            return dt
        except Exception: return None
