"""
computer/computer_use.py — Unified ComputerUse controller
Combines BrowserEngine + VisionEngine into one interface for the agent.
"""
from computer.browser_engine import browser_engine, BrowserEngine
from computer.vision_engine import vision_engine, VisionEngine


class ComputerUse:
    """
    High-level computer control combining browser and vision.
    The agent calls this module to interact with any UI element.

    Priority:
      1. Browser DOM (fast, precise)
      2. Vision OCR (fallback for native apps / non-web UI)
    """

    def __init__(self):
        self.browser: BrowserEngine = browser_engine
        self.vision: VisionEngine = vision_engine

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def open(self, url: str) -> str:
        return self.browser.open(url)

    def search(self, query: str) -> str:
        return self.browser.search_google(query)

    # ------------------------------------------------------------------
    # Interaction — tries DOM first, falls back to vision
    # ------------------------------------------------------------------

    def click(self, target: str) -> str:
        """Click by CSS selector, text label, or screen OCR."""
        # Try CSS selector first
        if target.startswith(("#", ".", "[", "a", "button", "input")):
            try:
                return self.browser.click(target)
            except Exception:
                pass

        # Try DOM text search
        result = self.browser.click_by_text(target)
        if "Not found" not in result:
            return result

        # Final fallback: vision OCR click
        if self.vision.is_available():
            return self.vision.click_text(target)

        return f"Cannot click '{target}': not found in DOM or screen"

    def type(self, text: str, selector: str = None) -> str:
        if selector:
            return self.browser.fill(selector, text)
        return self.vision.type_text(text)

    def scroll(self, amount: int = 1500) -> str:
        return self.browser.scroll(amount)

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    def extract_text(self) -> str:
        """Extract page text via DOM, fall back to OCR screenshot."""
        dom_text = self.browser.extract_text()
        if dom_text:
            return dom_text
        if self.vision.is_available():
            return self.vision.read_screen()
        return ""

    def screenshot(self, name: str = "screen") -> str:
        return self.browser.screenshot(name)

    def read_screen(self) -> str:
        return self.vision.read_screen()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self):
        self.browser.close()


# Global singleton
computer_use = ComputerUse()
