import sys
from html.parser import HTMLParser

class Validator(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []
        self.void_elements = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def handle_starttag(self, tag, attrs):
        if tag not in self.void_elements:
            self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag in self.void_elements:
            return
        
        if not self.stack:
            self.errors.append(f"Line {self.getpos()[0]}: Unexpected end tag </{tag}>, nothing open.")
            return

        last_tag, pos = self.stack[-1]
        if last_tag == tag:
            self.stack.pop()
        else:
            self.errors.append(f"Line {self.getpos()[0]}: Mismatched end tag </{tag}>. Expected </{last_tag}> which was opened at line {pos[0]}.")
            # Try to recover by popping the matched tag if it's further up the stack
            for i in range(len(self.stack)-1, -1, -1):
                if self.stack[i][0] == tag:
                    self.stack = self.stack[:i]
                    break
            else:
                pass # Unmatched closing tag, ignore

    def check(self, html):
        self.feed(html)
        for tag, pos in self.stack:
            self.errors.append(f"Line {pos[0]}: Unclosed tag <{tag}>.")
        return self.errors

def main():
    try:
        with open('e:/Gams Ai Jarvis Os/ui/advanced_dashboard.html', 'r', encoding='utf-8') as f:
            html = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    v = Validator()
    errors = v.check(html)
    if errors:
        print(f"Found {len(errors)} HTML structure errors:")
        for e in errors[:50]:
            print(e)
    else:
        print("No HTML structure errors found.")

if __name__ == '__main__':
    main()
