import time
import re
import sys
from core.browser import BrowserController
from core.selector import MatchSelector
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

sys.stdout.reconfigure(encoding='utf-8')

def test_flow(home_team, away_team):
    browser = BrowserController()
    if not browser.start():
        print("Failed to start browser")
        return
        
    selector = MatchSelector()
    
    try:
        print(f"Searching for: {home_team} vs {away_team}")
        print("Navigating to Flashscore.vn...")
        browser.navigate("https://www.flashscore.vn/")
        time.sleep(5)
        
        # Accept cookies
        cookie_btn = browser.driver.find_elements(By.ID, "onetrust-accept-btn-handler")
        if cookie_btn:
            print("Accepting cookies...")
            cookie_btn[0].click()
            time.sleep(2)
            
        # Click search icon
        search_selectors = [
            "#search-window",
            ".header__search",
            ".header__searchIcon",
            "[class*='searchIcon']",
            "button[class*='search']"
        ]
        
        btn = None
        for sel in search_selectors:
            elements = browser.driver.find_elements(By.CSS_SELECTOR, sel)
            if elements:
                for el in elements:
                    if el.is_displayed():
                        print(f"Found search button with selector: {sel}")
                        btn = el
                        break
            if btn:
                break
                
        if not btn:
            print("Search button not found!")
            return
            
        print("Opening search modal...")
        browser.click_element(btn)
        time.sleep(3)
        
        # Find input
        input_selectors = [
            "input[placeholder*='Tìm kiếm']",
            "input[placeholder*='Search']",
            "input[class*='search']",
            ".search__input"
        ]
        
        inp = None
        for sel in input_selectors:
            elements = browser.driver.find_elements(By.CSS_SELECTOR, sel)
            if elements:
                for el in elements:
                    if el.is_displayed():
                        print(f"Found search input with selector: {sel}")
                        inp = el
                        break
            if inp:
                break
                
        if not inp:
            print("Search input field not found!")
            return
            
        # Search query
        query = f"{home_team} {away_team}"
        print(f"Typing query: {query}")
        inp.send_keys(query)
        time.sleep(2)
        inp.send_keys(Keys.ENTER)
        time.sleep(5)
        
        # Get results page source
        html = browser.get_page_source()
        soup = BeautifulSoup(html, "html.parser")
        
        # Find all match links
        match_links = soup.find_all(href=lambda href: href and "/trandau/" in href)
        print(f"Found {len(match_links)} links containing '/trandau/'")
        
        target_href = None
        for el in match_links:
            text = el.text.strip()
            href = el.get('href')
            print(f"Found link: {text} | href: {href}")
            
            # Split by - or vs
            parts = [p.strip() for p in re.split(r'\s+[-–vsVS]\s+', text)]
            if len(parts) == 2:
                # Use MatchSelector to match
                similar = selector.is_match_similar(home_team, away_team, parts[0], parts[1], threshold=65)
                if similar:
                    print(f"🎉 Matched link: '{text}' matches '{home_team} vs {away_team}'")
                    target_href = href
                    break
                    
        if target_href:
            # Navigate directly
            full_url = "https://www.flashscore.vn" + target_href
            print(f"Navigating to match URL: {full_url}")
            browser.navigate(full_url)
            time.sleep(5)
            
            # Audit score
            detail_html = browser.get_page_source()
            detail_soup = BeautifulSoup(detail_html, "html.parser")
            
            h_score, a_score = 0, 0
            status = "LIVE"
            
            score_home_el = detail_soup.select_one('.detailScore__wrapper span:nth-child(1)')
            score_away_el = detail_soup.select_one('.detailScore__wrapper span:nth-child(3)')
            
            if score_home_el and score_away_el:
                h_str = re.sub(r'\D', '', score_home_el.text)
                a_str = re.sub(r'\D', '', score_away_el.text)
                if h_str and a_str:
                    h_score = int(h_str)
                    a_score = int(a_str)
            
            status_el = detail_soup.select_one('.fixedHeader__status, .detailScore__status')
            if status_el:
                status_txt = status_el.text.strip()
                print(f"Match status text: {status_txt}")
                if any(kw in status_txt for kw in ["Kết thúc", "FT", "Finished", "Đã xong"]):
                    status = "FIN"
                    
            print(f"✅ AUDIT RESULT: {home_team} {h_score} - {a_score} {away_team} | Status: {status}")
        else:
            print("❌ No matching match link found in search results!")
            
    except Exception as e:
        print(f"Error in test: {e}")
    finally:
        browser.stop()

if __name__ == "__main__":
    test_flow("Ả Rập Saudi", "Senegal")
