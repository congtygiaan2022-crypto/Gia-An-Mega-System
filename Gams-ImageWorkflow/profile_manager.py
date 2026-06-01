import os
import time
from playwright.sync_api import sync_playwright

class ProfileManager:
    def __init__(self, profiles_dir):
        self.profiles_dir = profiles_dir

    def get_profile_dir(self, profile_name):
        path = os.path.join(self.profiles_dir, profile_name)
        abs_path = os.path.abspath(path)
        os.makedirs(abs_path, exist_ok=True)
        return abs_path

    def launch_browser_for_profile(self, p, profile_name, headless=False):
        """
        Launches a persistent browser context for the given profile.
        Returns the context object.
        """
        user_data_dir = self.get_profile_dir(profile_name)
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",
            headless=headless,
            viewport={'width': 1280, 'height': 720},
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars'
            ]
        )
        return context

if __name__ == '__main__':
    # Test
    with sync_playwright() as p:
        pm = ProfileManager("profiles")
        ctx = pm.launch_browser_for_profile(p, "test_profile", headless=False)
        page = ctx.new_page()
        page.goto("https://google.com")
        time.sleep(2)
        ctx.close()
