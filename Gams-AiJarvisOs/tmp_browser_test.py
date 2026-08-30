# -*- coding: utf-8 -*-
"""
Simulate and test BrowserManager to verify all fixes are working.
"""
import sys
import os
import time
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "plugins", "lib"))
sys.path.insert(0, os.path.dirname(__file__))

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"

results = []

def check(name, ok, detail=""):
    status = PASS if ok else FAIL
    results.append((status, name, detail))
    icon = "[OK]" if ok else "[!!]"
    print(f"  {icon} {name}: {detail}")
    return ok


print("=" * 60)
print("GAMS BROWSER TEST - Full simulation")
print("=" * 60)

# ------------------------------------------------------------------ #
# 1. Helper functions
# ------------------------------------------------------------------ #
print("\n[1/6] Helper: _get_chrome_version()")
try:
    from gams_utils import _get_chrome_version
    ver = _get_chrome_version()
    check("Chrome version detected", bool(ver), ver or "empty")
except Exception as e:
    check("_get_chrome_version import", False, str(e))

print("\n[2/6] Helper: _find_best_cached_chromedriver()")
try:
    from gams_utils import _find_best_cached_chromedriver
    drv = _find_best_cached_chromedriver()
    exists = os.path.isfile(drv) if drv else False
    check("Cached ChromeDriver found", bool(drv), drv or "not found")
    check("Cached ChromeDriver file exists", exists, str(exists))
except Exception as e:
    check("_find_best_cached_chromedriver import", False, str(e))

# ------------------------------------------------------------------ #
# 2. Kill-logic safety check (no port-9222 condition in launch_browser)
# ------------------------------------------------------------------ #
print("\n[3/6] Kill-logic safety check")
try:
    gams_utils_path = os.path.join(os.path.dirname(__file__), "plugins", "lib", "gams_utils.py")
    with open(gams_utils_path, "r", encoding="utf-8") as f:
        src = f.read()

    launch_start = src.find("def launch_browser(")
    close_start = src.find("def close_browser(")
    launch_section = src[launch_start:close_start]

    has_port_kill = "remote-debugging-port" in launch_section and "should_kill" in launch_section
    # The only occurrence should be inside options.add_argument, not in kill logic
    # Check: if "remote-debugging-port" appears in a should_kill block
    kill_block_start = launch_section.find("should_kill = False")
    kill_block_end = launch_section.find("options = Options()")
    kill_block = launch_section[kill_block_start:kill_block_end]
    port_in_kill = "remote-debugging-port" in kill_block

    check("Port-9222 NOT in kill block", not port_in_kill,
          "safe - only user-data-dir used" if not port_in_kill else "STILL KILLING BY PORT!")
    check("user-data-dir in kill block", "user-data-dir" in kill_block, "profile-specific kill OK")
except Exception as e:
    check("Kill-logic code scan", False, str(e))

# ------------------------------------------------------------------ #
# 3. BrowserManager launch
# ------------------------------------------------------------------ #
print("\n[4/6] BrowserManager.launch_browser()")
bm = None
try:
    from gams_utils import BrowserManager
    chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    bm = BrowserManager(chrome_exe)
    bm.launch_browser()
    check("launch_browser() succeeded", True, "no exception")
except Exception as e:
    check("launch_browser()", False, str(e))
    traceback.print_exc()

# ------------------------------------------------------------------ #
# 4. check_alive
# ------------------------------------------------------------------ #
print("\n[5/6] check_alive() and navigate_to()")
if bm:
    try:
        alive = bm.check_alive()
        check("check_alive() after launch", alive, str(alive))
    except Exception as e:
        check("check_alive()", False, str(e))

    # Navigate to a simple page
    try:
        ok = bm.navigate_to("https://www.google.com")
        check("navigate_to(google.com)", ok, "loaded OK" if ok else "failed to navigate")
        if ok and bm.driver:
            url = bm.driver.current_url
            check("URL after navigate", "google" in url.lower(), url)
    except Exception as e:
        check("navigate_to()", False, str(e))

    # Test relaunch_browser
    try:
        bm.relaunch_browser()
        alive2 = bm.check_alive()
        check("relaunch_browser() + check_alive()", alive2, "alive after relaunch" if alive2 else "dead after relaunch")
    except Exception as e:
        check("relaunch_browser()", False, str(e))

# ------------------------------------------------------------------ #
# 5. close_browser
# ------------------------------------------------------------------ #
print("\n[6/6] close_browser()")
if bm:
    try:
        bm.close_browser()
        alive_after = bm.check_alive()
        check("close_browser() executed", True, "no exception")
        check("check_alive() after close", not alive_after, "correctly dead" if not alive_after else "still alive - bug!")
    except Exception as e:
        check("close_browser()", False, str(e))

# ------------------------------------------------------------------ #
# Summary
# ------------------------------------------------------------------ #
print()
print("=" * 60)
total = len(results)
passed = sum(1 for s, _, _ in results if s == PASS)
failed = sum(1 for s, _, _ in results if s == FAIL)
print(f"RESULT: {passed}/{total} passed, {failed} failed")
if failed == 0:
    print("ALL TESTS PASSED - Browser setup is healthy!")
else:
    print("SOME TESTS FAILED - See above for details")
    for s, name, detail in results:
        if s == FAIL:
            print(f"  FAILED: {name} -> {detail}")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
