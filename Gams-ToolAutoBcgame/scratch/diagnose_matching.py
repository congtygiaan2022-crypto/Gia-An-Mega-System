import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.browser import BrowserController
from core.scraper_wap import WapScraper
from core.scraper import BCGameScraper
from core.selector import MatchSelector

def main():
    print("Starting diagnostics...")
    browser = BrowserController(headless=True)
    if not browser.start():
        print("Failed to start browser")
        return

    try:
        scraper_wap = WapScraper(browser)
        scraper_bc = BCGameScraper(browser)
        selector = MatchSelector()

        print("\n--- STEP 1: SCRAPING WAP.VN ---")
        wap_matches = scraper_wap.get_tai_matches()
        print(f"Found {len(wap_matches)} matches on Wap.vn:")
        for m in wap_matches:
            print(f"  - {m['time_str']} | {m['home']} vs {m['away']}")

        print("\n--- STEP 2: SCRAPING BCGAME SOCCER MATCHES ---")
        if not scraper_bc.navigate_to_sports():
            print("Failed to navigate to BCGame sports")
            return

        bc_matches = scraper_bc.get_matches()
        print(f"Found {len(bc_matches)} matches on BCGame:")
        for m in bc_matches[:20]:
            print(f"  - {m.home_team} vs {m.away_team} (Status: {m.status})")

        print("\n--- STEP 3: TESTING MATCHING LOGIC ---")
        matched_count = 0
        for wm in wap_matches:
            print(f"\nChecking Wap Match: {wm['home']} vs {wm['away']}")
            
            # Print search queries that would be generated
            from core.selector import normalize_name
            norm_home = normalize_name(wm['home'])
            norm_away = normalize_name(wm['away'])
            queries = [wm['home'], norm_home, wm['away'], norm_away, f"{wm['home']} vs {wm['away']}"]
            print(f"  Search queries: {list(set(queries))}")
            
            # Find in all scraped BCGame matches
            found = False
            for bcm in bc_matches:
                if selector.is_match_similar(wm['home'], wm['away'], bcm.home_team, bcm.away_team):
                    print(f"  🎯 MATCHED: {bcm.home_team} vs {bcm.away_team}")
                    found = True
                    matched_count += 1
                    break
            
            if not found:
                print("  ❌ NO MATCH FOUND in currently scraped BCGame list.")
                # Show top 3 closest matches by score
                candidates = []
                for bcm in bc_matches:
                    s_home = selector.is_match_similar(wm['home'], wm['away'], bcm.home_team, bcm.away_team)
                    # Let's calculate the raw score
                    n_wh = normalize_name(wm['home'])
                    n_wa = normalize_name(wm['away'])
                    n_bh = normalize_name(bcm.home_team)
                    n_ba = normalize_name(bcm.away_team)
                    from thefuzz import fuzz
                    score_h = fuzz.token_sort_ratio(n_wh, n_bh)
                    score_a = fuzz.token_sort_ratio(n_wa, n_ba)
                    avg = (score_h + score_a) / 2
                    candidates.append((avg, bcm.home_team, bcm.away_team, score_h, score_a))
                
                candidates.sort(reverse=True)
                print("  Top candidates:")
                for score, h, a, sh, sa in candidates[:3]:
                    print(f"    - {h} vs {a} (Avg score: {score:.1f}%, Home: {sh}%, Away: {sa}%)")

        print(f"\nMatched {matched_count}/{len(wap_matches)} matches")

    finally:
        browser.stop()

if __name__ == "__main__":
    main()
