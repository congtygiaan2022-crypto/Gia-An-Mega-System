import asyncio
from playwright.async_api import async_playwright
import os
import time

class BrowserController:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

    async def start(self):
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=False)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            print("Browser: Started successfully.")

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.browser = None
        self.playwright = None
        print("Browser: Stopped.")

    async def open_url(self, url: str):
        await self.start()
        await self.page.goto(url)
        print(f"Browser: Navigated to {url}")
        return f"Opened {url}"

    async def search(self, query: str):
        await self.start()
        # Simple heuristic: if on google, use search box
        if "google.com" in self.page.url:
            await self.page.fill('textarea[name="q"]', query)
            await self.page.press('textarea[name="q"]', "Enter")
        else:
            await self.page.goto(f"https://www.google.com/search?q={query}")
        print(f"Browser: Searched for '{query}'")
        return f"Searched for {query}"

    async def click(self, selector: str):
        await self.start()
        await self.page.click(selector)
        return f"Clicked {selector}"

    async def type(self, selector: str, text: str):
        await self.start()
        await self.page.fill(selector, text)
        return f"Typed '{text}' into {selector}"

    async def scroll(self, direction: str = "down"):
        await self.start()
        if direction == "down":
            await self.page.evaluate("window.scrollBy(0, 500)")
        else:
            await self.page.evaluate("window.scrollBy(0, -500)")
        return f"Scrolled {direction}"

    async def take_screenshot(self, name: str = "screenshot.png") -> str:
        await self.start()
        # Save to a temporary or data directory
        os.makedirs("data/screenshots", exist_ok=True)
        path = f"data/screenshots/{name}_{int(time.time())}.png"
        await self.page.screenshot(path=path)
        return path

    async def extract_dom(self):
        await self.start()
        content = await self.page.content()
        return content

# Global instance for async access
# Note: Using a global might be tricky with async loops in FastAPI/Threads, 
# but for simplicity in this architecture we'll manage it.
browser_controller = BrowserController()
