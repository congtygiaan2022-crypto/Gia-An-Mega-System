"""
Scraper - Lấy dữ liệu trận đấu và tỷ lệ cược từ BCGame
"""
import time
import re
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from loguru import logger

from core.browser import BrowserController
from core.bug_tracker import report_bug

try:
    from selenium.webdriver.common.by import By
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


@dataclass
class MatchOdds:
    """Tỷ lệ cược 1X2"""
    home_win: float = 0.0
    draw: float = 0.0
    away_win: float = 0.0


@dataclass
class Match:
    """Thông tin một trận đấu"""
    match_id: str = ""
    league: str = ""
    home_team: str = ""
    away_team: str = ""
    start_time: str = ""
    status: str = "upcoming"   # upcoming | live | finished
    score_home: int = 0
    score_away: int = 0
    odds_1x2: MatchOdds = field(default_factory=MatchOdds)
    odds_over_under: Dict = field(default_factory=dict)
    odds_handicap: Dict = field(default_factory=dict)
    element: object = None    # Selenium element reference

    def __repr__(self):
        return (f"[{self.status.upper()}] {self.league} | "
                f"{self.home_team} vs {self.away_team} | "
                f"1X2: {self.odds_1x2.home_win}/{self.odds_1x2.draw}/{self.odds_1x2.away_win}")


