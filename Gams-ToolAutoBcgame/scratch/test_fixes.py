import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.browser import BrowserController
from core.scraper_wap import WapScraper
from core.auditor import GoogleAuditor

def verify_fixes():
    print("Initializing browser...")
    browser = BrowserController(headless=True)
    if not browser.start():
        print("Failed to start browser")
        return
        
    try:
        # 1. Test WapScraper
        print("\n--- Testing WapScraper ---")
        scraper = WapScraper(browser=browser)
        matches = scraper.get_tai_matches()
        print(f"Found {len(matches)} matches")
        
        if matches:
            test_match = matches[0]
            print(f"Testing check_match_status for {test_match['home']} vs {test_match['away']} ({test_match['detail_url']})")
            is_upcoming = scraper.check_match_status(test_match['detail_url'], time_str=test_match.get('time_str'))
            print(f"Result: is_upcoming = {is_upcoming}")
            print("WapScraper check_match_status passed! No invalid session id.")
        else:
            print("No matches to test check_match_status.")
            
        # 2. Test GoogleAuditor (using native tab-switching)
        print("\n--- Testing GoogleAuditor ---")
        auditor = GoogleAuditor(browser=browser)
        # Choose a dummy match to search on Google
        home, away = "Vietnam", "Thailand"
        print(f"Auditing result on Google for {home} vs {away}...")
        status, h, a = auditor.check_result(home, away)
        print(f"Auditor result: status={status}, home_score={h}, away_score={a}")
        print("GoogleAuditor passed! No invalid session id.")
        
        print("\nAll tests completed successfully!")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        browser.stop()

if __name__ == "__main__":
    verify_fixes()
