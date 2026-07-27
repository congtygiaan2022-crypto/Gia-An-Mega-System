import sys
import os
import time
from playwright.sync_api import sync_playwright
import db_manager
import profile_manager

def main():
    profile_name = "Yui Hatano"
    print("Inspecting active button properties for profile...")
    
    config = db_manager.get_profile_config(profile_name)
    fb_account = config.get("facebook_account", "").strip()
    if not fb_account:
        global_cfg = db_manager.get_global_config()
        if global_cfg.get("apply_fb_global"):
            fb_account = global_cfg.get("global_facebook_account", "").strip()
            
    if not fb_account:
        print("No Facebook account configured!")
        return
        
    parts = [p.strip() for p in fb_account.split("|")]
    uid = parts[0]
    password = parts[1]
    
    pm = profile_manager.ProfileManager("profiles")
    with sync_playwright() as p:
        try:
            context = pm.launch_browser_for_profile(p, profile_name, headless=True)
            page = context.new_page()
            page.goto("https://www.facebook.com/login", timeout=45000)
            page.wait_for_timeout(3000)
            
            page.fill("input[name='email']", uid)
            page.fill("input[name='pass']", password)
            page.wait_for_timeout(1000)
            
            login_btn = page.locator("button[name='login'], button[type='submit']").first
            if login_btn.count() > 0:
                login_btn.click()
            else:
                page.keyboard.press("Enter")
                
            page.wait_for_timeout(10000)
            
            # Find the frame
            target_frame = None
            for frame in page.frames:
                if "two_factor" in frame.url or "two_step" in frame.url:
                    target_frame = frame
                    break
                    
            if not target_frame:
                print("Two-factor frame not found.")
                context.close()
                return
                
            # Click Thử cách khác
            print("Clicking Try other way...")
            try_other_xpath = "//div[@role='button'][contains(.,'Thử cách khác') or contains(.,'Try another way')]"
            target_frame.locator(try_other_xpath).first.click()
            page.wait_for_timeout(3000)
            
            # Click Ứng dụng xác thực
            print("Selecting Authenticator App...")
            auth_app_xpath = "//span[contains(text(),'Ứng dụng xác thực') or contains(text(),'Authentication app')]/ancestor::div[@role='radio']"
            target_frame.locator(auth_app_xpath).first.click()
            page.wait_for_timeout(2000)
            
            # Now we have both continue buttons in the DOM. Let's inspect them!
            c_sel = "//div[@role='button'][contains(.,'Tiếp tục') or contains(.,'Continue')]"
            locs = target_frame.locator(c_sel).all()
            print(f"Total Continue buttons found: {len(locs)}")
            
            out_lines = []
            for i, loc in enumerate(locs):
                info = loc.evaluate("""el => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    
                    // Check parent chain for opacity or transform or aria-hidden
                    let parent = el;
                    let parentChain = [];
                    let hasHiddenParent = false;
                    while (parent) {
                        const pStyle = window.getComputedStyle(parent);
                        const pAriaHidden = parent.getAttribute('aria-hidden');
                        parentChain.push({
                            tag: parent.tagName,
                            opacity: pStyle.opacity,
                            display: pStyle.display,
                            visibility: pStyle.visibility,
                            transform: pStyle.transform,
                            ariaHidden: pAriaHidden
                        });
                        if (pAriaHidden === 'true' || pStyle.opacity === '0' || pStyle.display === 'none') {
                            hasHiddenParent = true;
                        }
                        parent = parent.parentElement;
                    }
                    
                    return {
                        text: el.innerText,
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height,
                        opacity: style.opacity,
                        display: style.display,
                        transform: style.transform,
                        isIntersecting: rect.x >= 0 && rect.y >= 0 && rect.width > 0 && rect.height > 0,
                        hasHiddenParent: hasHiddenParent,
                        parentChain: parentChain.slice(0, 5)
                    };
                }""")
                out_lines.append(f"\n--- Button {i} ---")
                out_lines.append(f"Text: '{info['text']}'")
                out_lines.append(f"Rect: x={info['x']}, y={info['y']}, width={info['width']}, height={info['height']}")
                out_lines.append(f"Opacity: {info['opacity']}, Display: {info['display']}, Transform: {info['transform']}")
                out_lines.append(f"IsIntersecting (x,y >= 0): {info['isIntersecting']}")
                out_lines.append(f"Has Hidden Parent (aria-hidden/opacity 0/display none): {info['hasHiddenParent']}")
                out_lines.append("Parent Chain:")
                for p_idx, p in enumerate(info['parentChain']):
                    out_lines.append(f"  Parent {p_idx}: tag={p['tag']}, opacity={p['opacity']}, display={p['display']}, transform={p['transform']}, ariaHidden={p['ariaHidden']}")
            
            with open("scratch/inspect_button_result.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(out_lines))
            print("Successfully wrote details to scratch/inspect_button_result.txt")
            
            context.close()
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
