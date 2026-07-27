import sys
import os
import time
import re
from playwright.sync_api import sync_playwright
import db_manager
import profile_manager

def main():
    profile_name = "Yui Hatano"
    print(f"Inspecting frame DOM for profile: {profile_name}")
    
    config = db_manager.get_profile_config(profile_name)
    fb_account = config.get("facebook_account", "").strip()
    if not fb_account:
        global_cfg = db_manager.get_global_config()
        if global_cfg.get("apply_fb_global"):
            fb_account = global_cfg.get("global_facebook_account", "").strip()
            
    if not fb_account:
        print("No facebook credentials found!")
        return
        
    parts = fb_account.split("|")
    uid = parts[0].strip()
    password = parts[1].strip()
    
    pm = profile_manager.ProfileManager("profiles")
    with sync_playwright() as p:
        try:
            context = pm.launch_browser_for_profile(p, profile_name, headless=True)
            page = context.new_page()
            
            print("Accessing facebook login page...")
            page.goto("https://www.facebook.com/login", timeout=45000)
            page.wait_for_timeout(3000)
            
            print("Filling email and pass...")
            page.fill("input[name='email']", uid)
            page.fill("input[name='pass']", password)
            page.wait_for_timeout(1000)
            
            print("Submitting login...")
            login_btn = page.locator("button[name='login'], button[type='submit']").first
            if login_btn.count() > 0:
                login_btn.click()
            else:
                page.keyboard.press("Enter")
                
            print("Waiting 10 seconds for 2FA screen to load...")
            page.wait_for_timeout(10000)
            
            print(f"Current page URL: {page.url}")
            
            # Find the two-factor frame
            target_frame = None
            for frame in page.frames:
                print(f"Frame URL: {frame.url}")
                if "two_factor" in frame.url or "two_step" in frame.url:
                    target_frame = frame
                    break
                    
            if not target_frame:
                print("Could not find two-factor frame. Inspecting all page buttons:")
                buttons = page.locator("div[role='button'], button").all()
                for i, btn in enumerate(buttons):
                    try:
                        print(f"Page Button {i}: text='{btn.inner_text()}', html='{btn.evaluate('el => el.outerHTML[:200]')}'")
                    except:
                        pass
                
                # Take screenshot
                page.screenshot(path="scratch/inspect_no_frame.png")
                context.close()
                return
                
            print(f"Found target frame: {target_frame.url}")
            
            # Print target frame buttons
            buttons = target_frame.locator("div[role='button'], button").all()
            print(f"Total buttons in frame: {len(buttons)}")
            for i, btn in enumerate(buttons):
                try:
                    text = btn.inner_text().strip()
                    html = btn.evaluate("el => el.outerHTML")
                    print(f"\n--- Frame Button {i} (text: '{text}') ---")
                    print(html)
                except Exception as e:
                    print(f"Error printing button {i}: {e}")
                    
            # Save the frame HTML
            frame_html = target_frame.content()
            with open("scratch/frame_two_factor.html", "w", encoding="utf-8") as f:
                f.write(frame_html)
            print("Saved frame DOM to scratch/frame_two_factor.html")
            
            # Save parent DOM
            with open("scratch/parent_two_factor.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            print("Saved parent DOM to scratch/parent_two_factor.html")
            
            page.screenshot(path="scratch/inspect_success.png")
            context.close()
        except Exception as e:
            print(f"Error during inspection: {e}")

if __name__ == "__main__":
    main()
