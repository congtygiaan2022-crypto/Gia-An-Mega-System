import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from flask import Flask, render_template, jsonify, request
from bot_controller import bot_controller_instance
import db_manager
import os
import logging

import json

app = Flask(__name__)

# (Bật lại log của Flask để khi bấm nút có lỗi sẽ hiện rõ ở màn hình Start.bat)
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

def get_profiles_list():
    config = bot_controller_instance._load_config()
    if "profiles" in config:
        return config["profiles"]
    # Fallback to threads
    threads = config.get("threads", 2)
    return [f"Profile_{i+1}" for i in range(threads)]

@app.route('/')
def index():
    profiles = get_profiles_list()
    return render_template('index.html', profiles=profiles)

@app.route('/api/rename_profile/<old_name>', methods=['POST'])
def rename_profile(old_name):
    new_name = request.json.get('new_name')
    if not new_name or new_name == old_name:
        return jsonify({"success": False, "message": "Tên không hợp lệ"})
    
    config = bot_controller_instance._load_config()
    profiles = get_profiles_list()
    
    if old_name in profiles:
        idx = profiles.index(old_name)
        profiles[idx] = new_name
        config["profiles"] = profiles
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        bot_controller_instance.config = config
    
    # Rename physical directory
    old_path = os.path.join(config.get("profiles_dir", "profiles"), old_name)
    new_path = os.path.join(config.get("profiles_dir", "profiles"), new_name)
    if os.path.exists(old_path):
        try:
            os.rename(old_path, new_path)
        except Exception as e:
            print("Khong the doi ten thu muc profile Chrome:", e)
            
    db_manager.rename_profile(old_name, new_name)
    return jsonify({"success": True})

@app.route('/api/create_profile', methods=['POST'])
def create_profile():
    new_name = request.json.get('profile_name')
    if not new_name:
        return jsonify({"success": False, "message": "Tên không hợp lệ"})
    
    config = bot_controller_instance._load_config()
    profiles = get_profiles_list()
    
    if new_name in profiles:
        return jsonify({"success": False, "message": "Tên Profile đã tồn tại"})
        
    profiles.append(new_name)
    config["profiles"] = profiles
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)
    bot_controller_instance.config = config
    
    # Tạo thư mục vật lý để không bị lỗi khi manual browser
    new_path = os.path.join(config.get("profiles_dir", "profiles"), new_name)
    os.makedirs(new_path, exist_ok=True)
    
    return jsonify({"success": True, "message": "Đã tạo Profile thành công!"})

@app.route('/api/delete_profile/<profile_name>', methods=['POST'])
def delete_profile(profile_name):
    config = bot_controller_instance._load_config()
    profiles = get_profiles_list()
    
    if profile_name in profiles:
        profiles.remove(profile_name)
        config["profiles"] = profiles
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        bot_controller_instance.config = config
        
        # Có thể xóa thư mục vật lý ở đây, nhưng để an toàn thì chỉ xóa trong config.
        # Nếu muốn xóa hẳn: import shutil; shutil.rmtree(path, ignore_errors=True)
        return jsonify({"success": True, "message": "Đã xóa Profile!"})
    
    return jsonify({"success": False, "message": "Không tìm thấy Profile"})

@app.route('/api/status')
def get_status():
    return jsonify(bot_controller_instance.get_status())

@app.route('/api/start/<profile_name>', methods=['POST'])
def start_profile(profile_name):
    profiles_cfg = db_manager.get_profile_config(profile_name)
    if profiles_cfg.get('is_active') is False:
        return jsonify({"success": False, "message": "Profile đang bị vô hiệu hóa (Deactivated). Vui lòng bật lại trong Cài đặt."})
    global_cfg = db_manager.get_global_config()
    success, msg = bot_controller_instance.start_profile(profile_name, profiles_cfg, global_cfg)
    return jsonify({"success": success, "message": msg})

@app.route('/api/stop/<profile_name>', methods=['POST'])
def stop_profile(profile_name):
    success, msg = bot_controller_instance.stop_profile(profile_name)
    return jsonify({"success": success, "message": msg})

