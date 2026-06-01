from bs4 import BeautifulSoup
with open('dump_appeal_page.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

buttons = soup.find_all(lambda tag: tag.name in ['button', 'div', 'span'] and tag.has_attr('role') and tag['role'] in ['button', 'radio'])
print("Found buttons:")
for b in buttons:
    text = b.text.lower().strip()
    if any(x in text for x in ['xóa', 'gỡ', 'delete', 'remove', 'tiếp tục', 'continue']):
        print(f"Match: {text}")
