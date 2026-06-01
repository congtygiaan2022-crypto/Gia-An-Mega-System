from computer.browser_vision import browser_vision

class ComputerBrain:
    def __init__(self):
        self.browser = browser_vision

    def start(self):
        return self.browser.start()

    def open_site(self, url):
        return self.browser.open(url)

    def analyze_page(self):
        elements = self.browser.get_dom_elements()
        summary = []
        for el in elements:
            text = el.get("text", "").strip()
            if text:
                summary.append(f"{el.get('tag')}: {text}")
        
        # Return a summarized view of the page
        return summary[:30]

    def find_and_click(self, keyword):
        # Human-like logic: look for text match in DOM and click
        return self.browser.click_by_text(keyword)

    def type_text(self, text, keyword=""):
        # Human-like logic: find input field and type
        return self.browser.type_by_placeholder(text, keyword)

    def auto_scroll(self, direction="down"):
        # We'll use a direct JS call or engine-level scroll if exposed
        if not self.browser.page: return "Browser not started"
        if direction == "down":
            self.browser.page.evaluate("window.scrollBy(0, 800)")
        else:
            self.browser.page.evaluate("window.scrollBy(0, -800)")
        return f"Scrolled {direction}"

    def capture_screen(self):
        return self.browser.screenshot()

    def stop(self):
        return self.browser.stop()

# Global instance
computer_brain = ComputerBrain()
