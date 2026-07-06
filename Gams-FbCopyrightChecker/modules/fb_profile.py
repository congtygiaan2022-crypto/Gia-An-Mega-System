"""
Tự động lấy profile URL và danh sách fanpage sau khi đăng nhập.
"""
import json
import re
import time
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from modules.logger import get_logger

log = get_logger(__name__)


def get_profile_info(driver: webdriver.Chrome) -> dict:
    """
    Lấy tên, UID và profile URL của tài khoản đang đăng nhập.
    Trả về: {"name": str, "uid": str, "profile_url": str, "avatar": str}
    """
    from modules.config_loader import CONFIG
    is_mobile = CONFIG.get("mobile_settings", {}).get("enabled", False)
    if is_mobile:
        try:
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": ""})
            driver.execute_cdp_cmd('Emulation.clearDeviceMetricsOverride', {})
        except Exception:
            pass

    try:
        driver.get("https://www.facebook.com/me")
        try:
            # Chờ cho h1 (tên cá nhân) hoặc các thẻ chính hiển thị
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.XPATH, "//h1 | //div[@role='main']"))
            )
        except Exception:
            pass

        profile_url = driver.current_url
        if "profile.php?id=" in profile_url:
            profile_url = profile_url.split("&")[0]
        else:
            profile_url = profile_url.split("?")[0].rstrip("/")

        # Lấy tên hiển thị
        name = ""
        try:
            h1_elements = driver.find_elements(By.XPATH, "//h1")
            for h1 in h1_elements:
                text = h1.text.strip()
                if not text:
                    text = (h1.get_attribute("textContent") or "").strip()
                if text and text.lower() not in ["", "thêm ảnh bìa", "add cover photo", "facebook"]:
                    name = text
                    break
        except Exception:
            pass

        if not name:
            # Fallback dùng Title của trang
            title = driver.title
            if title and "facebook" not in title.lower():
                name = title.strip()

        # Lấy UID từ meta tag hoặc source
        uid = ""
        try:
            page_src = driver.page_source
            m = re.search(r'"userID":"(\d+)"', page_src)
            if not m:
                m = re.search(r'entity_id["\s:]+(\d{5,})', page_src)
            if m:
                uid = m.group(1)
        except Exception:
            pass

        # Lấy avatar
        avatar = ""
        try:
            av_el = driver.find_element(By.XPATH, "//image[@xlink:href] | //img[@data-imgperflogname='profileCover']")
            avatar = av_el.get_attribute("xlink:href") or av_el.get_attribute("src") or ""
        except Exception:
            pass

        log.info(f"Profile: {name} | {profile_url} | uid={uid}")
        return {"name": name, "uid": uid, "profile_url": profile_url, "avatar": avatar}

    except Exception as e:
        log.error(f"Lỗi lấy profile info: {e}")
        return {"name": "", "uid": "", "profile_url": "", "avatar": ""}
    finally:
        if is_mobile:
            try:
                mobile_cfg = CONFIG.get("mobile_settings", {})
                user_agents = mobile_cfg.get("user_agents", [])
                if not user_agents:
                    user_agents = [
                        "Mozilla/5.0 (iPhone; CPU iPhone OS 19_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/130.0.0.0 Mobile/15E148 Safari/604.1"
                    ]
                window_idx = mobile_cfg.get("window_index", 0)
                mobile_ua = user_agents[window_idx % len(user_agents)]
                driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": mobile_ua})
                driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                    "width": 375, "height": 812, "deviceScaleFactor": 3, "mobile": True
                })
            except Exception:
                pass



