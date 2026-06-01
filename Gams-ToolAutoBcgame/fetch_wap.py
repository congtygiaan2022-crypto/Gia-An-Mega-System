import undetected_chromedriver as uc
import time

def fetch_wap_html():
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    driver = uc.Chrome(
        options=options, 
        browser_executable_path=r"D:\laptrinh_code\Tool_auto_bcgame\bin\chrome\chrome.exe", 
        version_main=124
    )
    
    driver.get("https://bongda.wap.vn/nhan-dinh-bong-da.html")
    time.sleep(3)
    
    with open("wap_debug.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    
    driver.quit()
    print("Done")

if __name__ == "__main__":
    fetch_wap_html()
