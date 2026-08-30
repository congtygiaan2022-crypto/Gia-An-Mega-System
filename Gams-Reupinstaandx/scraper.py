import os
import re
import time
import base64
import urllib.request
import traceback
import subprocess
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass
import db_manager

def p_log(profile_name, msg):
    print(msg)
    try:
        db_manager.log_msg(profile_name, msg)
    except Exception:
        pass

def extract_instagram_shortcode(url):
    # Trích xuất shortcode từ URL Instagram (post hoặc reel)
    # Ví dụ: https://www.instagram.com/p/C8pa_xyz/ -> C8pa_xyz
    match = re.search(r'/(?:p|reel)/([A-Za-z0-9_-]+)', url)
    if match:
        return match.group(1)
    return url

def scrape_instagram_profile(page, profile_url, num_posts=3, profile_name="System"):
    """
    Truy cập vào trang cá nhân Instagram và lấy danh sách các bài viết gần nhất.
    """
    p_log(profile_name, f"Đang truy cập trang cá nhân Instagram: {profile_url}")
    
    try:
        page.goto(profile_url, timeout=60000)
        page.wait_for_timeout(5000)
        
        # Đóng popup đăng nhập nếu hiển thị (nhấn Escape)
        for _ in range(2):
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            
        # Đợi các liên kết bài viết xuất hiện
        try:
            page.wait_for_selector('a[href*="/p/"], a[href*="/reel/"]', timeout=15000)
        except Exception:
            p_log(profile_name, "Không tìm thấy bài viết nào trên trang cá nhân. Có thể tài khoản riêng tư hoặc bị chặn đăng nhập.")
            # Chụp ảnh debug
            os.makedirs("scratch", exist_ok=True)
            page.screenshot(path=f"scratch/insta_profile_error.png")
            return []
            
        # Lấy các liên kết bài viết bằng cách cuộn trang nếu cần
        posts = []
        seen_ids = set()
        
        for scroll_attempt in range(4):
            links = page.locator('a[href*="/p/"], a[href*="/reel/"]').all()
            for link in links:
                if len(posts) >= num_posts:
                    break
                try:
                    href = link.get_attribute("href")
                    if not href:
                        continue
                    # Chuẩn hóa URL
                    if href.startswith("/"):
                        full_url = f"https://www.instagram.com{href}"
                    else:
                        full_url = href
                        
                    shortcode = extract_instagram_shortcode(full_url)
                    if shortcode and shortcode not in seen_ids:
                        seen_ids.add(shortcode)
                        posts.append({
                            "id": shortcode,
                            "url": full_url
                        })
                except Exception as e:
                    pass
            if len(posts) >= num_posts:
                break
            page.evaluate("window.scrollBy(0, 1000)")
            page.wait_for_timeout(2000)
                
        p_log(profile_name, f"Quét được {len(posts)} bài viết gần nhất từ Instagram.")
        return posts
    except Exception as e:
        p_log(profile_name, f"Lỗi quét Instagram profile: {e}")
        return []