def get_fanpages(driver: webdriver.Chrome) -> list[dict]:
    """
    Lấy danh sách fanpage bằng cách truy cập /pages/?category=your_pages&ref=bookmarks.
    Cuộn để tải toàn bộ danh sách trang, hỗ trợ click nút "Xem thêm".
    """
    from modules.config_loader import CONFIG
    is_mobile = CONFIG.get("mobile_settings", {}).get("enabled", False)
    if is_mobile:
        try:
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": ""})
            driver.execute_cdp_cmd('Emulation.clearDeviceMetricsOverride', {})
        except Exception:
            pass

    pages = []
    seen = set()
    try:
        driver.get("https://www.facebook.com/pages/?category=your_pages&ref=bookmarks")
        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='main']"))
            )
        except Exception:
            pass

        # Click Xem thêm / Tải thêm nếu có
        for _ in range(5):
            try:
                see_more_btns = driver.find_elements(By.XPATH, "//div[@role='button'][contains(translate(., 'XEM THÊM', 'xem thêm'), 'xem thêm') or contains(translate(., 'TẢI THÊM', 'tải thêm'), 'tải thêm') or contains(translate(., 'SEE MORE', 'see more'), 'see more')]")
                clicked = False
                for btn in see_more_btns:
                    if btn.is_displayed():
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(1.5)
                        clicked = True
                if not clicked:
                    break
            except Exception:
                pass

        # Cuộn thông minh: tối đa 30 lần, dừng khi số lượng card ổn định
        prev_count = 0
        for _ in range(30):
            cards = driver.find_elements(By.XPATH, "//div[@role='main']//a[@href]")
            if len(cards) == prev_count and prev_count > 0:
                break
            prev_count = len(cards)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)

        time.sleep(1)
        cards = driver.find_elements(By.XPATH, "//div[@role='main']//a[@href]")

        for card in cards:
            try:
                href = card.get_attribute("href") or ""
                if not href or "facebook.com" not in href:
                    continue
                # Loại bỏ các link không phải page
                if any(x in href.lower() for x in [
                    "category=", "ref=", "pages/creation", "pages/discover", 
                    "pages/liked", "pages/invocations", "help", "policies", 
                    "ads", "notifications", "settings", "bookmarks", "about", 
                    "marketplace", "gaming", "watch", "groups", "events",
                    "reel", "latest", "inbox", "ad_center"
                ]):
                    continue
                if href.endswith("/pages") or href.endswith("/pages/"):
                    continue
                if "profile.php?id=" in href:
                    href = href.split("&")[0]
                else:
                    href = href.split("?")[0].rstrip("/")
                    
                name = card.text.strip().split("\n")[0]
                if not name or name.lower() in ["", "báo cáo sự cố", "trợ giúp", "đăng xuất", "xem thêm", "tải thêm", "tạo", "tạo trang", "khám phá", "lời mời", "trang đã thích"]:
                    continue

                if href not in seen:
                    seen.add(href)
                    pages.append({
                        "name": name,
                        "url": href,
                        "category": "",
                        "likes": ""
                    })
            except Exception:
                continue

        log.info(f"Tổng hợp tìm thấy {len(pages)} fanpage")
    except Exception as e:
        log.error(f"Lỗi lấy fanpage tổng hợp: {e}")
    finally:
        if is_mobile:
            try:
                mobile_cfg = CONFIG.get("mobile_settings", {})
                user_agents = mobile_cfg.get("user_agents", [])
                if not user_agents:
                    user_agents = [
                        "Mozilla/5.0 (iPhone; CPU iPhone OS 19_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/130.0.0.0 Mobile/15E148 Safari/604.1"
                    ]
                window_idx = mobile_cfg.get("window_index", 0)
                mobile_ua = user_agents[window_idx % len(user_agents)]
                driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": mobile_ua})
                driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                    "width": 375, "height": 812, "deviceScaleFactor": 3, "mobile": True
                })
            except Exception:
                pass

    return pages



def get_fanpages_by_api(token: str) -> list[dict]:
    """
    Lấy danh sách fanpage qua Graph API sử dụng Access Token.
    Tham khảo API: /me/accounts trả về danh sách các Trang mà user có quyền truy cập.
    """
    pages = []
    try:
        url = "https://graph.facebook.com/v19.0/me/accounts"
        params = {
            "access_token": token,
            "limit": 100,
            "fields": "id,name,link,category,fan_count,followers_count,access_token"
        }
        while url:
            resp = requests.get(url, params=params if params else None)
            if resp.status_code != 200:
                log.error(f"Lỗi gọi API: {resp.text}")
                break
            data = resp.json()
            for p in data.get("data", []):
                link = p.get("link")
                if not link:
                    link = f"https://www.facebook.com/{p.get('id')}"
                elif "facebook.com/" in link and "profile.php" not in link and "-" in link:
                    # Đôi khi link trả về có dạng facebook.com/Tên-Trang-ID
                    pass
                
                # Cố gắng lấy số lượng like/follow
                likes = p.get("followers_count", p.get("fan_count", ""))
                
                pages.append({
                    "name": p.get("name", ""),
                    "url": link,
                    "id": p.get("id", ""),
                    "access_token": p.get("access_token", ""),
                    "category": p.get("category", ""),
                    "likes": str(likes)
                })
            
            # Phân trang (Pagination)
            url = data.get("paging", {}).get("next")
            params = {} # params đã bao gồm sẵn trong url 'next'
            
        log.info(f"API lấy được {len(pages)} trang.")
    except Exception as e:
        log.error(f"Lỗi khi lấy fanpage bằng API: {e}")
    return pages


def save_profile_to_config(profile: dict, config_path: str = "config.json"):
    """Lưu profile_url vào config.json."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        cfg["facebook"]["profile_url"] = profile.get("profile_url", "")
        cfg["facebook"]["profile_name"] = profile.get("name", "")
        cfg["facebook"]["uid"] = profile.get("uid", "")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        log.info(f"Đã lưu profile_url: {profile.get('profile_url')}")
    except Exception as e:
        log.error(f"Lỗi lưu config: {e}")
