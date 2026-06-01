import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath('')))
from modules.fb_login import build_driver, login
from modules.copyright_checker import switch_context_via_menu

driver = build_driver()
login(driver)
switch_context_via_menu(driver, 'Tin Này Trending')
# Go to a specific support item
driver.get('https://www.facebook.com/support/?item_id=122247808022265943')
time.sleep(10)

js = """
let buttons = Array.from(document.querySelectorAll("div[role='button'], button, a"));
return buttons.map(b => b.outerHTML).filter(h => h.toLowerCase().includes("see options") || h.toLowerCase().includes("continue") || h.toLowerCase().includes("xem các tùy chọn") || h.toLowerCase().includes("tiếp tục") || h.toLowerCase().includes("remove") || h.toLowerCase().includes("gỡ") || h.toLowerCase().includes("xóa") || h.toLowerCase().includes("delete"));
"""
btns = driver.execute_script(js)
print("INTERACTIVE ELEMENTS:", len(btns))
for b in btns:
    print(b[:300])

html = driver.page_source
with open('support_item_debug.html', 'w', encoding='utf-8') as f:
    f.write(html)
driver.quit()
