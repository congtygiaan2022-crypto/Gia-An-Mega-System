import re
import time
import requests
from bs4 import BeautifulSoup
from typing import Tuple
from loguru import logger
from selenium.webdriver.common.by import By
from thefuzz import fuzz
from datetime import datetime, timedelta
from core.selector import normalize_name

class GoogleAuditor:
    """Theo dõi kết quả trận đấu trên Google Search"""
    
    def __init__(self, browser):
        self.browser = browser

    def check_result(self, home_team: str, away_team: str) -> Tuple[str, int, int]:
        """Tìm kiếm kết quả trên Google"""
        query = f"{home_team} vs {away_team} score"
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        
        logger.info(f"🕵️ Đang check Google: {query}")

        original_window = None
        _new_tab_opened = False
        try:
            original_window = self.browser.driver.current_window_handle
            self.browser.driver.switch_to.new_window('tab')
            _new_tab_opened = True
            
            self.browser.navigate(search_url)
            time.sleep(3)
            
            html = self.browser.get_page_source()
            soup = BeautifulSoup(html, 'html.parser')
            
            status = "LIVE"
            h_score, a_score = 0, 0
            
            # Cấu trúc Google Sports Snippet
            score_elements = soup.find_all('div', {'class': re.compile(r'imso_mh__.*-sc')})
            if len(score_elements) >= 2:
                try:
                    h_score = int(score_elements[0].text.strip())
                    a_score = int(score_elements[1].text.strip())
                    logger.info(f"⚽ Tỷ số Google: {h_score} - {a_score}")
                except Exception as e: logger.debug(f"Parse score Google: {e}")
            else:
                match_score = re.search(r'\b(\d{1,2})\s*-\s*(\d{1,2})\b', soup.get_text())
                if match_score:
                    h_score = int(match_score.group(1))
                    a_score = int(match_score.group(2))
            
            end_keywords = ["Kết thúc", "Đã xong", "Final", "FT", "Full-time"]
            if any(kw in html for kw in end_keywords):
                status = "FIN"
            
            if len(self.browser.driver.window_handles) > 1:
                self.browser.driver.close()
            self.browser.driver.switch_to.window(original_window)
            return status, h_score, a_score

        except Exception as e:
            logger.error(f"❌ Lỗi check Google: {e}")
            try:
                if _new_tab_opened and len(self.browser.driver.window_handles) > 1:
                    self.browser.driver.close()
                if original_window:
                    self.browser.driver.switch_to.window(original_window)
            except Exception as e2: logger.debug(f"Window recovery failed: {e2}")
            return "ERROR", 0, 0

