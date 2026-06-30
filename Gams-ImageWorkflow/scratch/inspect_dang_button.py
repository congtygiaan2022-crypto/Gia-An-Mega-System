from bs4 import BeautifulSoup
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('fb_upload_dom_after_click2.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Tim noi [13] - nut Dang
buttons = soup.find_all(attrs={'role': 'button'})
btn = buttons[13]
print("=== NUT DANG [index 13] ===")
print(f"Tag: {btn.name}")
print(f"Text: {repr(btn.get_text())}")

# In tat ca attributes
print("Attributes:")
for k, v in btn.attrs.items():
    print(f"  {k}: {v}")

# In HTML day du
print("\nHTML day du:")
print(str(btn)[:3000])

# Tim parent
print("\nParent chain:")
p = btn.parent
for i in range(5):
    if p:
        attrs_str = {k: v for k, v in p.attrs.items() if k in ['role', 'aria-label', 'aria-disabled', 'data-testid', 'class']}
        cls_short = str(attrs_str.get('class', []))[:50]
        attrs_str['class'] = cls_short
        print(f"  [{i}] tag={p.name} attrs={attrs_str}")
        p = p.parent
