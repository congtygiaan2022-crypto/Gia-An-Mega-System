import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')
soup = BeautifulSoup(open('chatgpt_img_dom.html', encoding='utf-8'), 'html.parser')

print("\n=== ASSISTANT MESSAGES ===")
for i in soup.find_all(attrs={"data-message-author-role": True}):
    print(i.get('data-message-author-role'), i.get('class'))
    for img in i.find_all('img'):
        print(" -> Image:", img.get('alt'), img.get('src')[:100] if img.get('src') else None)

print("\n=== BUTTONS ===")
for b in soup.find_all('button', attrs={"aria-label": True}):
    if "Download" in b.get('aria-label') or "download" in b.get('aria-label').lower():
        print("Download Button:", b.get('aria-label'), b.get('data-testid'), b.get('class'))