def scrape_instagram_post(page, post_url, profile_name="System"):
    """
    Truy cập trang chi tiết bài viết Instagram để lấy caption và media URL.
    """
    p_log(profile_name, f"Đang cào chi tiết bài viết Instagram: {post_url}")
    
    try:
        page.goto(post_url, timeout=60000)
        page.wait_for_timeout(4000)
        
        # Đóng popup đăng nhập nếu hiển thị bằng nhiều cách
        close_selectors = [
            'svg[aria-label="Close"]',
            'svg[aria-label="Đóng"]',
            'div[role="dialog"] svg',
            'div[role="dialog"] button',
            'button:has-text("Close")',
            'button:has-text("Đóng")',
            '[aria-label="Close"]',
            '[aria-label="Đóng"]'
        ]
        for sel in close_selectors:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible(timeout=1500):
                    loc.click()
                    page.wait_for_timeout(500)
                    break
            except Exception:
                pass
                
        # Vẫn nhấn Escape dự phòng
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        
        # 1. Lay Caption (Van ban) - Thu nhieu phuong phap
        caption = ""
        
        # Phuong phap 1 (UU TIEN CAO NHAT): meta og:description
        # Format: "18K likes, 403 comments - username on Date: \"caption text here\". "
        try:
            meta = page.locator('meta[property="og:description"], meta[name="description"]').first
            if meta.count() > 0:
                content = meta.get_attribute("content") or ""
                # Tim noi dung trong cap ngoac kep cuoi cung: key: "..."
                match = re.search(r':\s*"(.+?)"\s*\.?\s*$', content, re.DOTALL)
                if match:
                    t = match.group(1).strip()
                    if t and len(t) > 3:
                        caption = t
                elif ': ' in content:
                    # Fallback: lay phan sau dau ":" cuoi cung
                    parts = content.split(': ', 1)
                    if len(parts) > 1 and len(parts[1]) > 5:
                        caption = parts[1].strip().strip('"').strip()
        except Exception:
            pass
        
        # Phuong phap 2: article h1 (caption dang text dai)
        if not caption:
            try:
                h1_loc = page.locator('article h1').first
                if h1_loc.count() > 0:
                    t = h1_loc.inner_text().strip()
                    if t and len(t) > 5:
                        caption = t
            except Exception:
                pass
        
        # Phuong phap 3: span._ap3a (class caption Instagram hien tai)
        if not caption:
            for sel in [
                'article span._ap3a',
                'span._ap3a',
                'div._a9zs span',
                'div[class*="caption"] span',
                'h1 + div span',
                'div[data-testid*="caption"] span',
            ]:
                try:
                    loc = page.locator(sel).first
                    if loc.count() > 0:
                        t = loc.inner_text().strip()
                        if t and len(t) > 5:
                            caption = t
                            break
                except Exception:
                    pass
        
        # Phuong phap 4: page title regex
        if not caption:
            try:
                title = page.title()
                match = re.search(r'on Instagram:\s*"(.+?)"', title, re.DOTALL)
                if match:
                    caption = match.group(1).strip()
            except Exception:
                pass
        
        # Phuong phap 5: Lay tat ca text trong article, chon doan dai nhat
        if not caption:
            try:
                spans = page.locator('article span:not([class*="username"]):not([class*="time"])').all()
                best = ""
                for sp in spans:
                    try:
                        t = sp.inner_text().strip()
                        if t and len(t) > len(best) and len(t) > 20:
                            best = t
                    except:
                        pass
                if best:
                    caption = best
            except Exception:
                pass
        
        p_log(profile_name, f"Caption Instagram (do dai {len(caption)}): '{caption[:120]}'")
        
                
        # 2. Xác định loại media và URL tải về
        media_type = "image"
        media_url = ""
        
        # Tìm trong article trước để tránh lấy nhầm media ở ngoài (như trong popup/login)
        article_loc = page.locator('article').first
        if article_loc.count() > 0:
            # Kiểm tra xem có video không
            try:
                video_loc = article_loc.locator('video').first
                if video_loc.count() > 0:
                    media_type = "video"
                    
                    # Click nhẹ để kích hoạt video load src
                    try:
                        video_loc.click()
                        page.wait_for_timeout(2000)
                    except:
                        pass
                        
                    media_url = video_loc.get_attribute("src")
                    if not media_url:
                        source_loc = video_loc.locator('source').first
                        if source_loc.count() > 0:
                            media_url = source_loc.get_attribute("src")
                            
                    p_log(profile_name, f"Phát hiện bài viết dạng Video trong article. URL: {media_url[:80] if media_url else 'None'}")
            except Exception:
                pass
                
            # Nếu không có video, tìm ảnh
            if not media_url:
                try:
                    img_locs = article_loc.locator('img').all()
                    valid_imgs = []
                    for img in img_locs:
                        src = img.get_attribute("src")
                        alt = img.get_attribute("alt") or ""
                        if src and src.startswith("http"):
                            # Bỏ qua avatar của tác giả
                            if any(x in alt.lower() for x in ["profile picture", "profile photo", "ảnh đại diện", "avatar"]):
                                continue
                            # Kiểm tra kích thước để lọc ảnh đại diện/icon
                            try:
                                box = img.bounding_box()
                                if box and (box['width'] < 150 or box['height'] < 150):
                                    continue
                                nat_w = img.evaluate('el => el.naturalWidth')
                                if nat_w > 0 and nat_w < 150:
                                    continue
                            except Exception:
                                pass
                            if src not in valid_imgs:
                                valid_imgs.append(src)
                                
                    if len(valid_imgs) > 1:
                        media_type = "multi_image"
                        media_url = valid_imgs
                        p_log(profile_name, f"Phát hiện bài viết Carousel/Nhiều Ảnh ({len(valid_imgs)} ảnh) trong article.")
                    elif len(valid_imgs) == 1:
                        media_type = "image"
                        media_url = valid_imgs[0]
                        p_log(profile_name, "Phát hiện bài viết dạng 1 Ảnh trong article.")
                    else:
                        media_type = "status"
                        media_url = ""
                        p_log(profile_name, "Phát hiện bài viết dạng STATUS (văn bản chỉ có chữ).")
                except Exception as img_err:
                    p_log(profile_name, f"Lỗi quét ảnh: {img_err}")
        else:
            # Fallback nếu không tìm thấy article
            try:
                video_loc = page.locator('video').first
                if video_loc.count() > 0:
                    media_type = "video"
                    media_url = video_loc.get_attribute("src")
            except Exception:
                pass
                
            if not media_url:
                try:
                    img_locs = page.locator('img').all()
                    for img in img_locs:
                        src = img.get_attribute("src")
                        alt = img.get_attribute("alt") or ""
                        if src and src.startswith("http"):
                            if any(x in alt.lower() for x in ["profile picture", "profile photo", "ảnh đại diện", "avatar"]):
                                continue
                            try:
                                box = img.bounding_box()
                                if box and (box['width'] < 150 or box['height'] < 150):
                                    continue
                                nat_w = img.evaluate('el => el.naturalWidth')
                                if nat_w > 0 and nat_w < 150:
                                    continue
                            except:
                                pass
                            media_url = src
                            media_type = "image"
                            break
                except Exception:
                    pass
                    
        if not media_url:
            # Fallback cuối cùng lấy ảnh đầu tiên lớn hơn 150px của article
            try:
                img_locs = page.locator('article img').all()
                for img in img_locs:
                    try:
                        box = img.bounding_box()
                        if box and (box['width'] >= 150 and box['height'] >= 150):
                            src = img.get_attribute("src")
                            if src:
                                media_url = src
                                media_type = "image"
                                break
                    except:
                        pass
            except Exception:
                pass
                
        return {
            "caption": caption,
            "media_type": media_type,
            "media_url": media_url
        }
    except Exception as e:
        p_log(profile_name, f"Lỗi cào Instagram post: {e}")
        return None

