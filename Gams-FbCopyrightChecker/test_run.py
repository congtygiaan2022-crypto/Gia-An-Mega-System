import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath('')))
from modules.fb_login import build_driver, login
from modules.copyright_checker import get_copyright_appeals, delete_appeal_post
from modules.database import Database

db = Database()
driver = build_driver()
login(driver)

print("Fetching appeals...")
appeals = get_copyright_appeals(driver, "Test Profile")
print(f"Found {len(appeals)} appeals:")
for a in appeals:
    print(a)

if appeals:
    a = None
    for appeal in appeals:
        if '122246993480265943' in appeal.get('post_url'):
            a = appeal
            break
    if a:
        print(f"Trying to delete: {a.get('post_url')}")
        success = delete_appeal_post(driver, a, db)
        print(f"Delete success? {success}")

driver.quit()
