"""
computer/browser_engine.py — Playwright sync browser automation.
Clean v2 interface: open, search_google, click, scroll, extract_text, screenshot.
"""
import os
import time
from playwright.sync_api import sync_playwright


class BrowserEngine:
    def __init__(self):
        self.play = None
        self.browser = None
        self.page = None

    def _ensure(self):
        if not self.play:
            self.play = sync_playwright().start()
            self.browser = self.play.chromium.launch(headless=False)
            self.page = self.browser.new_page()

    def open(self, url: str) -> str:
        self._ensure()
        if not url.startswith("http"):
            url = f"https://{url}"
        self.page.goto(url, wait_until="domcontentloaded")
        return f"Opened: {url}"

    def search_google(self, query: str) -> str:
        self._ensure()
        self.page.goto("https://google.com")
        self.page.fill("textarea[name='q']", query)
        self.page.keyboard.press("Enter")
        self.page.wait_for_load_state("domcontentloaded")
        return f"Searched: {query}"

    def click(self, selector: str) -> str:
        self._ensure()
        self.page.click(selector)
        return f"Clicked: {selector}"

    def click_by_text(self, text: str) -> str:
        self._ensure()
        for tag in ["a", "button", "span", "div", "li"]:
            for el in self.page.query_selector_all(tag):
                try:
                    if text.lower() in el.inner_text().lower():
                        el.click()
                        return f"Clicked '{text}'"
                except Exception:
                    continue
        return f"Not found: '{text}'"

    def fill(self, selector: str, text: str) -> str:
        self._ensure()
        self.page.fill(selector, text)
        return f"Filled '{selector}' with '{text}'"

    def scroll(self, amount: int = 1500) -> str:
        self._ensure()
        self.page.mouse.wheel(0, amount)
        return f"Scrolled {amount}px"

    def extract_text(self) -> str:
        self._ensure()
        return self.page.inner_text("body")

    def screenshot(self, name: str = "browser") -> str:
        self._ensure()
        os.makedirs("data/screenshots", exist_ok=True)
        path = f"data/screenshots/{name}_{int(time.time())}.png"
        self.page.screenshot(path=path)
        return path

    def close(self):
        if self.browser:
            self.browser.close()
        if self.play:
            self.play.stop()
        self.play = self.browser = self.page = None


# Global singleton
browser_engine = BrowserEngine()
