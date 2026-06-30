from bs4 import BeautifulSoup
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

for fname in ['fb_upload_dom_after_click2.html', 'fb_upload_dom_after_click.html', 'fb_upload_dom.html']:
    try:
        with open(fname, 'r', encoding='utf-8') as f:
            html = f.read()
        soup = BeautifulSoup(html, 'html.parser')
        
        print(f'=== {fname} ===')
        
        # Tim tat ca role=button
        buttons = soup.find_all(attrs={'role': 'button'})
        print(f'Tong so role=button: {len(buttons)}')
        
        keywords = ['dang', 'post', 'publish', 'submit', 'share', 'done', 'save']
        for btn in buttons:
            text = btn.get_text(strip=True)
            aria = btn.get('aria-label', '')
            text_lower = text.lower()
            aria_lower = aria.lower()
            for kw in keywords:
                if (kw in text_lower or kw in aria_lower) and len(text) < 50:
                    testid = btn.get('data-testid', '')
                    tag = btn.name
                    # get class (shortened)
                    cls = str(btn.get('class', ''))[:60]
                    print(f'  TEXT=[{text}] aria=[{aria}] testid=[{testid}] tag={tag} class={cls}')
                    break
        
        # Tim theo aria-label co Publish/Post
        all_elems = soup.find_all(attrs={'aria-label': True})
        print(f'\nAll aria-label elements:')
        for el in all_elems:
            label = el.get('aria-label', '')
            tag = el.name
            role = el.get('role', '')
            print(f'  aria-label=[{label}] tag={tag} role={role}')
        
        # Tim button elements
        btns = soup.find_all('button')
        print(f'\nTat ca <button>:')
        for btn in btns:
            text = btn.get_text(strip=True)[:40]
            aria = btn.get('aria-label', '')
            typ = btn.get('type', '')
            testid = btn.get('data-testid', '')
            print(f'  TEXT=[{text}] aria=[{aria}] type={typ} testid=[{testid}]')
        
        print('\n')
        break
    except Exception as e:
        print(f'Loi doc {fname}: {e}')
