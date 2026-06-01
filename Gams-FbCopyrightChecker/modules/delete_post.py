import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from modules.database import Database
from modules.logger import get_logger

log = get_logger(__name__)


def delete_post(driver: webdriver.Chrome, post_url: str, post_id: str, db: Database, reason: str = "copyright") -> bool:
    """
    Navigate to a post and delete it via the 3-dot menu.
    Returns True if deletion succeeded.
    """
    if not post_url:
        log.warning(f"delete_post: post_url rỗng, bỏ qua (post_id={post_id})")
        return False
    try:
        driver.get(post_url)
        wait = WebDriverWait(driver, 15)
        time.sleep(1)

        # Click the 3-dot / options menu on the post
        menu_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@aria-label='Actions for this post' or @aria-label='More' or contains(@aria-label,'options')]")
        ))
        menu_btn.click()
        time.sleep(0.5)

        # Click "Move to Trash" or "Delete"
        delete_option = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(),'Move to trash') or contains(text(),'Delete') or contains(text(),'Xóa')]")
        ))
        delete_option.click()
        time.sleep(0.5)

        # Confirm deletion in the dialog
        confirm_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@aria-label='Move to Trash' or @aria-label='Delete' or @aria-label='Xóa']//div[@role='button']"
                       " | //button[contains(text(),'Move to Trash')] | //button[contains(text(),'OK')]")
        ))
        confirm_btn.click()
        time.sleep(0.5)

        db.record_deletion(post_id, post_url, reason)
        log.info(f"Post deleted: {post_url}")
        return True

    except Exception as e:
        log.error(f"Failed to delete post {post_url}: {e}")
        return False


def bulk_delete_flagged(driver: webdriver.Chrome, db: Database) -> int:
    """Delete all posts currently flagged in the database. Returns count deleted."""
    flagged = db.get_flagged_posts()
    deleted = 0
    for post_id, url in flagged:
        if delete_post(driver, url, post_id, db):
            deleted += 1
        time.sleep(0.5)
    log.info(f"Bulk delete complete: {deleted}/{len(flagged)} posts deleted")
    return deleted