def scrape_x_profile(page, profile_url, num_posts=3, profile_name="System"):
    """
    Truy cập trang cá nhân X (Twitter) và lấy thông tin các bài đăng mới nhất từ timeline.
    """
    p_log(profile_name, f"Đang truy cập trang cá nhân X: {profile_url}")
    
    try:
        page.goto(profile_url, timeout=60000)
        page.wait_for_timeout(6000)
        
        # Đợi các tweet hiển thị
        try:
            page.wait_for_selector('article', timeout=20000)
        except Exception:
            p_log(profile_name, "Không tìm thấy tweet nào trên dòng thời gian. Có thể bị chặn đăng nhập hoặc tài khoản không tồn tại.")
            # Chụp ảnh debug
            os.makedirs("scratch", exist_ok=True)
            page.screenshot(path=f"scratch/x_profile_error.png")
            return []
            
        posts = []
        seen_ids = set()
        
        for scroll_attempt in range(4):
            tweets_locators = page.locator('article').all()
            for tweet in tweets_locators:
                if len(posts) >= num_posts:
                    break
                try:
                    # 1. Trích xuất link chi tiết và ID của tweet
                    status_link = tweet.locator('a[href*="/status/"]').first
                    if status_link.count() == 0:
                        continue
                    href = status_link.get_attribute("href")
                    if not href:
                        continue
                    
                    if href.startswith("/"):
                        full_url = f"https://x.com{href}"
                    else:
                        full_url = href
                        
                    tweet_id = full_url.split("/status/")[-1].split("?")[0]
                    if tweet_id in seen_ids:
                        continue
                    seen_ids.add(tweet_id)
                    
                    # 2. Lấy văn bản tweet (caption)
                    text_loc = tweet.locator('div[data-testid="tweetText"], div.font-chirp, div[class*="font-chirp"]').first
                    caption = text_loc.inner_text().strip() if text_loc.count() > 0 else ""
                    
                    # 3. Xác định loại media
                    media_type = "text"
                    media_url = ""
                    
                    # Kiểm tra video trước
                    video_loc = tweet.locator('video, div[data-testid="videoPlayer"]').first
                    if video_loc.count() > 0:
                        media_type = "video"
                        media_url = full_url # X video uses blob, we will pass the status URL to yt-dlp to download
                        p_log(profile_name, f"Phát hiện Tweet {tweet_id} dạng Video.")
                    else:
                        # Kiểm tra ảnh (ảnh đính kèm twimg/media)
                        photo_loc = tweet.locator('img[src*="pbs.twimg.com/media/"], div[data-testid="tweetPhoto"] img').first
                        if photo_loc.count() > 0:
                            media_type = "image"
                            raw_url = photo_loc.get_attribute("src") or ""
                            # Nâng cấp lên chất lượng gốc: thay name=small/medium/large -> name=orig
                            if raw_url and "pbs.twimg.com" in raw_url:
                                raw_url = re.sub(r'[?&]name=[^&]+', '', raw_url)
                                sep = '&' if '?' in raw_url else '?'
                                media_url = raw_url + sep + "name=orig"
                            else:
                                media_url = raw_url
                            p_log(profile_name, f"Phát hiện Tweet {tweet_id} dạng Ảnh (full-size).")
                            
                    posts.append({
                        "id": tweet_id,
                        "url": full_url,
                        "caption": caption,
                        "media_type": media_type,
                        "media_url": media_url
                    })
                except Exception as e:
                    pass
            if len(posts) >= num_posts:
                break
            page.evaluate("window.scrollBy(0, 1000)")
            page.wait_for_timeout(2000)
                
        p_log(profile_name, f"Quét được {len(posts)} Tweet gần nhất từ X.")
        return posts
    except Exception as e:
        p_log(profile_name, f"Lỗi quét X profile: {e}")
        return []

