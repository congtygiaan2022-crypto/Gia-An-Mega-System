from core.scraper_wap import WapScraper
from core.browser import BrowserController

def test_scrape():
    browser = BrowserController()
    browser.start()
    scraper = WapScraper(browser)
    matches = scraper.get_tai_matches()
    print(f"Found {len(matches)} matches")
    for m in matches:
        print(f"{m['time_str']} | {m['home']} vs {m['away']}")
    browser.stop()

if __name__ == "__main__":
    test_scrape()