class FlashScoreAuditor:
    """Theo dõi kết quả trận đấu trên Flashscore.vn (Ưu tiên số 1)"""
    
    def __init__(self, browser):
        self.browser = browser

    def check_result(self, home_team: str, away_team: str) -> Tuple[str, int, int]:
        """Tìm kiếm kết quả trên Flashscore.vn bằng cách tương tác với thanh tìm kiếm trang chủ"""
        from core.selector import MatchSelector
        from selenium.webdriver.common.keys import Keys
        selector = MatchSelector()
        
        search_query = f"{home_team} {away_team}"
        logger.info(f"🕵️ Đang check Flashscore (Stealth): {search_query}")

        original_window = None
        _new_tab_opened = False
        try:
            original_window = self.browser.driver.current_window_handle
            self.browser.driver.switch_to.new_window('tab')
            _new_tab_opened = True
            
            # Điều hướng đến trang chủ
            self.browser.navigate("https://www.flashscore.vn/")
            time.sleep(4)
            
            # Chấp nhận cookie nếu có
            try:
                cookie_btn = self.browser.driver.find_elements(By.ID, "onetrust-accept-btn-handler")
                if cookie_btn:
                    cookie_btn[0].click()
                    time.sleep(1.5)
            except Exception:
                pass
                
            # Click nút tìm kiếm
            search_selectors = [
                "#search-window",
                ".header__search",
                ".header__searchIcon",
                "[class*='searchIcon']",
                "button[class*='search']"
            ]
            btn = None
            for sel in search_selectors:
                elements = self.browser.driver.find_elements(By.CSS_SELECTOR, sel)
                if elements:
                    for el in elements:
                        if el.is_displayed():
                            btn = el
                            break
                if btn:
                    break
                    
            if not btn:
                logger.warning("⚠️ Không tìm thấy nút tìm kiếm trên Flashscore!")
                if len(self.browser.driver.window_handles) > 1:
                    self.browser.driver.close()
                self.browser.driver.switch_to.window(original_window)
                return "NOT_FOUND", 0, 0
                
            self.browser.click_element(btn)
            time.sleep(2)
            
            # Tìm input tìm kiếm
            input_selectors = [
                "input[placeholder*='Tìm kiếm']",
                "input[placeholder*='Search']",
                "input[class*='search']",
                ".search__input"
            ]
            inp = None
            for sel in input_selectors:
                elements = self.browser.driver.find_elements(By.CSS_SELECTOR, sel)
                if elements:
                    for el in elements:
                        if el.is_displayed():
                            inp = el
                            break
                if inp:
                    break
                    
            if not inp:
                logger.warning("⚠️ Không tìm thấy ô nhập tìm kiếm trên Flashscore!")
                if len(self.browser.driver.window_handles) > 1:
                    self.browser.driver.close()
                self.browser.driver.switch_to.window(original_window)
                return "NOT_FOUND", 0, 0
                
            inp.send_keys(search_query)
            time.sleep(1.5)
            inp.send_keys(Keys.ENTER)
            time.sleep(4)
            
            html = self.browser.get_page_source()
            soup = BeautifulSoup(html, 'html.parser')
            
            match_links = soup.find_all(href=lambda href: href and "/trandau/" in href)
            target_href = None
            for el in match_links:
                text = el.text.strip()
                href = el.get('href')
                parts = [p.strip() for p in re.split(r'\s+[-–vsVS]\s+', text)]
                if len(parts) == 2:
                    if selector.is_match_similar(home_team, away_team, parts[0], parts[1], threshold=65):
                        logger.info(f"🎯 Khớp trận Flashscore: '{text}' cho '{home_team} vs {away_team}'")
                        target_href = href
                        break
                        
            if not target_href:
                logger.warning(f"⚠️ Không tìm thấy trận đấu khớp với '{home_team} vs {away_team}' trong danh sách kết quả.")
                if len(self.browser.driver.window_handles) > 1:
                    self.browser.driver.close()
                self.browser.driver.switch_to.window(original_window)
                return "NOT_FOUND", 0, 0
                
            # Điều hướng trực tiếp đến trang trận đấu
            self.browser.navigate("https://www.flashscore.vn" + target_href)
            time.sleep(4)
            
            html = self.browser.get_page_source()
            soup = BeautifulSoup(html, 'html.parser')
            
            h_score, a_score = 0, 0
            status = "LIVE"
            
            score_home_el = soup.select_one('.detailScore__wrapper span:nth-child(1)')
            score_away_el = soup.select_one('.detailScore__wrapper span:nth-child(3)')
            
            if score_home_el and score_away_el:
                h_str = re.sub(r'\D', '', score_home_el.text)
                a_str = re.sub(r'\D', '', score_away_el.text)
                if h_str and a_str:
                    h_score = int(h_str)
                    a_score = int(a_str)
            
            status_el = soup.select_one('.fixedHeader__status, .detailScore__status')
            if status_el:
                status_txt = status_el.text.strip()
                if any(kw in status_txt for kw in ["Kết thúc", "FT", "Finished", "Đã xong"]):
                    status = "FIN"
            
            logger.info(f"⚽ Tỷ số Flashscore: {h_score} - {a_score} ({status})")
            
            if len(self.browser.driver.window_handles) > 1:
                self.browser.driver.close()
            self.browser.driver.switch_to.window(original_window)
            return status, h_score, a_score
            
        except Exception as e:
            logger.error(f"❌ Lỗi Flashscore: {e}")
            try:
                if _new_tab_opened and len(self.browser.driver.window_handles) > 1:
                    self.browser.driver.close()
                if original_window:
                    self.browser.driver.switch_to.window(original_window)
            except Exception as e2: logger.debug(f"Window recovery failed: {e2}")
            return "ERROR", 0, 0

