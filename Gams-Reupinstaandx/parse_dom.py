import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

try:
    with open("google_ai_dom.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Find the model response text
    import xml.etree.ElementTree as ET
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html, "html.parser")
    
    responses = soup.select('.model-response-text')
    print(f"Tìm thấy {len(responses)} thẻ .model-response-text")
    if responses:
        print("Text cuối cùng:")
        print(responses[-1].get_text(separator="\n", strip=True))
        
    imgs = soup.select('img')
    print(f"Tìm thấy {len(imgs)} thẻ img")
    for img in imgs[-5:]:
        print(img.get('src', ''), img.get('alt', ''), img.get('class', ''))

    menus = soup.select('button')
    print("Các nút bấm:")
    for b in menus:
        if 'Upload' in b.get_text() or 'Tải' in b.get_text():
            print(b.get_text(strip=True), b.get('aria-label', ''), b.get('class', ''))
except Exception as e:
    print(e)
