import time
from core.browser import BrowserController
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

def run_test():
    browser = BrowserController()
    if not browser.start():
        print("Failed to start browser")
        return
        
    try:
        print("Navigating to Flashscore.vn...")
        browser.navigate("https://www.flashscore.vn/")
        time.sleep(5)
        
        # Save page source to check elements
        html = browser.get_page_source()
        with open("scratch/flashscore_home.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        print("Checking if cookie consent button exists...")
        # Cookie banner check
        cookie_btn = browser.driver.find_elements(By.ID, "onetrust-accept-btn-handler")
        if cookie_btn:
            print("Accepting cookies...")
            cookie_btn[0].click()
            time.sleep(2)
            
        print("Searching for search button/icon...")
        # Common search button/icon selectors on Flashscore:
        # e.g., #search-window, .header__search, etc.
        search_selectors = [
            "#search-window",
            ".header__search",
            ".header__searchIcon",
            ".header__search-icon",
            "[class*='searchIcon']",
            "[class*='search-icon']",
            "button[class*='search']",
            "div[class*='search']"
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
                
        if btn:
            print("Clicking search button...")
            browser.click_element(btn)
            time.sleep(3)
            
            # Now find search input
            input_selectors = [
                "input[placeholder*='Tìm kiếm']",
                "input[placeholder*='Search']",
                "input[class*='search']",
                ".search__input",
                "input.search"
            ]
            
            inp = None
            for sel in input_selectors:
                elements = browser.driver.find_elements(By.CSS_SELECTOR, sel)
                if elements:
                    for el in elements:
                        if el.is_displayed():
                            print(f"Found input field with selector: {sel}")
                            inp = el
                            break
                if inp:
                    break
                    
            if inp:
                print("Typing search query...")
                inp.send_keys("Saudi Arabia Senegal")
                time.sleep(2)
                inp.send_keys(Keys.ENTER)
                time.sleep(5)
                
                print("Checking search results...")
                results_html = browser.get_page_source()
                with open("scratch/flashscore_results.html", "w", encoding="utf-8") as f:
                    f.write(results_html)
                print("Saved results html.")
            else:
                print("Search input field not found after click!")
        else:
            print("Search button not found on home page!")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        browser.stop()

if __name__ == "__main__":
    run_test()