class ESPNAuditor:
    """Theo dõi kết quả trận đấu trên ESPN API (JSON, keyless, không CAPTCHA)"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback

    def _log(self, message: str, level: str = "INFO"):
        if self.log_callback:
            self.log_callback(message, level)
        else:
            logger.info(message)

    def check_result(self, home_team: str, away_team: str) -> Tuple[str, int, int]:
        """
        Tìm kiếm kết quả trên ESPN.
        status: "LIVE" | "FIN" | "NOT_FOUND" | "ERROR"
        """
        norm_home = normalize_name(home_team)
        norm_away = normalize_name(away_team)
        
        now = datetime.now()
        dates_to_check = [
            now.strftime("%Y%m%d"),
            (now - timedelta(days=1)).strftime("%Y%m%d"),
            (now + timedelta(days=1)).strftime("%Y%m%d")
        ]
        
        for date_str in dates_to_check:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={date_str}"
            try:
                response = requests.get(url, timeout=10)
                if response.status_code != 200:
                    continue
                
                data = response.json()
                events = data.get("events", [])
                
                for ev in events:
                    competitions = ev.get("competitions", [{}])
                    if not competitions:
                        continue
                    comp = competitions[0]
                    competitors = comp.get("competitors", [])
                    if len(competitors) < 2:
                        continue
                    
                    c_home = None
                    c_away = None
                    for c in competitors:
                        if c.get("homeAway") == "home":
                            c_home = c
                        elif c.get("homeAway") == "away":
                            c_away = c
                            
                    if not c_home or not c_away:
                        c_home = competitors[0]
                        c_away = competitors[1]
                        
                    espn_home = c_home.get("team", {}).get("displayName", "")
                    espn_away = c_away.get("team", {}).get("displayName", "")
                    
                    norm_eh = normalize_name(espn_home)
                    norm_ea = normalize_name(espn_away)
                    
                    match_direct = (
                        (fuzz.token_sort_ratio(norm_home, norm_eh) >= 70 or norm_home in norm_eh or norm_eh in norm_home) and
                        (fuzz.token_sort_ratio(norm_away, norm_ea) >= 70 or norm_away in norm_ea or norm_ea in norm_away)
                    )
                    match_reverse = (
                        (fuzz.token_sort_ratio(norm_home, norm_ea) >= 70 or norm_home in norm_ea or norm_ea in norm_home) and
                        (fuzz.token_sort_ratio(norm_away, norm_eh) >= 70 or norm_away in norm_eh or norm_eh in norm_away)
                    )
                    
                    if match_direct or match_reverse:
                        self._log(f"🎯 Khớp trận trên ESPN: {espn_home} vs {espn_away} (Từ khóa: {home_team} vs {away_team})", "SUCCESS")
                        
                        try:
                            h_score = int(c_home.get("score", 0))
                            a_score = int(c_away.get("score", 0))
                        except Exception:
                            h_score, a_score = 0, 0
                            
                        if match_reverse:
                            h_score, a_score = a_score, h_score
                            
                        state = ev.get("status", {}).get("type", {}).get("state", "").lower()
                        status = "LIVE"
                        if state == "post":
                            status = "FIN"
                        elif state == "pre":
                            status = "PRE"
                            
                        return status, h_score, a_score
                        
            except Exception as e:
                self._log(f"⚠️ Lỗi kết nối ESPN cho ngày {date_str}: {e}", "DEBUG")
                
        return "NOT_FOUND", 0, 0

class CombinedAuditor:
    """Kết hợp ESPN (JSON), Google và Flashscore (Dự phòng)"""
    def __init__(self, browser):
        log_callback = getattr(browser, 'log_callback', None)
        self.espn = ESPNAuditor(log_callback=log_callback)
        self.google = GoogleAuditor(browser)
        self.flash = FlashScoreAuditor(browser)

    def check_result(self, home_team: str, away_team: str) -> Tuple[str, int, int]:
        # 1. Thử ESPN trước (JSON API, keyless) - Không tốn browser/tab
        status, h, a = self.espn.check_result(home_team, away_team)
        if status not in ["ERROR", "NOT_FOUND"]:
            return status, h, a
            
        # 2. Fallback sang Google Search
        logger.info("⚠️ ESPN không tìm thấy, chuyển sang Google Search...")
        status, h, a = self.google.check_result(home_team, away_team)
        if status not in ["ERROR", "NOT_FOUND"]:
            return status, h, a
            
        # 3. Fallback sang Flashscore
        logger.info("⚠️ Google Search không tìm thấy, chuyển sang Flashscore...")
        return self.flash.check_result(home_team, away_team)

    def is_bet_won(self, threshold: float, score_home: int, score_away: int) -> bool:
        return (score_home + score_away) > threshold
