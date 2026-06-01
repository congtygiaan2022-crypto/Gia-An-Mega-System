from playwright.sync_api import sync_playwright
import time
import os

class BrowserVision:
    def __init__(self):
        self.browser = None
        self.page = None
        self._playwright = None

    def start(self):
        if not self._playwright:
            self._playwright = sync_playwright().start()
            self.browser = self._playwright.chromium.launch(headless=False)
            self.page = self.browser.new_page()
        return "Browser started"

    def open(self, url):
        if not self.page:
            self.start()
        if not url.startswith("http"):
            url = f"https://{url}"
        self.page.goto(url)
        return f"Opened {url}"

    def get_dom_elements(self):
        if not self.page: return []
        elements = self.page.query_selector_all("a,button,input,textarea,text,span")
        data = []
        for el in elements:
            try:
                text = el.inner_text().strip()
                tag = el.evaluate("el => el.tagName")
                placeholder = el.get_attribute("placeholder") or ""
                # Only include visible elements with text or relevant tags
                if text or tag in ["INPUT", "TEXTAREA"] or placeholder:
                    data.append({
                        "tag": tag,
                        "text": text,
                        "placeholder": placeholder
                    })
            except:
                continue
        return data

    def click_by_text(self, text):
        if not self.page: return "Browser not started"
        elements = self.page.query_selector_all("a,button,span,div")
        for el in elements:
            try:
                label = el.inner_text().strip().lower()
                if text.lower() in label:
                    el.click()
                    return f"Clicked element containing '{text}'"
            except:
                continue
        return "Element not found"

    def type_by_placeholder(self, text, placeholder_text=""):
        if not self.page: return "Browser not started"
        inputs = self.page.query_selector_all("input,textarea")
        
        if placeholder_text:
            for i in inputs:
                try:
                    p = i.get_attribute("placeholder") or ""
                    n = i.get_attribute("name") or ""
                    a = i.get_attribute("aria-label") or ""
                    if (placeholder_text.lower() in p.lower()) or (placeholder_text.lower() in n.lower()) or (placeholder_text.lower() in a.lower()):
                        i.fill(text)
                        return f"Typed '{text}' into field matching '{placeholder_text}'"
                except:
                    continue
        
        # Fallback: if no placeholder text provided or no match, try the first visible input
        for i in inputs:
            try:
                if i.is_visible():
                    i.fill(text)
                    return f"Typed '{text}' into the first visible input field"
            except:
                continue

        return f"Input field '{placeholder_text}' not found"

    def screenshot(self):
        if not self.page: return "Browser not started"
        os.makedirs("data/screenshots", exist_ok=True)
        path = f"data/screenshots/vision_{int(time.time())}.png"
        self.page.screenshot(path=path)
        return f"Screenshot saved: {path}"

    def stop(self):
        if self.browser:
            self.browser.close()
        if self._playwright:
            self._playwright.stop()
        self.page = None
        self.browser = None
        self._playwright = None
        return "Browser stopped"

# Global instance
browser_vision = BrowserVision()