@app.route('/api/manual_browser/<profile_name>', methods=['POST'])
def manual_browser(profile_name):
    import subprocess
    import sys
    # Chặn nếu profile đang chạy auto
    state = bot_controller_instance.profiles_state.get(profile_name)
    if state and state.get("status") == "RUNNING":
        return jsonify({"success": False, "message": "Profile đang chạy Auto! Vui lòng STOP Auto trước khi mở thủ công."})
    
    # Mở script manual_browser.py bằng đúng môi trường ảo Python hiện tại
    subprocess.Popen(
        [sys.executable, "manual_browser.py", profile_name],
        cwd=os.getcwd(),
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    return jsonify({"success": True, "message": f"Đang mở trình duyệt thủ công cho {profile_name}..."})

@app.route('/api/global_config', methods=['GET'])
def get_global_cfg():
    return jsonify(db_manager.get_global_config())

@app.route('/api/save_global_config', methods=['POST'])
def save_global_cfg():
    global_cfg = request.json
    db_manager.save_global_config(global_cfg)
    return jsonify({"success": True, "message": "Đã lưu cài đặt toàn hệ thống!"})

@app.route('/api/start_all', methods=['POST'])
def start_all():
    global_cfg = request.json
    db_manager.save_global_config(global_cfg)
    
    profiles = get_profiles_list()
    
    started = []
    skipped = []
    for profile_name in profiles:
        profiles_cfg = db_manager.get_profile_config(profile_name)
        
        # Kiểm tra profile có được kích hoạt không
        if profiles_cfg.get('is_active') is False:
            db_manager.init_profile_log(profile_name)
            db_manager.log_msg(profile_name, f"[{profile_name}] Bỏ qua: Profile đã bị vô hiệu hóa (Deactivated).")
            db_manager.set_status(profile_name, "Deactivated")
            skipped.append(profile_name)
            continue

        # Kiểm tra các trường cấu hình bắt buộc trước khi chạy
        missing = []
        if not profiles_cfg.get("status_base", "").strip(): missing.append("Status mẫu")
        if not profiles_cfg.get("prompt_base", "").strip(): missing.append("Prompt viết status")
        if not profiles_cfg.get("output_txt_dir", "").strip(): missing.append("Thư mục lưu Text")
        if not profiles_cfg.get("input_img_dir", "").strip(): missing.append("Thư mục ảnh mẫu")
        if not profiles_cfg.get("prompt_img", "").strip(): missing.append("Prompt tạo ảnh")
        if not profiles_cfg.get("output_img_dir", "").strip(): missing.append("Thư mục lưu Ảnh")
        if not profiles_cfg.get("fanpage_url", "").strip(): missing.append("Link Fanpage")
        
        if missing:
            db_manager.init_profile_log(profile_name)
            err_msg = f"[{profile_name}] ❌ KHÔNG THỂ CHẠY. Thiếu cấu hình: {', '.join(missing)}. Vui lòng điền đủ trong tab Cài Đặt của profile."
            db_manager.log_msg(profile_name, err_msg)
            db_manager.set_status(profile_name, f"Missing: {', '.join(missing)}")
            skipped.append(profile_name)
            continue
            
        bot_controller_instance.start_profile(profile_name, profiles_cfg, global_cfg)
        started.append(profile_name)
        
    msg = f"Khởi động {len(started)} profile."
    if skipped:
        msg += f" Bỏ qua {len(skipped)} profile (kiểm tra log để biết lý do)."
    return jsonify({"success": True, "message": msg, "started": started, "skipped": skipped})

@app.route('/api/stop_all', methods=['POST'])
def stop_all():
    profiles = get_profiles_list()
    
    stopped = []
    for profile_name in profiles:
        bot_controller_instance.stop_profile(profile_name)
        stopped.append(profile_name)
        
    return jsonify({"success": True, "message": f"Sent stop signal to {len(stopped)} profiles."})

@app.route('/api/force_stop', methods=['POST'])
def force_stop():
    bot_controller_instance.force_stop_all()
    # Tắt server ngay lập tức
    os._exit(0)
    return jsonify({"success": True})

@app.route('/api/restart_tool', methods=['POST'])
def restart_tool():
    # Dừng toàn bộ tiến trình
    bot_controller_instance.force_stop_all()
    # Replace process
    import subprocess
    subprocess.Popen([sys.executable, "app.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
    os._exit(0)
    return jsonify({"success": True})

@app.route('/api/clear_log/<profile_name>', methods=['POST'])
def clear_log(profile_name):
    db_manager.clear_profile_log(profile_name)
    return jsonify({"success": True, "message": f"Đã xóa log cho {profile_name}."})

@app.route('/api/clear_all_logs', methods=['POST'])
def clear_all_logs():
    db_manager.clear_all_profile_logs()
    return jsonify({"success": True, "message": "Đã xóa log của tất cả profile."})

@app.route('/api/profile_config/<profile_name>', methods=['GET'])
def get_profile_config(profile_name):
    cfg = db_manager.get_profile_config(profile_name)
    return jsonify(cfg)

@app.route('/api/profile_config/<profile_name>', methods=['POST'])
def save_profile_config(profile_name):
    data = request.json
    db_manager.save_profile_config(profile_name, data)
    return jsonify({"success": True})

def start_file_watcher():
    import threading
    import time
    import subprocess
    
    def watch():
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        def get_py_files():
            files = []
            for root, dirs, filenames in os.walk(script_dir):
                # Bỏ qua venv, git, gemini, pycache và các thư mục tạm
                if any(x in root for x in ['venv', '__pycache__', '.git', '.gemini', 'output_data', 'input_images']):
                    continue
                for f in filenames:
                    if f.endswith('.py'):
                        files.append(os.path.join(root, f))
            return files

        # Lấy mtime ban đầu
        py_files = get_py_files()
        mtimes = {}
        for f in py_files:
            try:
                mtimes[f] = os.path.getmtime(f)
            except:
                pass
        
        print("[Auto-Reload] File watcher started. Monitoring python files for changes...")
        
        while True:
            time.sleep(1.5)
            try:
                current_files = get_py_files()
                changed = False
                for f in current_files:
                    try:
                        mtime = os.path.getmtime(f)
                    except:
                        continue
                    if f not in mtimes:
                        mtimes[f] = mtime
                        changed = True
                        print(f"[Auto-Reload] Detected new file: {f}")
                        break
                    elif mtimes[f] != mtime:
                        mtimes[f] = mtime
                        changed = True
                        print(f"[Auto-Reload] Detected changes in file: {f}")
                        break
                
                if not changed:
                    for f in list(mtimes.keys()):
                        if f not in current_files:
                            mtimes.pop(f)
                            changed = True
                            print(f"[Auto-Reload] Detected deleted file: {f}")
                            break
                
                if changed:
                    print("[Auto-Reload] Restarting tool server to apply new code...")
                    try:
                        bot_controller_instance.force_stop_all()
                    except Exception as e:
                        print(f"[Auto-Reload] Error stopping profiles: {e}")
                    
                    app_path = os.path.join(script_dir, "app.py")
                    print(f"[Auto-Reload] Spawning: {sys.executable} -u {app_path}")
                    # Chạy lại app.py trong console mới và tắt tiến trình hiện tại
                    subprocess.Popen([sys.executable, "-u", app_path], cwd=script_dir, creationflags=subprocess.CREATE_NEW_CONSOLE)
                    os._exit(0)
            except Exception as e:
                pass

    t = threading.Thread(target=watch, daemon=True)
    t.start()

if __name__ == '__main__':
    # Lưu PID của tiến trình Flask để stop.bat chỉ tắt đúng app này
    with open("app.pid", "w") as f:
        f.write(str(os.getpid()))

    # Khởi động file watcher để tự động restart khi thay đổi file
    start_file_watcher()

    # Disable auto-reload (debug mode false) to avoid multithreading issues
    import time
    for attempt in range(10):
        try:
            app.run(debug=False, port=5000)
            break
        except OSError as e:
            if attempt < 9:
                print(f"[App] Port 5000 is busy (attempt {attempt+1}/10). Retrying in 1s...")
                time.sleep(1.0)
            else:
                raise e
