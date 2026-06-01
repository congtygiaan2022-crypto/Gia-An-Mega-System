"""
Auditor - Module C: Kiểm tra kết quả trận đấu từ Flashscore (Chính) và Google Search (Dự phòng)
"""
import re
import time
from bs4 import BeautifulSoup
from typing import Tuple
from loguru import logger
from selenium.webdriver.common.by import By

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
        try:
            original_window = self.browser.driver.current_window_handle
            self.browser.execute_script("window.open('');")
            self.browser.driver.switch_to.window(self.browser.driver.window_handles[-1])
            
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
                match_score = re.search(r'(\d+)\s*-\s*(\d+)', soup.get_text())
                if match_score:
                    h_score = int(match_score.group(1))
                    a_score = int(match_score.group(2))
            
            end_keywords = ["Kết thúc", "Đã xong", "Final", "FT", "Full-time"]
            if any(kw in html for kw in end_keywords):
                status = "FIN"
            
            self.browser.driver.close()
            self.browser.driver.switch_to.window(original_window)
            return status, h_score, a_score

        except Exception as e:
            logger.error(f"❌ Lỗi check Google: {e}")
            try:
                if original_window and len(self.browser.driver.window_handles) > 1:
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
        """Tìm kiếm kết quả trên Flashscore.vn"""
        search_query = f"{home_team} {away_team}"
        search_url = f"https://www.flashscore.vn/tim-kiem/?q={search_query.replace(' ', '+')}"
        
        logger.info(f"🕵️ Đang check Flashscore: {search_query}")

        original_window = None
        try:
            original_window = self.browser.driver.current_window_handle
            self.browser.execute_script("window.open('');")
            self.browser.driver.switch_to.window(self.browser.driver.window_handles[-1])
            
            self.browser.navigate(search_url)
            time.sleep(5)
            
            # Tìm trận đấu đầu tiên
            match_link = self.browser.find_element(By.CSS_SELECTOR, ".search__result, [id^='g_1_']", timeout=7)
            if match_link:
                self.browser.click_element(match_link)
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
                if status_el and any(kw in status_el.text for kw in ["Kết thúc", "FT", "Finished", "Đã xong"]):
                    status = "FIN"
                
                logger.info(f"⚽ Tỷ số Flashscore: {h_score} - {a_score} ({status})")
                
                self.browser.driver.close()
                self.browser.driver.switch_to.window(original_window)
                return status, h_score, a_score
            
            self.browser.driver.close()
            self.browser.driver.switch_to.window(original_window)
            return "NOT_FOUND", 0, 0
            
        except Exception as e:
            logger.error(f"❌ Lỗi Flashscore: {e}")
            try:
                if original_window and len(self.browser.driver.window_handles) > 1:
                    self.browser.driver.close()
                if original_window:
                    self.browser.driver.switch_to.window(original_window)
            except Exception as e2: logger.debug(f"Window recovery failed: {e2}")
            return "ERROR", 0, 0

class CombinedAuditor:
    """Kết hợp Flashscore (Chính) và Google (Dự phòng)"""
    def __init__(self, browser):
        self.flash = FlashScoreAuditor(browser)
        self.google = GoogleAuditor(browser)

    def check_result(self, home_team: str, away_team: str) -> Tuple[str, int, int]:
        # Thử Flashscore trước
        status, h, a = self.flash.check_result(home_team, away_team)
        if status not in ["ERROR", "NOT_FOUND"]:
            return status, h, a
            
        # Fallback sang Google
        logger.info("⚠️ Flashscore không tìm thấy, chuyển sang Google Search...")
        return self.google.check_result(home_team, away_team)

    def is_bet_won(self, threshold: float, score_home: int, score_away: int) -> bool:
        return (score_home + score_away) > threshold
