import time
import sys
import os
import re
from bs4 import BeautifulSoup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.browser import BrowserController

def test_google_scores():
    browser = BrowserController(headless=True)
    if not browser.start():
        print("Failed to start browser")
        return
        
    try:
        driver = browser.driver
        # Test queries for completed/recent matches
        queries = [
            "Man City vs Real Madrid score",
            "Arsenal vs Everton score",
            "Vietnam vs Thailand score" # Dummy query
        ]
        
        for q in queries:
            print(f"\nSearching Google for: '{q}'...")
            search_url = f"https://www.google.com/search?q={q.replace(' ', '+')}"
            driver.get(search_url)
            time.sleep(3)
            
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # 1. Print some matching text or elements to understand the DOM
            print("Checking elements starting with 'imso_mh__'...")
            ims_elements = soup.find_all(class_=re.compile(r'imso_mh__'))
            print(f"Found {len(ims_elements)} elements with class starting with 'imso_mh__'")
            for idx, el in enumerate(ims_elements[:10]):
                print(f"  {idx}: Class={el.get('class')}, Text='{el.text.strip()}'")
                
            # 2. Try the current parsing logic
            score_elements = soup.find_all('div', {'class': re.compile(r'imso_mh__.*-sc')})
            print(f"Found {len(score_elements)} score elements (current class pattern)")
            h_score, a_score = 0, 0
            if len(score_elements) >= 2:
                try:
                    h_score = int(score_elements[0].text.strip())
                    a_score = int(score_elements[1].text.strip())
                    print(f"⚽ Current parser result: {h_score} - {a_score}")
                except Exception as e:
                    print(f"Current parser parse error: {e}")
            else:
                # Test fallback parsing
                # Current fallback: r'(\d+)\s*-\s*(\d+)'
                match_score = re.search(r'(\d+)\s*-\s*(\d+)', soup.get_text())
                if match_score:
                    print(f"Fallback regex matched (current pattern): {match_score.group(1)} - {match_score.group(2)}")
                
                # New fallback: limit to 1-2 digits, and look for team/score context
                # Also, we can look for specific class names that contain the score
                match_score_new = re.search(r'\b(\d{1,2})\s*-\s*(\d{1,2})\b', soup.get_text())
                if match_score_new:
                    print(f"Fallback regex matched (new 1-2 digit pattern): {match_score_new.group(1)} - {match_score_new.group(2)}")
                    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        browser.stop()

if __name__ == "__main__":
    test_google_scores()
