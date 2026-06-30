from bs4 import BeautifulSoup

def main():
    with open('chatgpt_modal_dom_old_chat.html', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        
    for btn in soup.find_all(['button', 'a']):
        text = btn.get_text().strip()
        aria = btn.get('aria-label', '')
        title = btn.get('title', '')
        cls = btn.get('class', [])
        print(f"Tag: {btn.name}, text: '{text}', aria: '{aria}', title: '{title}', class: {cls}")

    for div in soup.find_all('div', role='button'):
        text = div.get_text().strip()
        aria = div.get('aria-label', '')
        print(f"Tag: div[role=button], text: '{text}', aria: '{aria}'")

if __name__ == '__main__':
    main()
