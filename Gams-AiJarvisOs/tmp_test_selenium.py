import os
import sys
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

if __name__ == "__main__":
    print("Testing Selenium ChromeDriver Launch...")
    portable_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    options = Options()
    options.binary_location = portable_path
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--start-maximized")
    
    user_data_dir = os.path.abspath(os.path.join(os.getcwd(), "plugins", "data", "gams_insight", "user_data"))
    options.add_argument(f"user-data-dir={user_data_dir}")

    print(f"Chrome Path: {portable_path} (exists: {os.path.exists(portable_path)})")
    print(f"User Data Dir: {user_data_dir}")

    try:
        print("Installing ChromeDriver...")
        driver_path = ChromeDriverManager().install()
        print(f"Driver Path: {driver_path} (exists: {os.path.exists(driver_path)})")
        
        print("Launching WebDriver...")
        driver = webdriver.Chrome(service=ChromeService(driver_path), options=options)
        print("WebDriver launched successfully!")
        driver.quit()
    except Exception as e:
        print(f"\nFailed to launch WebDriver: {e}")
        traceback.print_exc()
