import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.browser import BrowserController

def main():
    print("Starting DOM inspection...")
    browser = BrowserController(headless=True)
    if not browser.start():
        return

    try:
        url = "https://bcvn2.com/vi/sports/soccer-1"
        browser.navigate(url)
        time.sleep(15)
        
        # JS to inspect DOM for Crystal Palace or Rayo Vallecano
        js_code = """
        function findPaths(root, targetText, path) {
            path = path || 'document';
            let results = [];
            let all = root.querySelectorAll('*');
            for (let i = 0; i < all.length; i++) {
                let el = all[i];
                let text = el.innerText || '';
                if (text.includes(targetText)) {
                    // Check if it's the leaf or near leaf containing the text
                    let childrenContaining = 0;
                    for (let j = 0; j < el.children.length; j++) {
                        if ((el.children[j].innerText || '').includes(targetText)) {
                            childrenContaining++;
                        }
                    }
                    if (childrenContaining === 0) {
                        // Leaf element
                        let elPath = el.tagName.toLowerCase();
                        if (el.className) elPath += '.' + Array.from(el.classList).join('.');
                        results.push({
                            tag: el.tagName,
                            classes: el.className,
                            text: text.trim(),
                            parentTag: el.parentElement ? el.parentElement.tagName : null,
                            parentClasses: el.parentElement ? el.parentElement.className : null,
                            grandparentTag: el.parentElement && el.parentElement.parentElement ? el.parentElement.parentElement.tagName : null,
                            grandparentClasses: el.parentElement && el.parentElement.parentElement ? el.parentElement.parentElement.className : null
                        });
                    }
                }
                if (el.shadowRoot) {
                    results = results.concat(findPaths(el.shadowRoot, targetText, path + ' -> shadowRoot'));
                }
            }
            return results;
        }
        return findPaths(document, 'Crystal Palace');
        """
        results = browser.driver.execute_script(js_code)
        print(f"Found {len(results)} elements matching target 'Crystal Palace':")
        for idx, res in enumerate(results[:15]):
            print(f"Element {idx + 1}:")
            print(f"  Tag: {res['tag']}, Classes: {res['classes']}")
            print(f"  Text: {res['text'][:100]}")
            print(f"  Parent: {res['parentTag']}, Classes: {res['parentClasses']}")
            print(f"  Grandparent: {res['grandparentTag']}, Classes: {res['grandparentClasses']}")
            
        # Let's also search for any matches or rows and see what their class name is
        js_rows = """
        function findRows(root) {
            let results = [];
            let all = root.querySelectorAll('*');
            for(let i=0; i<all.length; i++) {
                let el = all[i];
                let cl = el.className || '';
                if (typeof cl === 'string' && (cl.includes('match') || cl.includes('Match') || cl.includes('game') || cl.includes('Game'))) {
                    results.push({tag: el.tagName, classes: cl, text: (el.innerText || '').substring(0, 100)});
                }
                if (el.shadowRoot) {
                    results = results.concat(findRows(el.shadowRoot));
                }
            }
            return results;
        }
        return findRows(document);
        """
        rows = browser.driver.execute_script(js_rows)
        print(f"\nFound {len(rows)} elements containing 'match' or 'game' in class:")
        for idx, r in enumerate(rows[:20]):
            print(f"Row {idx+1}: Tag: {r['tag']}, Class: {r['classes']} | Text: {r['text'].strip()}")

    finally:
        browser.stop()

if __name__ == "__main__":
    main()
