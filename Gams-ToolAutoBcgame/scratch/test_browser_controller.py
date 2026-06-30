from core.browser import BrowserController
import time

print("--- TESTING BROWSERCONTROLLER ---")
b = BrowserController()
if b.start():
    print("BrowserController started Chrome portable successfully!")
    time.sleep(2)
    b.stop()
else:
    print("Failed to start BrowserController!")
print("--- TEST END ---")
