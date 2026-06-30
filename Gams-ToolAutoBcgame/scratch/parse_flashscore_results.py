from bs4 import BeautifulSoup
import re
import sys

# Configure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

def parse():
    with open("scratch/flashscore_results.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, "html.parser")
    
    # Let's search for potential result elements
    # e.g., elements with class containing 'search', 'result', 'match', or team names.
    print("Page Title:", soup.title.text if soup.title else "No Title")
    
    print("\n--- Listing elements with class containing 'search' ---")
    search_elements = soup.find_all(class_=re.compile(r'search', re.I))
    print(f"Found {len(search_elements)} elements with 'search' in class name.")
    for idx, el in enumerate(search_elements[:30]):
        # Print class and snippet of text/attrs
        classes = el.get("class", [])
        text = el.text.strip().replace('\n', ' ')[:100]
        print(f"{idx}: Class={classes} | Tag={el.name} | Text={text}")
        
    print("\n--- Listing elements with id containing 'g_1_' ---")
    g_elements = soup.find_all(id=re.compile(r'^g_1_'))
    print(f"Found {len(g_elements)} elements with id starting with 'g_1_'.")
    for idx, el in enumerate(g_elements[:10]):
        text = el.text.strip().replace('\n', ' ')[:100]
        print(f"{idx}: ID={el.get('id')} | Text={text}")

    print("\n--- Searching for 'Saudi' or 'Arab' or 'Senegal' in text ---")
    for word in ['Saudi', 'Arab', 'Senegal', 'Saudi Arabia', 'Senegal', 'Ả Rập', 'Saudi', 'Senegal']:
        matches = soup.find_all(text=re.compile(re.escape(word), re.I))
        print(f"Found {len(matches)} occurrences of word '{word}'")
        for idx, m in enumerate(matches[:10]):
            parent = m.parent
            print(f"  {idx}: ParentTag={parent.name} | ParentClass={parent.get('class')} | ParentAttrs={parent.attrs} | Text={m.strip()}")
            if parent.name == 'a':
                print(f"    Parent Outer HTML: {str(parent)[:200]}...")
            elif parent.parent.name == 'a':
                print(f"    Grandparent Outer HTML: {str(parent.parent)[:200]}...")

if __name__ == "__main__":
    parse()
