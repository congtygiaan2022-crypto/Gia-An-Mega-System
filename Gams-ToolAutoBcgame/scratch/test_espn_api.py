import requests
import json

def test_espn():
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            events = data.get("events", [])
            print(f"Found {len(events)} events today.")
            for ev in events[:5]:
                name = ev.get("name")
                status = ev.get("status", {}).get("type", {}).get("state")
                detail = ev.get("status", {}).get("type", {}).get("detail")
                
                competitors = ev.get("competitions", [{}])[0].get("competitors", [])
                scores = []
                for comp in competitors:
                    team_name = comp.get("team", {}).get("displayName")
                    score = comp.get("score")
                    scores.append(f"{team_name}: {score}")
                
                print(f"Match: {name} | Status: {status} ({detail}) | Scores: {', '.join(scores)}")
        else:
            print("Failed to get data.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_espn()
