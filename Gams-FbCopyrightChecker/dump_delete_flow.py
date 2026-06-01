import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath('')))
from modules.fb_login import build_driver, login
from modules.copyright_checker import switch_context_via_menu
from selenium.webdriver.common.by import By

driver = build_driver()
login(driver)

driver.get("https://www.facebook.com/support/")
time.sleep(5)
print("Finding support items...")
items = driver.find_elements(By.XPATH, "//a[contains(@href, '/support/?item_id=')]")
urls = [item.get_attribute("href") for item in items]

print(f"Found {len(urls)} support items.")
if not urls:
    switch_context_via_menu(driver, 'Tin Này Trending')
    driver.get("https://www.facebook.com/support/")
    time.sleep(5)
    items = driver.find_elements(By.XPATH, "//a[contains(@href, '/support/?item_id=')]")
    urls = [item.get_attribute("href") for item in items]
    print(f"Found {len(urls)} support items on Fanpage.")

for idx, url in enumerate(urls[:2]):
    print(f"\nNavigating to item {idx+1}: {url}")
    driver.get(url)
    time.sleep(4)
    with open(f"dom_step0_{idx}.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    
    # Try finding the "See options" button
    buttons = driver.find_elements(By.XPATH, "//div[@role='button'] | //button")
    clicked = False
    for b in buttons:
        try:
            text = driver.execute_script("return arguments[0].textContent;", b).lower().strip()
            if any(kw in text for kw in ["xem các tùy chọn", "xem lựa chọn", "see options", "xem chi tiết", "see details"]):
                print(f"Clicking: {text}")
                driver.execute_script("arguments[0].click();", b)
                clicked = True
                time.sleep(3)
                with open(f"dom_step1_{idx}.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                break
        except Exception: pass
    
    if clicked:
        # Try finding the next buttons
        for step in range(2, 6):
            buttons = driver.find_elements(By.XPATH, "//div[@role='button'] | //div[@role='radio'] | //button")
            step_clicked = False
            for b in buttons:
                try:
                    text = driver.execute_script("return arguments[0].textContent;", b).lower().strip()
                    if any(kw in text for kw in ["tiếp tục", "continue", "gỡ video", "remove video", "xóa video", "delete video", "xóa", "delete"]):
                        print(f"Clicking step {step}: {text}")
                        driver.execute_script("arguments[0].click();", b)
                        step_clicked = True
                        time.sleep(3)
                        with open(f"dom_step{step}_{idx}.html", "w", encoding="utf-8") as f:
                            f.write(driver.page_source)
                        break
                except Exception: pass
            if not step_clicked:
                break

driver.quit()
print("Done dumping.")