def scrape_x_post(page, post_url, profile_name="System"):
    """
    Truy cập trang chi tiết tweet X (Twitter) để lấy caption và media URL.
    """
    p_log(profile_name, f"Đang cào chi tiết tweet X: {post_url}")
    try:
        page.goto(post_url, timeout=60000)
        page.wait_for_timeout(5000)
        
        # Đợi phần article hiển thị
        try:
            page.wait_for_selector('article', timeout=15000)
        except Exception:
            p_log(profile_name, "Không tìm thấy tweet article chi tiết.")
            return None
            
        tweet = page.locator('article').first
        if tweet.count() == 0:
            return None
            
        # Lấy caption
        text_loc = tweet.locator('div[data-testid="tweetText"], div.font-chirp, div[class*="font-chirp"]').first
        caption = text_loc.inner_text().strip() if text_loc.count() > 0 else ""
        
        # Xác định media
        media_type = "text"
        media_url = ""
        
        # Video
        video_loc = tweet.locator('video, div[data-testid="videoPlayer"]').first
        if video_loc.count() > 0:
            media_type = "video"
            media_url = post_url
            p_log(profile_name, "Phát hiện tweet dạng Video.")
        else:
            # Ảnh
            photo_loc = tweet.locator('img[src*="pbs.twimg.com/media/"], div[data-testid="tweetPhoto"] img').first
            if photo_loc.count() > 0:
                media_type = "image"
                raw_url = photo_loc.get_attribute("src") or ""
                if raw_url and "pbs.twimg.com" in raw_url:
                    raw_url = re.sub(r'[?&]name=[^&]+', '', raw_url)
                    sep = '&' if '?' in raw_url else '?'
                    media_url = raw_url + sep + "name=orig"
                else:
                    media_url = raw_url
                p_log(profile_name, "Phát hiện tweet dạng Ảnh.")
                
        return {
            "caption": caption,
            "media_type": media_type,
            "media_url": media_url
        }
    except Exception as e:
        p_log(profile_name, f"Lỗi cào chi tiết tweet X: {e}")
        return None

def download_file_direct(url, output_path):
    # Tải file trực tiếp qua urllib
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        )
        with urllib.request.urlopen(req, timeout=30) as response, open(output_path, 'wb') as out_file:
            out_file.write(response.read())
        return True
    except Exception:
        return False

