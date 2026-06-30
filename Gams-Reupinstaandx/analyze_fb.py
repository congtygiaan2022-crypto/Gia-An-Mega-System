import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

try:
    with open('explore_facebook.json', encoding='utf-8') as f:
        data = json.load(f)
        for i, e in enumerate(data):
            if e['tag'] in ('INPUT', 'TEXTAREA') or e.get('contentEditable') == 'true' or e['tag'] == 'BUTTON':
                text = e.get('text', '').replace('\n', ' ')
                print(f"[{i}] {e['tag']} type='{e.get('type')}' aria='{e.get('ariaLabel')}' text='{text}' class='{e.get('className')}'")
except Exception as ex:
    print(ex)
