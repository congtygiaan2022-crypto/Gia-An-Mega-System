from bs4 import BeautifulSoup
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Phan tich tat ca role=button de tim nut Dang
with open('fb_upload_dom_after_click2.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

print("=== TAT CA role=button ===")
buttons = soup.find_all(attrs={'role': 'button'})
for i, btn in enumerate(buttons):
    text = btn.get_text(strip=True)[:80]
    aria = btn.get('aria-label', '')
    testid = btn.get('data-testid', '')
    tag = btn.name
    cls = str(btn.get('class', ''))[:80]
    print(f"[{i}] tag={tag} text=[{text}] aria=[{aria}] testid=[{testid}]")
    print(f"     class={cls}")

print("\n=== TAT CA <div> co text ngan lien quan ===")
divs = soup.find_all('div')
seen = set()
for div in divs:
    # Chi lay div co text truc tiep (khong qua nested)
    direct_text = ''.join(c for c in div.strings if c.strip())[:40]
    if direct_text and direct_text not in seen and len(direct_text) < 30:
        # Uu tien nhung gi co ve la button
        role = div.get('role', '')
        aria = div.get('aria-label', '')
        testid = div.get('data-testid', '')
        if role or aria or testid:
            seen.add(direct_text)
            print(f"  div role=[{role}] aria=[{aria}] testid=[{testid}] text=[{direct_text}]")
