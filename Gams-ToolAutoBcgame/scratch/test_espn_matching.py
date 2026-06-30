import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.selector import normalize_name
from core.auditor import GoogleAuditor
import requests
from thefuzz import fuzz
from datetime import datetime, timedelta

def test_espn_matching():
    # Test cases: (Vietnamese home, Vietnamese away) -> expected match in ESPN today/yesterday
    test_cases = [
        ("Thái Lan", "Trung Quốc"), # Thailand vs China
        ("Campuchia", "Hồng Kông"), # Cambodia vs Hong Kong
        ("Ma-rốc", "Thụy Điển"),    # Morocco vs Sweden
        ("Ả Rập Saudi", "Senegal")  # Saudi Arabia vs Senegal
    ]
    
    now = datetime.now()
    dates = [
        now.strftime("%Y%m%d"),
        (now - timedelta(days=1)).strftime("%Y%m%d"),
        (now + timedelta(days=1)).strftime("%Y%m%d")
    ]
    
    print("Fetching ESPN scoreboard data...")
    all_events = []
    for d in dates:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={d}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                events = r.json().get("events", [])
                all_events.extend(events)
                print(f"  Loaded {len(events)} events for date {d}")
        except Exception as e:
            print(f"  Error loading date {d}: {e}")
            
    print(f"\nTotal events loaded: {len(all_events)}")
    
    for vt_home, vt_away in test_cases:
        print(f"\nSearching match: '{vt_home} vs {vt_away}'")
        norm_vh = normalize_name(vt_home)
        norm_va = normalize_name(vt_away)
        print(f"  Normalized search terms: '{norm_vh}' vs '{norm_va}'")
        
        found = False
        for ev in all_events:
            competitions = ev.get("competitions", [{}])
            if not competitions: continue
            competitors = competitions[0].get("competitors", [])
            if len(competitors) < 2: continue
            
            c_home = competitors[0] if competitors[0].get("homeAway") == "home" else competitors[1]
            c_away = competitors[1] if competitors[0].get("homeAway") == "home" else competitors[0]
            
            espn_home = c_home.get("team", {}).get("displayName", "")
            espn_away = c_away.get("team", {}).get("displayName", "")
            
            norm_eh = normalize_name(espn_home)
            norm_ea = normalize_name(espn_away)
            
            # Direct match
            match_direct = (
                (fuzz.token_sort_ratio(norm_vh, norm_eh) >= 70 or norm_vh in norm_eh or norm_eh in norm_vh) and
                (fuzz.token_sort_ratio(norm_va, norm_ea) >= 70 or norm_va in norm_ea or norm_ea in norm_va)
            )
            # Reverse match
            match_reverse = (
                (fuzz.token_sort_ratio(norm_vh, norm_ea) >= 70 or norm_vh in norm_ea or norm_ea in norm_vh) and
                (fuzz.token_sort_ratio(norm_va, norm_eh) >= 70 or norm_va in norm_eh or norm_eh in norm_va)
            )
            
            if match_direct or match_reverse:
                score_home = c_home.get("score")
                score_away = c_away.get("score")
                state = ev.get("status", {}).get("type", {}).get("state")
                print(f"  🎯 FOUND MATCH: '{espn_home}' vs '{espn_away}' | Score: {score_home}-{score_away} | Status: {state}")
                found = True
                break
        if not found:
            print(f"  ❌ Not found in ESPN data.")

if __name__ == "__main__":
    test_espn_matching()
