import time
import hashlib

from selenium import webdriver
from selenium.webdriver.common.by import By

from modules.config_loader import CONFIG
from modules.database import Database
from modules.logger import get_logger

log = get_logger(__name__)


def _make_post_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:16]


def scan_profile_posts(driver: webdriver.Chrome, db: Database) -> dict:
    """
    Scan the configured profile page for posts containing copyright keywords.
    Returns {'total': int, 'flagged': int}.
    """
    profile_url = CONFIG.get("facebook", {}).get("profile_url", "")
    keywords = [kw.lower() for kw in CONFIG.get("checker", {}).get("keywords", [])]
    if not profile_url:
        log.error("scan_profile_posts: 'profile_url' chưa được cấu hình trong config.json")
        return {"total": 0, "flagged": 0}
    log.info(f"Scanning posts at: {profile_url}")

    driver.get(profile_url)
    time.sleep(4)

    # Scroll down to load more posts
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    posts = driver.find_elements(By.XPATH, "//div[@data-pagelet='ProfileTimeline']//div[@role='article']")
    if not posts:
        posts = driver.find_elements(By.XPATH, "//div[@role='article']")

    total = len(posts)
    flagged = 0
    log.info(f"Found {total} post elements")

    for post in posts:
        try:
            text = post.text.lower()
            # Try to get post URL from the timestamp link
            try:
                link = post.find_element(By.XPATH, ".//a[contains(@href,'/posts/') or contains(@href,'story_fbid')]")
                url = link.get_attribute("href") or profile_url
            except Exception:
                url = profile_url

            post_id = _make_post_id(url)
            db.upsert_post(post_id, url, post.text[:500])

            if any(kw in text for kw in keywords):
                db.flag_post(post_id)
                flagged += 1
                log.warning(f"Copyright keyword detected in post: {url}")
        except Exception as e:
            log.debug(f"Error processing post element: {e}")

    db.log_scan(total, flagged, 0)
    return {"total": total, "flagged": flagged}
