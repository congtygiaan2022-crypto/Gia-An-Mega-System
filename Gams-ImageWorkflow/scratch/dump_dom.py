import sys
import os
import time
from playwright.sync_api import sync_playwright
import db_manager
import profile_manager

def main():
    profile_name = "Yui Hatano"
    print(f"Launching browser for profile: {profile_name}")
    
    pm = profile_manager.ProfileManager("profiles")
    with sync_playwright() as p:
        try:
            # We run headless=True to load the DOM and check frames
            context = pm.launch_browser_for_profile(p, profile_name, headless=True)
            page = context.new_page()
            
            print("Navigating to facebook.com...")
            page.goto("https://www.facebook.com/", timeout=45000)
            print(f"Current URL: {page.url}")
            
            # Wait for 10 seconds to let the checkpoint screen load
            print("Waiting for page to settle...")
            time.sleep(10)
            
            # Print page title
            print(f"Page Title: {page.title()}")
            
            # Capture screenshot
            page.screenshot(path="scratch/dump_checkpoint.png")
            print("Screenshot saved to scratch/dump_checkpoint.png")
            
            # Save HTML
            html_content = page.content()
            with open("scratch/dump_checkpoint.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print("HTML DOM saved to scratch/dump_checkpoint.html")
            
            # Let's inspect the page frames
            print(f"Total frames: {len(page.frames)}")
            for idx, frame in enumerate(page.frames):
                print(f"Frame {idx}: name='{frame.name}', url='{frame.url}'")
                
            context.close()
        except Exception as e:
            print(f"Error during dump: {e}")

if __name__ == "__main__":
    main()
