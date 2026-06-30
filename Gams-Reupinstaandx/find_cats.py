from bs4 import BeautifulSoup
import sys
sys.stdout.reconfigure(encoding='utf-8')
soup = BeautifulSoup(open('google_ai_dom.html', encoding='utf-8'), 'html.parser')
res = [t.get_text(separator='\n', strip=True) for t in soup.select('ms-chat-turn .chat-turn-container.model ms-text-chunk')]
with open("cats.txt", "w", encoding="utf-8") as f:
    f.write("\n\n---\n\n".join(res))
print(f"Found {len(res)} chunks")
