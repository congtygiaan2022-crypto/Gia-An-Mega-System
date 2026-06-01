"""
Computer Use Engine — Playwright-based browser automation.
Provides a simple sync interface for LLM-driven browser control.
"""

import os
import time
from playwright.sync_api import sync_playwright
from core.logger import get_module_logger

logger = get_module_logger("ComputerEngine")


class ComputerUseEngine:
    """
    Full browser automation engine.
    Actions: open_url, click, type, scroll, screenshot, extract_text, close
    """

    def __init__(self):
        self._playwright = None
        self.browser = None
        self.page = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start_browser(self, headless: bool = False):
        """Launch Chromium. headless=False for visual debugging."""
        if self._playwright:
            return "Browser already running"
        self._playwright = sync_playwright().start()
        self.browser = self._playwright.chromium.launch(headless=headless)
        self.page = self.browser.new_page()
        logger.info("[ComputerEngine] Browser started.")
        return "Browser started"

    def stop(self):
        if self.browser:
            self.browser.close()
        if self._playwright:
            self._playwright.stop()
        self.page = None
        self.browser = None
        self._playwright = None
        logger.info("[ComputerEngine] Browser stopped.")
        return "Browser stopped"

    def _ensure_started(self):
        if not self.page:
            self.start_browser()

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def open_url(self, url: str) -> str:
        self._ensure_started()
        if not url.startswith("http"):
            url = f"https://{url}"
        self.page.goto(url, wait_until="domcontentloaded")
        logger.info(f"[ComputerEngine] Opened: {url}")
        return f"Opened {url}"

    def search_google(self, query: str) -> str:
        return self.open_url(f"https://www.google.com/search?q={query}")

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    def click(self, selector: str) -> str:
        self._ensure_started()
        self.page.click(selector)
        return f"Clicked selector: {selector}"

    def click_by_text(self, text: str) -> str:
        """Click the first element whose visible text contains `text`."""
        self._ensure_started()
        elements = self.page.query_selector_all("a,button,span,div,li")
        for el in elements:
            try:
                label = el.inner_text().strip()
                if text.lower() in label.lower():
                    el.click()
                    logger.info(f"[ComputerEngine] Clicked element with text: '{text}'")
                    return f"Clicked '{text}'"
            except Exception:
                continue
        return f"Element with text '{text}' not found"

    def type(self, selector: str, text: str) -> str:
        self._ensure_started()
        self.page.fill(selector, text)
        return f"Typed into {selector}"

    def press_key(self, key: str) -> str:
        self._ensure_started()
        self.page.keyboard.press(key)
        return f"Pressed {key}"

    def scroll(self, direction: str = "down", amount: int = 1000) -> str:
        self._ensure_started()
        delta = amount if direction == "down" else -amount
        self.page.mouse.wheel(0, delta)
        return f"Scrolled {direction} by {amount}px"

    # ------------------------------------------------------------------
    # Reading content
    # ------------------------------------------------------------------

    def extract_text(self) -> str:
        """Extract all visible text from current page."""
        self._ensure_started()
        try:
            text = self.page.inner_text("body")
            logger.info(f"[ComputerEngine] Extracted {len(text)} chars from page.")
            return text
        except Exception as e:
            logger.error(f"[ComputerEngine] extract_text failed: {e}")
            return ""

    def get_page_title(self) -> str:
        self._ensure_started()
        return self.page.title()

    def get_url(self) -> str:
        self._ensure_started()
        return self.page.url

    # ------------------------------------------------------------------
    # Screenshot
    # ------------------------------------------------------------------

    def screenshot(self, name: str = "screen") -> str:
        self._ensure_started()
        os.makedirs("data/screenshots", exist_ok=True)
        path = f"data/screenshots/{name}_{int(time.time())}.png"
        self.page.screenshot(path=path)
        logger.info(f"[ComputerEngine] Screenshot saved: {path}")
        return path


# Global singleton
computer_engine = ComputerUseEngine()
