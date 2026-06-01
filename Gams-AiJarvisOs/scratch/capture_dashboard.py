import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def capture():
    print("Initializing headless Chrome to capture dashboard...")
    options = Options()
    options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1440,900")
    
    driver_path = ChromeDriverManager().install()
    driver = webdriver.Chrome(service=ChromeService(driver_path), options=options)
    
    try:
        print("Navigating to http://127.0.0.1:8080/ ...")
        driver.get("http://127.0.0.1:8080/")
        time.sleep(3)  # wait for initial render
        
        # Click on "Kho Công Cụ" menu item to switch to that tab
        # Let's find the element containing "Kho Công Cụ"
        menu_items = driver.find_elements(By.CLASS_NAME, "nav-item")
        for item in menu_items:
            if "Kho Công Cụ" in item.text:
                print("Clicking on 'Kho Công Cụ' menu item...")
                item.click()
                time.sleep(2)  # wait for tab to load and render
                break
        
        screenshot_path = os.path.abspath("dashboard_tools_capture.png")
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
        
    except Exception as e:
        print(f"Error during capture: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    capture()
