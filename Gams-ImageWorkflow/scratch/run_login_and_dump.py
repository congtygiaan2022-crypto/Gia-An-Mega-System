import sys
import os
import time
from playwright.sync_api import sync_playwright
import db_manager
import profile_manager
import worker_process

def save_state(page, name):
    try:
        page.screenshot(path=f"scratch/{name}.png")
        print(f"Saved screenshot: scratch/{name}.png")
        with open(f"scratch/{name}.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        print(f"Saved DOM: scratch/{name}.html")
    except Exception as e:
        print(f"Failed to save state {name}: {e}")

def main():
    profile_name = "Yui Hatano"
    print(f"Launching login and dump for profile: {profile_name}")
    
    config = db_manager.get_profile_config(profile_name)
    fb_account = config.get("facebook_account", "").strip()
    if not fb_account:
        global_cfg = db_manager.get_global_config()
        if global_cfg.get("apply_fb_global"):
            fb_account = global_cfg.get("global_facebook_account", "").strip()
            
    if not fb_account:
        print("No facebook credentials found!")
        return
        
    pm = profile_manager.ProfileManager("profiles")
    with sync_playwright() as p:
        try:
            context = pm.launch_browser_for_profile(p, profile_name, headless=True)
            page = context.new_page()
            
            print("Accessing facebook...")
            page.goto("https://www.facebook.com/", timeout=45000)
            page.wait_for_timeout(3000)
            
            save_state(page, "1_after_load")
            
            parts = fb_account.split("|")
            uid = parts[0].strip()
            password = parts[1].strip()
            
            # Fill email/pass with fallback selectors
            try:
                email_selectors = ["input#email", "input[name='email']", "input[type='text']"]
                email_field = None
                for sel in email_selectors:
                    loc = page.locator(sel).first
                    if loc.count() > 0 and loc.is_visible():
                        email_field = loc
                        break
                if email_field:
                    email_field.fill(uid)
                else:
                    print("Could not find email field.")
                    
                pass_selectors = ["input#pass", "input[name='pass']", "input[type='password']"]
                pass_field = None
                for sel in pass_selectors:
                    loc = page.locator(sel).first
                    if loc.count() > 0 and loc.is_visible():
                        pass_field = loc
                        break
                if pass_field:
                    pass_field.fill(password)
                else:
                    print("Could not find password field.")
                    
                page.wait_for_timeout(1000)
                
                # Click Login
                login_selectors = ["button[name='login']", "button[type='submit']", "input[type='submit']"]
                login_btn = None
                for sel in login_selectors:
                    loc = page.locator(sel).first
                    if loc.count() > 0:
                        login_btn = loc
                        break
                if login_btn:
                    login_btn.click()
                else:
                    page.keyboard.press("Enter")
            except Exception as fe:
                print(f"Exception during credentials fill: {fe}")
                save_state(page, "err_fill")
            
            print("Waiting 10 seconds for 2FA/login result...")
            page.wait_for_timeout(10000)
            
            save_state(page, "2_login_result")
            
            # Check frames
            print(f"Total frames: {len(page.frames)}")
            for idx, frame in enumerate(page.frames):
                print(f"Frame {idx}: name='{frame.name}', url='{frame.url}'")
                try:
                    with open(f"scratch/frame_{idx}.html", "w", encoding="utf-8") as f:
                        f.write(frame.content())
                    print(f"Dumped frame {idx} DOM")
                except Exception as fe:
                    print(f"Failed to dump frame {idx}: {fe}")
                    
            context.close()
        except Exception as e:
            print(f"Error during login and dump: {e}")

if __name__ == "__main__":
    main()
