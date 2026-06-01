import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath('')))
from modules.fb_login import build_driver, login
from modules.copyright_checker import switch_context_via_menu

driver = build_driver()
login(driver)
switch_context_via_menu(driver, 'Tin Này Trending')
driver.get('https://www.facebook.com/support/?tab_type=APPEALS')
time.sleep(10)
html = driver.page_source
with open('appeals_debug.html', 'w', encoding='utf-8') as f:
    f.write(html)

js = """
let items = Array.from(document.querySelectorAll("*")).filter(e => e.textContent.includes("điểm cập nhật mới về bản quyền") && e.children.length === 0);
let result = [];
for (let e of items) {
    let parent = e.parentElement;
    while(parent && parent.tagName !== "A" && parent.getAttribute("role") !== "article" && parent.getAttribute("role") !== "button" && parent.tagName !== "BODY") {
        parent = parent.parentElement;
    }
    if (parent) {
        result.push(parent.outerHTML);
    }
}
return result;
"""
elements = driver.execute_script(js)
print('FOUND:', len(elements))
for i, e in enumerate(elements):
    print(i, e[:500])

driver.quit()
