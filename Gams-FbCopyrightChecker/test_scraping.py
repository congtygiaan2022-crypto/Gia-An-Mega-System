import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.fb_login import build_driver, login
from modules.fb_profile import get_fanpages, get_profile_info

def main():
    driver = build_driver()
    try:
        if not login(driver):
            print("Login failed or no active session.")
            return

        print("=== GET PROFILE INFO ===")
        profile = get_profile_info(driver)
        print("Profile:", profile)

        print("\n=== GET FANPAGES ===")
        pages = get_fanpages(driver)
        print(f"Found {len(pages)} pages.")
        for p in pages:
            print(f"- {p['name']}: {p['url']}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
