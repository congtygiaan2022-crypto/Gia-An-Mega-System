from bs4 import BeautifulSoup
import sys

sys.stdout.reconfigure(encoding='utf-8')
soup = BeautifulSoup(open('google_ai_dom.html', encoding='utf-8'), 'html.parser')

def find_path(element):
    path = []
    for parent in element.parents:
        if parent.name == '[document]': break
        classes = parent.get('class', [])
        cls_str = '.' + '.'.join(classes) if classes else ''
        path.append(f"{parent.name}{cls_str}")
    return " > ".join(reversed(path))

import re
for tag in soup.find_all(string=re.compile("mèo", re.IGNORECASE)):
    elem = tag.parent
    print("TEXT:", tag.strip())
    print("PATH:", find_path(elem))
    print("TAG INFO:", elem.name, elem.get('class'))
    print("---")
