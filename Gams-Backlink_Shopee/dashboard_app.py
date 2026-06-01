#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
import queue
import json
import threading
from pathlib import Path
from flask import Flask, render_template, jsonify, Response, request

# Add parent dir to path just in case
sys.path.insert(0, str(Path(__file__).parent))
import backlink_tool as bt

app = Flask(__name__)

# State variables
current_state = "IDLE"  # IDLE, RUNNING, BROWSER_OPEN
scraper_thread = None
browser_thread = None
login_driver = None
browser_should_close = False

# Thread-safe log queue
log_queue = queue.Queue()

# Thread-safe totals tracking
bt.total_urls_count = 0

def push_dashboard_log(msg, prefix_type="INFO"):
    log_queue.put({
        "msg": msg,
        "type": prefix_type
    })

# Register callback in backlink_tool
bt.dashboard_callback = push_dashboard_log

# Serve dashboard index page
@app.route("/")
def index():
    return render_template("index.html")

# Get status JSON
@app.route("/api/status")
def status():
    # If stats have not been initialized, read input count to show total links
    total = bt.total_urls_count
    if total == 0:
        try:
            input_path = bt.BASE_DIR / bt.INPUT_FILE
            if input_path.exists():
                all_urls = bt.load_input_urls(input_path)
                bt.total_urls_count = len(all_urls)
                total = bt.total_urls_count
        except Exception:
            pass

    return jsonify({
        "status": current_state,
        "stats": {
            "total": total,
            "success": bt.stats["success"],
            "failed": bt.stats["failed"],
            "skipped": bt.stats["skipped"],
            "phase1_total": bt.stats.get("phase1_total", 0),
            "phase1_done": bt.stats.get("phase1_done", 0),
            "phase2_total": bt.stats.get("phase2_total", 0),
            "phase2_done": bt.stats.get("phase2_done", 0),
        }
    })

# Start scraping process
def run_scraper_thread():
    global current_state
    try:
        current_state = "RUNNING"
        push_dashboard_log("Kích hoạt tiến trình quét Shopee...", "INFO")
        bt.should_stop = False
        bt.main()
    except Exception as e:
        push_dashboard_log(f"Tiến trình quét bị lỗi: {e}", "ERROR")
    finally:
        current_state = "IDLE"
        push_dashboard_log("Tiến trình quét đã kết thúc.", "INFO")

@app.route("/api/start", methods=["POST"])
def start_scraper():
    global current_state, scraper_thread
    if current_state != "IDLE":
        return jsonify({"status": "error", "message": f"Hệ thống đang bận: Trạng thái {current_state}"})
    
    # Reset stats
    with bt.stats_lock:
        bt.stats["success"] = 0
        bt.stats["failed"] = 0
        bt.stats["skipped"] = 0
    
    scraper_thread = threading.Thread(target=run_scraper_thread, daemon=True)
    scraper_thread.start()
    return jsonify({"status": "success"})

# Stop scraping process
@app.route("/api/stop", methods=["POST"])
def stop_scraper():
    global current_state
    if current_state != "RUNNING":
        return jsonify({"status": "error", "message": "Không có tiến trình nào đang chạy"})
    
    bt.should_stop = True
    push_dashboard_log("Đang yêu cầu dừng tiến trình... Vui lòng đợi trong giây lát.", "WARN")
    return jsonify({"status": "success"})

# Open browser for login
def run_browser_thread():
    global current_state, login_driver, browser_should_close
    try:
        browser_should_close = False
        current_state = "BROWSER_OPEN"
        profile_path = bt.PROFILE_DIR / "shopee_profile"
        profile_path.mkdir(parents=True, exist_ok=True)
        bt.clear_profile_locks(profile_path)

        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        opts = Options()
        opts.add_argument(f"--user-data-dir={profile_path.resolve()}")
        opts.add_argument("--profile-directory=Default")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument("--window-size=1280,800")
        opts.add_argument("--disable-notifications")
        
        push_dashboard_log("Khởi động Chrome Driver cho Đăng Nhập...", "INFO")
        login_driver = webdriver.Chrome(options=opts)
        login_driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"}
        )
        
        push_dashboard_log("Điều hướng tới Shopee.vn...", "INFO")
        login_driver.get("https://shopee.vn")
        push_dashboard_log("Chrome đã mở. Hãy đăng nhập tài khoản trên màn hình Chrome.", "WARN")

        # Lưu cookies theo thời gian thực (real-time) mỗi 2 giây khi trình duyệt đang mở
        while not browser_should_close:
            try:
                _ = login_driver.window_handles
                
                # Tự động trích xuất và cập nhật cookies sang file json trong lúc trình duyệt đang mở
                try:
                    cookies = login_driver.get_cookies()
                    cookies_path = bt.PROFILE_DIR / "cookies.json"
                    bt.PROFILE_DIR.mkdir(parents=True, exist_ok=True)
                    with open(cookies_path, "w", encoding="utf-8") as f:
                        json.dump(cookies, f, indent=4)
                except Exception:
                    pass
                    
                time.sleep(2)
            except Exception:
                # Closed manually (người dùng bấm X tắt trình duyệt)
                break
    except Exception as e:
        push_dashboard_log(f"Lỗi khi chạy Chrome: {e}", "ERROR")
    finally:
        if login_driver:
            # Lưu lần cuối (chỉ thực hiện nếu WebDriver vẫn hoạt động)
            try:
                cookies = login_driver.get_cookies()
                cookies_path = bt.PROFILE_DIR / "cookies.json"
                bt.PROFILE_DIR.mkdir(parents=True, exist_ok=True)
                with open(cookies_path, "w", encoding="utf-8") as f:
                    json.dump(cookies, f, indent=4)
            except Exception:
                pass
                
            try:
                login_driver.quit()
            except Exception:
                pass
            login_driver = None
            
        current_state = "IDLE"
        
        # Xác minh file cookies.json xem đã lưu thành công hay chưa
        cookies_path = bt.PROFILE_DIR / "cookies.json"
        if cookies_path.exists() and cookies_path.stat().st_size > 10:
            push_dashboard_log("Đã lưu Cookies đăng nhập thành công!", "SUCCESS")
        else:
            push_dashboard_log("Không tìm thấy file cookies đăng nhập. Vui lòng đăng nhập lại.", "ERROR")
            
        push_dashboard_log("Trình duyệt đăng nhập đã đóng.", "INFO")

