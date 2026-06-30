from bs4 import BeautifulSoup
import sys

sys.stdout.reconfigure(encoding='utf-8')

def parse():
    with open("scratch/flashscore_results.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, "html.parser")
    
    print("--- Elements containing /trandau/ ---")
    elements = soup.find_all(href=lambda href: href and "/trandau/" in href)
    print(f"Found {len(elements)} match elements.")
    for idx, el in enumerate(elements[:20]):
        print(f"{idx}: Tag={el.name} | Class={el.get('class')} | Attrs={el.attrs} | Text={el.text.strip()}")
        
    print("\n--- Elements with class 'searchResult' ---")
    sr_elements = soup.find_all(class_="searchResult")
    print(f"Found {len(sr_elements)} searchResult elements.")
    for idx, el in enumerate(sr_elements[:20]):
        cleaned_text = el.text.strip().replace('\n', ' ')
        print(f"{idx}: Tag={el.name} | Attrs={el.attrs} | Text={cleaned_text}")

if __name__ == "__main__":
    parse()