def download_file_in_browser(page, url, output_path):
    # Tải file bằng cách fetch trong ngữ cảnh trình duyệt và gửi base64 về Python
    try:
        if url.startswith("blob:"):
            try:
                # Dành cho blob URL: tạo thẻ <a>, click để tải về
                with page.expect_download(timeout=15000) as download_info:
                    page.evaluate("""(blobUrl) => {
                        const a = document.createElement('a');
                        a.href = blobUrl;
                        a.download = 'temp_file';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                    }""", url)
                download = download_info.value
                download.save_as(output_path)
                return True
            except Exception as blob_err:
                print(f"Error downloading blob via click: {blob_err}")
                
        js_code = """
        async (url) => {
            const response = await fetch(url);
            const blob = await response.blob();
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onloadend = () => resolve(reader.result.split(',')[1]);
                reader.onerror = reject;
                reader.readAsDataURL(blob);
            });
        }
        """
        base64_data = page.evaluate(js_code, url)
        file_data = base64.b64decode(base64_data)
        with open(output_path, "wb") as f:
            f.write(file_data)
        return True
    except Exception as e:
        print(f"Error downloading file in browser: {e}")
        return False

def download_video_ytdlp(url, output_path, cookies_path=None):
    # Sử dụng yt-dlp để tải video từ X/Instagram
    try:
        # Đường dẫn tới python.exe trong môi trường ảo hiện tại
        python_exe = sys.executable
        # Lệnh chạy module yt_dlp
        cmd = [python_exe, "-m", "yt_dlp", url, "-o", output_path, "--format", "mp4/best", "--no-warnings"]
        if cookies_path and os.path.exists(cookies_path):
            cmd += ["--cookies", cookies_path]
            
        # Nếu chạy trên Windows, ẩn cửa sổ Console
        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NO_WINDOW
            
        print(f"Đang chạy yt-dlp: {' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creation_flags, timeout=120)
        
        if result.returncode == 0 and os.path.exists(output_path):
            return True
        else:
            # yt-dlp có thể lưu thành output_path.mp4 nếu không chỉ định đuôi file đúng, hãy kiểm tra
            ext_path = output_path + ".mp4"
            if os.path.exists(ext_path):
                os.rename(ext_path, output_path)
                return True
                
            err_str = result.stderr.decode('utf-8', errors='ignore')
            print(f"yt-dlp error output: {err_str}")
            return False
    except Exception as e:
        print(f"Lỗi khi chạy yt-dlp: {e}")
        return False

def download_media_file(page, media_url, output_path, media_type="image", post_url=None):
    """
    Hàm tải media tổng quát. Hỗ trợ tải ảnh và video từ Instagram/X.
    """
    profile_name = "System"
    p_log(profile_name, f"Bắt đầu tải xuống file ({media_type}) về {output_path}...")
    
    # Xuất cookie trình duyệt ra file tạm cho yt-dlp sử dụng
    cookies_path = None
    if media_type == "video" and page:
        try:
            cookies_path = os.path.abspath("scratch/cookies.txt")
            os.makedirs("scratch", exist_ok=True)
            cookies = page.context.cookies()
            with open(cookies_path, 'w', encoding='utf-8') as f:
                f.write("# Netscape HTTP Cookie File\n")
                for c in cookies:
                    domain = c['domain']
                    include_sub = "TRUE" if domain.startswith(".") else "FALSE"
                    path = c['path']
                    secure = "TRUE" if c['secure'] else "FALSE"
                    expires = str(int(c.get('expires', time.time() + 3600 * 24 * 30)))
                    name = c['name']
                    value = c['value']
                    f.write(f"{domain}\t{include_sub}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")
        except Exception as ce:
            p_log(profile_name, f"Không thể xuất file cookie cho yt-dlp: {ce}")
            cookies_path = None

    # 0. Hỗ trợ bài viết nhiều ảnh (Carousel / Multi-Image)
    if media_type == "multi_image" or isinstance(media_url, list):
        urls = media_url if isinstance(media_url, list) else [media_url]
        downloaded_paths = []
        base_no_ext, ext = os.path.splitext(output_path)
        for idx, u in enumerate(urls):
            cur_path = f"{base_no_ext}_{idx+1}{ext}"
            p_log(profile_name, f"Đang tải ảnh {idx+1}/{len(urls)} của bài viết Carousel/Nhiều ảnh...")
            if download_file_direct(u, cur_path) or (page and download_file_in_browser(page, u, cur_path)):
                downloaded_paths.append(cur_path)
        if downloaded_paths:
            p_log(profile_name, f"✅ Đã tải thành công {len(downloaded_paths)}/{len(urls)} ảnh từ bài viết nhiều ảnh.")
            return downloaded_paths
        return False

    # 1. Nếu là video trên X (hoặc video Instagram mà không có link trực tiếp) -> dùng yt-dlp
    if media_type == "video" and post_url:
        is_x_post = "x.com" in post_url or "twitter.com" in post_url
        if is_x_post:
            p_log(profile_name, "Sử dụng yt-dlp để tải video từ Twitter/X...")
            success = download_video_ytdlp(post_url, output_path, cookies_path)
            if cookies_path and os.path.exists(cookies_path):
                try: os.remove(cookies_path)
                except: pass
            if success:
                p_log(profile_name, "Tải video bằng yt-dlp thành công.")
                return True
            p_log(profile_name, "Tải video bằng yt-dlp thất bại. Thử tải trực tiếp...")
            
    # 2. Thử tải trực tiếp
    if media_url:
        # Chuẩn hóa link
        if media_url.startswith("blob:"):
            # Đối với link blob, phải tải qua trình duyệt
            p_log(profile_name, "Tải tệp dạng blob qua trình duyệt...")
            if download_file_in_browser(page, media_url, output_path):
                if cookies_path and os.path.exists(cookies_path):
                    try: os.remove(cookies_path)
                    except: pass
                return True
            
        p_log(profile_name, "Thử tải trực tiếp qua urllib...")
        if download_file_direct(media_url, output_path):
            if cookies_path and os.path.exists(cookies_path):
                try: os.remove(cookies_path)
                except: pass
            return True
            
        p_log(profile_name, "Tải trực tiếp thất bại. Thử tải qua fetch của trình duyệt...")
        if download_file_in_browser(page, media_url, output_path):
            if cookies_path and os.path.exists(cookies_path):
                try: os.remove(cookies_path)
                except: pass
            return True
            
    # 3. Dự phòng cuối cùng cho video Instagram/Threads: Thử dùng yt-dlp trên post_url
    if media_type == "video" and post_url:
        p_log(profile_name, "Thử tải video Instagram/Threads qua yt-dlp bằng cookie...")
        success = download_video_ytdlp(post_url, output_path, cookies_path)
        if cookies_path and os.path.exists(cookies_path):
            try: os.remove(cookies_path)
            except: pass
        if success:
            return True
            
    if cookies_path and os.path.exists(cookies_path):
        try: os.remove(cookies_path)
        except: pass
    return False

def scrape_threads_profile(page, profile_url, num_posts=3, profile_name="System"):
    """
    Truy cập vào trang cá nhân Threads và lấy danh sách các bài viết gần nhất.
    """
    p_log(profile_name, f"Đang truy cập trang cá nhân Threads: {profile_url}")
    
    try:
        page.goto(profile_url, timeout=60000)
        page.wait_for_timeout(5000)
        
        # Đóng popup bằng nhấn Escape
        for _ in range(2):
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            
        # Đợi các liên kết bài viết Threads xuất hiện (Threads dùng /post/)
        try:
            page.wait_for_selector('a[href*="/post/"]', timeout=15000)
        except Exception:
            p_log(profile_name, "Không tìm thấy bài viết nào trên trang cá nhân Threads.")
            # Chụp ảnh debug
            os.makedirs("scratch", exist_ok=True)
            page.screenshot(path=f"scratch/threads_profile_error.png")
            return []
            
        posts = []
        seen_ids = set()
        
        for scroll_attempt in range(4):
            links = page.locator('a[href*="/post/"]').all()
            for link in links:
                if len(posts) >= num_posts:
                    break
                try:
                    href = link.get_attribute("href")
                    if not href:
                        continue
                    if href.startswith("/"):
                        full_url = f"https://www.threads.net{href}"
                    else:
                        full_url = href
                        
                    match = re.search(r'/post/([A-Za-z0-9_-]+)', full_url)
                    if match:
                        shortcode = match.group(1)
                        if shortcode not in seen_ids:
                            seen_ids.add(shortcode)
                            posts.append({
                                "id": shortcode,
                                "url": full_url
                            })
                except Exception:
                    pass
            if len(posts) >= num_posts:
                break
            page.evaluate("window.scrollBy(0, 1000)")
            page.wait_for_timeout(2000)
                
        p_log(profile_name, f"Quét được {len(posts)} bài viết gần nhất từ Threads.")
        return posts
    except Exception as e:
        p_log(profile_name, f"Lỗi quét Threads profile: {e}")
        return []

def scrape_threads_post(page, post_url, profile_name="System"):
    """
    Truy cập trang chi tiết bài viết Threads để lấy caption và media URL.
    """
    p_log(profile_name, f"Đang cào chi tiết bài viết Threads: {post_url}")
    
    try:
        page.goto(post_url, timeout=60000)
        page.wait_for_timeout(4000)
        
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        
        # 1. Lấy Caption - Thử nhiều phương pháp
        caption = ""
        
        # Phương pháp 1: page title regex
        try:
            title = page.title()
            match = re.search(r'on Threads:\s*"(.+?)"', title, re.DOTALL)
            if match:
                t = match.group(1).strip()
                if len(t) > 5:
                    caption = t
        except Exception:
            pass
        
        # Phương pháp 2: Các selector text của Threads
        if not caption:
            for sel in [
                'div[data-pressable-container] span[dir="auto"]',
                'span[dir="auto"]:not([class*="username"])',
                'div[class*="text"] span',
                'div[class*="content"] span',
                'p[dir="auto"]',
            ]:
                try:
                    locs = page.locator(sel).all()
                    best = ""
                    for loc in locs:
                        try:
                            t = loc.inner_text().strip()
                            if t and len(t) > len(best) and len(t) > 10:
                                best = t
                        except:
                            pass
                    if best and len(best) > 10:
                        caption = best
                        break
                except Exception:
                    pass
        
        # Phương pháp 3: meta og:description
        if not caption:
            try:
                meta = page.locator('meta[property="og:description"], meta[name="description"]').first
                if meta.count() > 0:
                    content = meta.get_attribute("content") or ""
                    if content and len(content) > 5:
                        caption = content.strip()
            except Exception:
                pass
        
        p_log(profile_name, f"Caption Threads (do dai {len(caption)}): '{caption[:120]}'")
        
        # 2. Lấy Media
        media_type = "image"
        media_url = ""
        
        # Kiểm tra video trước
        try:
            video_loc = page.locator('video').first
            if video_loc.count() > 0:
                media_type = "video"
                
                # Click nhẹ để kích hoạt video load src
                try:
                    video_loc.click()
                    page.wait_for_timeout(2000)
                except:
                    pass
                    
                media_url = video_loc.get_attribute("src")
                if not media_url:
                    source_loc = video_loc.locator('source').first
                    if source_loc.count() > 0:
                        media_url = source_loc.get_attribute("src")
                        
                p_log(profile_name, f"Phát hiện bài viết Threads dạng Video. URL: {media_url[:80] if media_url else 'None'}")
        except Exception:
            pass
            
        # Nếu không có video, quét ảnh
        if not media_url:
            try:
                img_locs = page.locator('img').all()
                for img in img_locs:
                    src = img.get_attribute("src")
                    alt = img.get_attribute("alt") or ""
                    if src and src.startswith("http"):
                        if any(x in alt.lower() for x in ["profile picture", "profile photo", "ảnh đại diện", "avatar"]):
                            continue
                        try:
                            box = img.bounding_box()
                            if box and (box['width'] < 150 or box['height'] < 150):
                                continue
                            nat_w = img.evaluate('el => el.naturalWidth')
                            if nat_w > 0 and nat_w < 150:
                                continue
                        except:
                            pass
                        media_url = src
                        media_type = "image"
                        p_log(profile_name, "Phát hiện bài viết Threads dạng Ảnh.")
                        break
            except Exception:
                pass
                
        return {
            "caption": caption,
            "media_type": media_type,
            "media_url": media_url
        }
    except Exception as e:
        p_log(profile_name, f"Lỗi cào chi tiết bài Threads: {e}")
        return None
