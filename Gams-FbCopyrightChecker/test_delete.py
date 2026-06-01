import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath('')))
from modules.fb_login import build_driver, login
from modules.copyright_checker import switch_context_via_menu, delete_appeal_post
from modules.database import Database

db = Database()
driver = build_driver()
login(driver)
switch_context_via_menu(driver, 'Tin Này Trending')

appeal = {
    "post_url": "https://www.facebook.com/support/?item_id=122247808022265943",
    "title": "Test Delete Appeal"
}

def _log(msg):
    print(msg)
    with open("delete_log.txt", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

_log("Bắt đầu thử xóa bài viết...")
success = delete_appeal_post(driver, appeal, db)
_log(f"Kết quả xóa: {success}")

time.sleep(3)
driver.quit()
