import sys
import os
import time

# Add project root to path
sys.path.append(os.getcwd())

from computer.browser_vision import browser_vision

def test_vision():
    print("--- Testing Browser Vision ---")
    try:
        print("Starting browser...")
        browser_vision.start()
        
        print("Opening Google...")
        browser_vision.open("google.com")
        
        print("Getting DOM elements...")
        elements = browser_vision.get_dom_elements()
        print(f"Found {len(elements)} relevant elements.")
        
        # We tip the test to use the search box if possible
        # On Google, search box is often an input with name='q' or certain placeholder
        print("Attempting to type 'herbal tea' by placeholder/text search...")
        # We use a broad placeholder search for 'search' or similar
        res = browser_vision.type_by_placeholder("herbal tea", "search")
        print(res)
        
        # If placeholder fails, we might just try a direct fill for 'q' if we knew it, 
        # but here we test the vision-like logic.
        
        print("Attempting to click 'Google Search' or 'Search'...")
        res = browser_vision.click_by_text("Search")
        print(res)
        
        print("Capturing vision screenshot...")
        path = browser_vision.screenshot()
        print(path)
        
        browser_vision.stop()
        print("--- Vision Test Completed ---")
    except Exception as e:
        print(f"Browser Vision error: {e}")
        try: browser_vision.stop()
        except: pass

if __name__ == "__main__":
    test_vision()
