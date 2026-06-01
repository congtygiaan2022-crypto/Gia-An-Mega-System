import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath('')))
from modules.fb_login import build_driver, login
from modules.copyright_checker import switch_context_via_menu

driver = build_driver()
login(driver)
switch_context_via_menu(driver, 'Tin Này Trending')

url = "https://www.facebook.com/support/?item_id=122245942472265943"
print(f"Navigating to: {url}")
driver.get(url)
time.sleep(5)

html = driver.page_source
with open("dump_appeal_page.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Dumped HTML to dump_appeal_page.html")

time.sleep(2)
driver.quit()