class BCGameScraper:
    """Scraper cho BCGame Sports - Bóng đá"""

    SPORTS_URL = "https://bcvn2.com/vi/sports/soccer-1"

    def __init__(self, browser: BrowserController, log_callback: Optional[Callable] = None):
        self.browser = browser
        self.log_callback = log_callback
        self._matches_cache: List[Match] = []

    def _log(self, message: str, level: str = "INFO"):
        logger.info(message)
        if self.log_callback:
            self.log_callback(message, level)

    def navigate_to_sports(self) -> bool:
        """Điều hướng đến trang thể thao"""
        current = self.browser.current_url
        if "sports/soccer" not in current:
            return self.browser.navigate(self.SPORTS_URL)
        return True

    def get_matches(self, match_filter: str = "all",
                    min_odds: float = 1.0,
                    max_odds: float = 99.0,
                    leagues: List[str] = None) -> List[Match]:
        """
        Lấy danh sách trận đấu
        match_filter: 'all' | 'live' | 'upcoming'
        """
        self._log("🔍 Đang quét danh sách trận đấu...")
        matches = []

        try:
            # Chờ trang load xong
            time.sleep(2)

            # Cuộn để lazy-load thêm kèo (BCGame dùng virtual scroll)
            prev_count = 0
            for _ in range(8):
                match_rows_check = self._get_match_rows()
                if len(match_rows_check) == prev_count and prev_count > 0:
                    break
                prev_count = len(match_rows_check)
                self.browser.driver.execute_script("window.scrollBy(0, 600);")
                time.sleep(1.5)

            # Lấy tất cả các card trận đấu
            # BCGame dùng structure: section theo giải đấu, bên trong là các row trận
            match_rows = self._get_match_rows()

            self._log(f"📋 Tìm thấy {len(match_rows)} trận đấu")

            for row in match_rows:
                try:
                    match = self._parse_match_row(row)
                    if match:
                        # Lọc theo filter
                        if match_filter == "live" and match.status != "live":
                            continue
                        if match_filter == "upcoming" and match.status != "upcoming":
                            continue

                        # Lọc theo odds
                        if min_odds <= match.odds_1x2.home_win <= max_odds or \
                           min_odds <= match.odds_1x2.away_win <= max_odds:
                            matches.append(match)

                except Exception as e:
                    logger.debug(f"Lỗi parse trận: {e}")
                    continue

            self._matches_cache = matches
            return matches

        except Exception as e:
            self._log(f"❌ Lỗi quét trận đấu: {str(e)}", "ERROR")
            report_bug(exc=e, module="core.scraper", task="get_matches",
                       context={"filter": match_filter, "url": self.browser.current_url})
            return []

    def _get_match_rows(self) -> list:
        """Lấy danh sách row trận đấu từ DOM (Hỗ trợ xuyên Shadow DOM)"""
        js_get_rows = """
            function getRows(root) {
                let results = [];
                // Tìm các thẻ <a> chứa link trận đấu soccer hoặc class đặc thù
                let rows = root.querySelectorAll('a.bt230, a[href*="sports/soccer/"], [class*="match-item"]');
                for(let i=0; i<rows.length; i++) {
                    results.push({
                        element: rows[i],
                        text: rows[i].innerText || rows[i].textContent
                    });
                }
                
                let allNodes = root.querySelectorAll('*');
                for (let i = 0; i < allNodes.length; i++) {
                    if (allNodes[i].shadowRoot) {
                        results = results.concat(getRows(allNodes[i].shadowRoot));
                    }
                }
                return results;
            }
            return getRows(document);
        """
        try:
            return self.browser.driver.execute_script(js_get_rows) or []
        except Exception as e:
            self._log(f"⚠️ Lỗi quét kết quả Shadow DOM: {e}", "WARNING")
            return []

    def _parse_match_row(self, row_data) -> Optional[Match]:
        """Parse thông tin từ một row trận đấu"""
        try:
            # row_data có thể là WebElement (cũ) hoặc dict {'element': WebEle, 'text': str} (mới)
            if isinstance(row_data, dict):
                row_element = row_data['element']
                text = row_data['text']
            else:
                row_element = row_data
                text = row_element.text
                
            if not text or len(text.strip()) < 5:
                return None

            match = Match()
            match.element = row_element

            # Lấy tên đội
            team_elements = row_element.find_elements(By.XPATH,
                ".//*[contains(@class, 'team') or contains(@class, 'Team')]")
            
            if len(team_elements) >= 2:
                match.home_team = team_elements[0].text.strip()
                match.away_team = team_elements[1].text.strip()
            else:
                # Parse từ text
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                
                # Loại bỏ dòng chứa môn thể thao ("Soccer", "Bóng đá")
                lines = [l for l in lines if l.lower() not in ["soccer", "bóng đá", "football", "tennis", "basketball"]]
                
                # Dòng thời gian thường chứa :, /, -, hoặc "Hôm nay", "Ngày mai"
                time_keywords = [":", "/", "-", "hôm nay", "ngày mai", "today", "tomorrow"]
                
                team_lines = []
                for line in lines:
                    if not any(kw in line.lower() for kw in time_keywords) and len(line) > 2:
                        team_lines.append(line)
                
                if len(team_lines) >= 2:
                    match.home_team = team_lines[0]
                    match.away_team = team_lines[1]
                elif len(lines) >= 2:
                    # Fallback nếu filter quá khắt khe
                    match.home_team = lines[0]
                    match.away_team = lines[1]

            # Lấy odds (Bỏ qua nếu không cần thiết lúc tìm kiếm)
            # Không gán odds ở đây vì sẽ được quét riêng trong get_over_odds

            # Lấy giải đấu
            try:
                league_el = row_element.find_elements(By.XPATH,
                    "./ancestor::*[contains(@class, 'league') or contains(@class, 'competition')][1]")
                if league_el:
                    name_els = league_el[0].find_elements(By.XPATH, ".//*[contains(@class, 'name')]")
                    match.league = name_els[0].text if name_els else ""
            except Exception as e:
                logger.debug(f"Bỏ qua league parse: {e}")

            # Kiểm tra live/status (FIX CHÍNH XÁC: Tránh nhầm giờ thi đấu "2:00" là tỷ số "2-0")
            try:
                # 1. Loại bỏ bóng đá ảo
                if "(2x6" in text or "(3x10" in text or "Virtual" in text:
                    return None
                
                # 2. Nếu có từ khóa thời gian sắp đá thì CHẮC CHẮN là Upcoming
                upcoming_keywords = ["ngày mai", "hôm nay", "today", "tomorrow", "thg ", "tháng"]
                if any(kw in text.lower() for kw in upcoming_keywords):
                    match.status = "upcoming"
                else:
                    # 3. Chỉ coi là LIVE khi thấy phút thi đấu (45') hoặc HT/FT
                    # KHÔNG dùng tỷ số vì "2:00" là giờ thi đấu dễ bị nhầm!
                    live_indicators = re.search(r"\d+'|HT|FT", text)
                    match.status = "live" if live_indicators else "upcoming"
            except Exception:
                match.status = "upcoming"

            # Tạo ID từ tên đội
            match.match_id = f"{match.home_team}_{match.away_team}".replace(" ", "_").lower()

            if match.home_team and match.away_team:
                return match
            return None

        except Exception as e:
            logger.debug(f"Parse error: {e}")
            return None

    def find_match_element(self, match: Match):
        """Tìm lại element của trận đấu (refresh)"""
        try:
            elements = self._get_match_rows()
            for el in elements:
                text = el['text'] if isinstance(el, dict) else el.text
                if match.home_team in text and match.away_team in text:
                    match.element = el['element'] if isinstance(el, dict) else el
                    return match.element
        except Exception:
            pass
        return None

    def click_match(self, match: Match) -> bool:
        """Click vào trận đấu để xem chi tiết"""
        try:
            if not match.element:
                self.find_match_element(match)
            if match.element:
                self.browser.scroll_to_element(match.element)
                self.browser.click_element(match.element)
                time.sleep(1.5)
                return True
        except Exception as e:
            self._log(f"❌ Lỗi click trận: {str(e)}", "ERROR")
        return False

    def search_match(self, home: str, away: str) -> List[Match]:
        """Tìm kiếm trận đấu với cơ chế dự phòng và tối ưu hóa tốc độ tìm kiếm"""
        from core.selector import MatchSelector, normalize_name
        selector = MatchSelector()
        
        norm_home = normalize_name(home)
        norm_away = normalize_name(away)
        
        search_queries = []
        # Ưu tiên các từ khóa riêng lẻ trước (đội nhà, đội khách) vì tìm kiếm full vs thường lỗi
        if len(home.strip()) >= 3:
            search_queries.append(home.strip())
        if norm_home != home.lower() and len(norm_home) >= 3:
            search_queries.append(norm_home)
            
        if len(away.strip()) >= 3:
            search_queries.append(away.strip())
        if norm_away != away.lower() and len(norm_away) >= 3:
            search_queries.append(norm_away)
            
        # Thêm phương án sơ cua tìm cả hai
        full_query = f"{home} vs {away}"
        if len(full_query) >= 5:
            search_queries.append(full_query)
            
        # Lọc trùng lặp
        unique_queries = []
        for q in search_queries:
            if q not in unique_queries:
                unique_queries.append(q)
                
        # Điều hướng trang tìm kiếm một lần duy nhất ở đầu
        try:
            self.browser.navigate("https://bcvn2.com/vi/sports/search")
            time.sleep(2.0)
        except Exception as e:
            self._log(f"⚠️ Không thể hướng tới trang tìm kiếm: {e}", "WARNING")
            return []

        all_found_matches = []
        found_ids = set()

        for query in unique_queries:
            self._log(f"🔍 Đang tìm kiếm với từ khóa: '{query}'...")
            try:
                # Tìm ô input search trên trang hiện tại
                js_find_input = """
                    function findInput(root) {
                        let inputs = root.querySelectorAll('input');
                        for(let i=0; i<inputs.length; i++) {
                            let ph = (inputs[i].getAttribute('placeholder') || '').toLowerCase();
                            if (ph.includes('tìm') || ph.includes('search') || inputs[i].getAttribute('type') === 'search') return inputs[i];
                            if (inputs[i].offsetParent !== null) return inputs[i];
                        }
                        let allNodes = root.querySelectorAll('*');
                        for (let i = 0; i < allNodes.length; i++) {
                            if (allNodes[i].shadowRoot) {
                                let found = findInput(allNodes[i].shadowRoot);
                                if (found) return found;
                            }
                        }
                        return null;
                    }
                    return findInput(document);
                """
                search_input = self.browser.driver.execute_script(js_find_input)
                
                # Nếu không tìm thấy ô tìm kiếm, thử navigate lại làm fallback
                if not search_input:
                    self.browser.navigate("https://bcvn2.com/vi/sports/search")
                    time.sleep(2.0)
                    search_input = self.browser.driver.execute_script(js_find_input)
                    
                if search_input:
                    self.browser.click_element(search_input)
                    # Xóa nội dung cũ và gõ từ khóa mới
                    self.browser.type_text(search_input, query, clear_first=True, paste=True)
                    from selenium.webdriver.common.keys import Keys
                    search_input.send_keys(Keys.ENTER)
                    time.sleep(2.0)
                    
                    # Cuộn nhẹ để load kết quả
                    for scroll_idx in range(3):
                        self.browser.driver.execute_script("window.scrollBy(0, 300);")
                        time.sleep(1.0)
                        
                        match_rows = self._get_match_rows()
                        for row in match_rows:
                            match = self._parse_match_row(row)
                            if match and match.home_team and match.away_team:
                                m_id = f"{match.home_team}_{match.away_team}".lower()
                                if m_id not in found_ids:
                                    # Kiểm tra xem trận đấu này có phải là trận ta đang tìm không
                                    if selector.is_match_similar(home, away, match.home_team, match.away_team):
                                        self._log(f"🎯 Khớp thành công trận: {match.home_team} vs {match.away_team}!")
                                        return [match]
                                    all_found_matches.append(match)
                                    found_ids.add(m_id)
            except Exception as e:
                self._log(f"⚠️ Lỗi khi tìm kiếm '{query}': {e}", "WARNING")
                
        return all_found_matches

    def get_over_odds(self, match: Match) -> List[Dict]:
        """Lấy danh sách các kèo Tài (Over) xuyên qua Shadow DOM"""
        try:
            if not self.click_match(match):
                return []
                
            time.sleep(3)
            
            # Hàm JS tìm và click tab "Tổng cộng"
            js_click_tab = """
                function clickTotalTab(root) {
                    let els = root.querySelectorAll('div, button, span, a');
                    for(let i=0; i<els.length; i++) {
                        let t = (els[i].innerText || '').trim().toLowerCase();
                        if (t === 'tổng cộng' || t === 'tổng số bàn thắng' || t === 'tổng' || t === 'total' || t === 'over/under') {
                            els[i].click();
                            return true;
                        }
                    }
                    let allNodes = root.querySelectorAll('*');
                    for (let i = 0; i < allNodes.length; i++) {
                        if (allNodes[i].shadowRoot) {
                            if (clickTotalTab(allNodes[i].shadowRoot)) return true;
                        }
                    }
                    return false;
                }
                return clickTotalTab(document);
            """
            self.browser.driver.execute_script(js_click_tab)
            time.sleep(1.5)
            
            # JS Hợp nhất: Tìm và Click trong cùng 1 lần để đảm bảo chính xác
            js_bet_logic = """
                function betLogic(root, depth) {
                    depth = depth || 0;
                    if (depth > 20) return null;
                    
                    let main = document.querySelector('.sports-odds, #main-content, main, [class*="MatchDetails"]');
                    let searchRoot = (depth === 0 && main) ? main : root;
                    
                    let all = searchRoot.querySelectorAll('*');
                    for(let i=0; i < all.length; i++) {
                        let el = all[i];
                        let fullText = (el.innerText || el.textContent || '').trim();
                        let ft = fullText.toLowerCase();
                        
                        if(fullText.length > 0 && fullText.length < 40) {
                            if((ft.includes('trên') || ft.includes('tài') || ft.includes('over')) 
                               && ft.includes('0.5')
                               && !ft.match(/[1-9][.]5/)
                            ) {
                                // Kiểm tra odds
                                let lines = fullText.split(/\\r?\\n/);
                                let oddsVal = null;
                                for(let line of lines) {
                                    let n = parseFloat(line.trim());
                                    if(!isNaN(n) && n > 1.0 && n < 50) { oddsVal = n; break; }
                                }
                                
                                // Nếu tìm thấy odds hợp lệ, thực hiện click luôn
                                if (oddsVal && oddsVal > 1.0) {
                                    let rect = el.getBoundingClientRect();
                                    if(rect.width > 10 && rect.height > 10) {
                                        el.scrollIntoView({block: 'center'});
                                        el.click();
                                        return {clicked: true, text: fullText, odds: oddsVal};
                                    }
                                }
                            }
                        }
                        
                        if(el.shadowRoot) {
                            let r = betLogic(el.shadowRoot, depth + 1);
                            if(r) return r;
                        }
                    }
                    return null;
                }
                return betLogic(document);
            """
            
            result = self.browser.driver.execute_script(js_bet_logic)
            
            if result and result.get('clicked'):
                self._log(f"✅ Đã click kèo '{result['text']}' thành công qua JS!")
                return [{
                    "market": "trên 0.5",
                    "odds": result['odds'],
                    "element": None,
                    "_js_click_done": True # Đã click rồi không cần click lại
                }]
            else:
                self._log("⚠️ Không tìm thấy kèo Tài 0.5 để click.", "WARNING")
                return []

        except Exception as e:
            self._log(f"❌ Lỗi khi lấy kèo Tài: {str(e)}", "ERROR")
            report_bug(exc=e, module="core.scraper", task="get_over_odds",
                       context={"match": f"{match.home_team} vs {match.away_team}"})
            return []
