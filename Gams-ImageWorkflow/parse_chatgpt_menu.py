from bs4 import BeautifulSoup
import sys

sys.stdout.reconfigure(encoding='utf-8')
soup = BeautifulSoup(open('chatgpt_menu_dom.html', encoding='utf-8'), 'html.parser')

print("=== MENU ITEMS ===")
for i in soup.find_all(attrs={"role": "menuitem"}):
    print("MenuItem:", i.text.strip(), i.get('class'))

print("\n=== INPUT FILE INSIDE MENU ===")
for i in soup.find_all('input', type='file'):
    print(i.get('accept'), i.get('class'))
    parent = i.parent
    print(" -> Parent:", parent.name, parent.get('class'))