@app.route("/api/open-browser", methods=["POST"])
def open_browser():
    global current_state, browser_thread
    if current_state != "IDLE":
        return jsonify({"status": "error", "message": f"Hệ thống đang bận: Trạng thái {current_state}"})
    
    browser_thread = threading.Thread(target=run_browser_thread, daemon=True)
    browser_thread.start()
    return jsonify({"status": "success"})

# Complete browser session and save cookies
@app.route("/api/save-login", methods=["POST"])
def save_login():
    global login_driver, current_state, browser_should_close
    if current_state != "BROWSER_OPEN" or not login_driver:
        return jsonify({"status": "error", "message": "Trình duyệt đăng nhập chưa mở"})
    
    try:
        browser_should_close = True
        # Wait up to 5 seconds for the background thread to safely close and cleanup the driver
        for _ in range(25):
            if not login_driver:
                break
            time.sleep(0.2)
            
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# Open input file Link_shopee.txt in default editor
@app.route("/api/open-input", methods=["POST"])
def open_input():
    try:
        file_path = bt.BASE_DIR / bt.INPUT_FILE
        if file_path.exists():
            os.startfile(file_path.resolve())
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": f"Không tìm thấy file: {bt.INPUT_FILE}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# Open output file ket_qua.txt in default editor
@app.route("/api/open-output", methods=["POST"])
def open_output():
    try:
        file_path = bt.BASE_DIR / bt.OUTPUT_FILE
        if not file_path.exists():
            # Create file if it doesn't exist so the user can open it
            file_path.touch()
        os.startfile(file_path.resolve())
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# API to get current config
@app.route("/api/settings", methods=["GET"])
def get_settings():
    bt.load_config()
    return jsonify({
        "status": "success",
        "config": {
            "NUM_THREADS": bt.NUM_THREADS,
            "USE_CHROME_ONLY": bt.USE_CHROME_ONLY,
            "HEADLESS": bt.HEADLESS
        }
    })

# API to save new config
@app.route("/api/settings", methods=["POST"])
def save_settings():
    try:
        data = request.get_json() or {}
        num_threads = int(data.get("NUM_THREADS", 3))
        headless = bool(data.get("HEADLESS", False))
        use_chrome_only = bool(data.get("USE_CHROME_ONLY", True))
        
        if num_threads < 1:
            num_threads = 1
        elif num_threads > 10:
            num_threads = 10
            
        config_path = bt.BASE_DIR / "config.json"
        config_data = {
            "NUM_THREADS": num_threads,
            "HEADLESS": headless,
            "USE_CHROME_ONLY": use_chrome_only
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
            
        bt.NUM_THREADS = num_threads
        bt.HEADLESS = headless
        bt.USE_CHROME_ONLY = use_chrome_only
        
        push_dashboard_log(f"Cập nhật cấu hình: {num_threads} Threads, ChromeOnly={use_chrome_only}, Headless={headless}", "SUCCESS")
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# SSE endpoint to stream logs to browser
@app.route("/api/logs")
def logs_stream():
    def event_stream():
        # Clean queue before starting to avoid spamming old logs
        while not log_queue.empty():
            try:
                log_queue.get_nowait()
            except queue.Empty:
                break
                
        while True:
            try:
                # Non-blocking read with timeout to keep thread responsive to connection drops
                log_item = log_queue.get(timeout=3.0)
                yield f"data: {json.dumps(log_item)}\n\n"
            except queue.Empty:
                # Keep-alive ping
                yield ": ping\n\n"
            except Exception:
                break
                
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == "__main__":
    import socket
    # Try to find a free port, default to 5000
    port = 5000
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
    except socket.error:
        # Port is in use, find another one
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    finally:
        s.close()
        
    print(f"====================================================")
    print(f" Khoi chay Web Dashboard tai: http://127.0.0.1:{port}")
    print(f"====================================================")
    
    # Auto open dashboard URL in user browser
    import webbrowser
    threading.Timer(1.5, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
    
    # Run flask app
    app.run(host="127.0.0.1", port=port, debug=False)
