import sys
import os
import json
from dotenv import load_dotenv

# Setup paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "plugins", "lib"))

from gams_utils import BrowserManager

def main():
    if len(sys.argv) < 2:
        print("Usage: python login_facebook.py <path_to_creds_json>")
        sys.exit(3)
        
    creds_path = sys.argv[1]
    if not os.path.exists(creds_path):
        print(f"Error: Credentials file not found at {creds_path}")
        sys.exit(4)
        
    try:
        with open(creds_path, "r", encoding="utf-8") as f:
            creds = json.load(f)
    except Exception as e:
        print(f"Error reading credentials file: {e}")
        sys.exit(5)
    finally:
        # Delete temp file as soon as we read it for security
        try:
            os.remove(creds_path)
        except:
            pass
            
    username = creds.get("username")
    password = creds.get("password")
    two_factor_secret = creds.get("two_factor_secret")
    
    # Load env for chrome path
    load_dotenv()
    portable_path = os.getenv("CHROME_PORTABLE_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    if not os.path.exists(portable_path):
        paths = [
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ]
        for p in paths:
            if os.path.exists(p):
                portable_path = p
                break
                
    print(f"Using Chrome: {portable_path}")
    print(f"Attempting automated login for username: {username} ...")
    
    bm = BrowserManager(portable_path)
    try:
        success = bm.login_facebook(username, password, two_factor_secret)
        bm.close_browser()
        if success:
            print("LOGIN_SUCCESS")
            sys.exit(0)
        else:
            print("LOGIN_FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"LOGIN_ERROR: {e}")
        try:
            bm.close_browser()
        except:
            pass
        sys.exit(2)

if __name__ == "__main__":
    main()
