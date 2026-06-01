from playwright.sync_api import sync_playwright
from tools.tool_registry import tool
import os
import time
import random

# ---------------------------------------------------------------------------
# Jarvis-owned browser instance — completely separate from any user browsers.
# Only browser_close() will ever touch these globals.
# ---------------------------------------------------------------------------
_browser = None
_playwright = None
_page = None

# Stealth
try:
    from playwright_stealth import stealth_sync
    _STEALTH_AVAILABLE = True
except ImportError:
    _STEALTH_AVAILABLE = False

# 2Captcha solver (lazy import to avoid circular deps)
def _get_captcha_solver():
    try:
        from tools.captcha_solver import captcha_solver
        return captcha_solver
    except Exception:
        return None

# Real Chrome user-agent
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

# Extension folder — drop any unpacked .crx / folder here
# Override via env: JARVIS_EXTENSION_DIR=C:/path/to/extension
_EXT_DIR = os.getenv(
    "JARVIS_EXTENSION_DIR",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "extensions")
)


def _load_extensions() -> list[str]:
    """Return list of extension directories found in extensions/ folder."""
    if not os.path.isdir(_EXT_DIR):
        return []
    exts = []
    for name in os.listdir(_EXT_DIR):
        path = os.path.join(_EXT_DIR, name)
        if os.path.isdir(path) and os.path.exists(os.path.join(path, "manifest.json")):
            exts.append(path)
    return exts


def _get_page():
    global _browser, _playwright, _page
    if _page is None:
        _playwright = sync_playwright().start()

        extensions = _load_extensions()
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-infobars",
        ]

        if extensions:
            ext_paths = ",".join(extensions)
            launch_args += [
                f"--disable-extensions-except={ext_paths}",
                f"--load-extension={ext_paths}",
            ]
            # Extensions require non-headless
            _browser = _playwright.chromium.launch_persistent_context(
                user_data_dir=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".browser_profile"),
                headless=False,
                args=launch_args,
                user_agent=_USER_AGENT,
                viewport={"width": 1280, "height": 800},
                locale="vi-VN",
            )
            _page = _browser.new_page()
        else:
            _browser = _playwright.chromium.launch(headless=False, args=launch_args)
            context = _browser.new_context(
                user_agent=_USER_AGENT,
                viewport={"width": 1280, "height": 800},
                locale="vi-VN",
            )
            _page = context.new_page()

        if _STEALTH_AVAILABLE:
            stealth_sync(_page)

    return _page


def _human_type(page, selector: str, text: str):
    """Type text character by character with random delays — mimics human typing."""
    page.click(selector)
    for char in text:
        page.keyboard.type(char)
        time.sleep(random.uniform(0.04, 0.12))


@tool(description="Open a webpage in the browser. Arguments: url (str)")
def browser_open(url: str):
    page = _get_page()
    if not url.startswith("http"):
        url = f"https://{url}"
    page.goto(url, wait_until="domcontentloaded", timeout=20000)

    # Auto-solve captcha if detected
    solver = _get_captcha_solver()
    if solver and solver.is_configured():
        solver.auto_solve(page)

    return f"Opened {url}"

@tool(description="Take a screenshot of the current page. Returns the file path. Arguments: None")
def browser_screenshot():
    page = _get_page()
    os.makedirs("memory", exist_ok=True)
    path = "memory/screenshot.png"
    page.screenshot(path=path)
    return f"Screenshot saved to {path}"

@tool(description="Click an element on the page using a CSS selector. Arguments: selector (str)")
def browser_click(selector: str):
    page = _get_page()
    page.click(selector)
    page.wait_for_timeout(1000)
    return f"Clicked {selector}"

@tool(description="Type text into an input field using a CSS selector. Arguments: selector (str), text (str)")
def browser_type(selector: str, text: str):
    page = _get_page()
    page.fill(selector, text)
    return f"Typed '{text}' into {selector}"

@tool(description="Extract all text matching a CSS selector. Arguments: selector (str)")
def browser_extract(selector: str):
    page = _get_page()
    try:
        # Wait briefly for any in-progress navigation to settle
        try:
            page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            pass
        elements = page.query_selector_all(selector)
        results = []
        for el in elements:
            try:
                results.append(el.inner_text())
            except Exception:
                continue  # element detached during navigation
        return results
    except Exception as e:
        return [f"Extract error: {e}"]

@tool(description="Search Google using the browser. Arguments: query (str)")
def browser_search(query: str):
    page = _get_page()
    browser_open("https://www.google.com")

    # Google changed its DOM — try selectors in priority order
    SEARCH_SELECTORS = [
        "textarea[name='q']",   # current Google (2024+)
        "input[name='q']",      # older Google
        "textarea",             # generic fallback
    ]

    filled = False
    for sel in SEARCH_SELECTORS:
        try:
            page.wait_for_selector(sel, timeout=5000)
            _human_type(page, sel, query)          # human-like typing
            time.sleep(random.uniform(0.3, 0.7))   # pause before Enter
            page.keyboard.press("Enter")
            filled = True
            break
        except Exception:
            continue

    if not filled:
        return f"Could not find Google search box. Selectors tried: {SEARCH_SELECTORS}"

    # Wait for results page to fully load before extracting
    try:
        page.wait_for_load_state("domcontentloaded", timeout=12000)
    except Exception:
        pass
    try:
        # Extra safety: wait for at least one h3 to appear
        page.wait_for_selector("h3", timeout=8000)
    except Exception:
        pass

    results = browser_extract("h3")
    return results if results else "Search completed but no h3 results found."


@tool(description="Check if Jarvis browser session is currently open. Returns bool.")
def is_browser_open() -> bool:
    return _page is not None and _browser is not None


@tool(description="Close the Jarvis browser session to free memory. Only closes Jarvis browser, never touches other user sessions.")
def browser_close() -> str:
    """Safely close ONLY the Jarvis-owned Playwright browser instance."""
    global _browser, _playwright, _page
    if _browser is None and _playwright is None:
        return "Browser already closed (nothing to do)."
    try:
        if _page:
            try:
                _page.close()
            except Exception:
                pass
            _page = None
        if _browser:
            _browser.close()
            _browser = None
        if _playwright:
            _playwright.stop()
            _playwright = None
        return "Jarvis browser session closed and memory freed."
    except Exception as e:
        return f"Browser close error: {e}"
