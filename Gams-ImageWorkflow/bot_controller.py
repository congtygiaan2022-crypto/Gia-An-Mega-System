import os
import json
import threading
import subprocess
import sys
import time
import random
from datetime import datetime
import psutil
import db_manager

class BotController:
    def __init__(self):
        self.lock = threading.Lock()
        
        # State: profile_name -> state_dict
        # state_dict keys: 
        #   status: 'STOPPED', 'WAITING_FOR_SLOT', 'RUNNING', 'DELAYING', 'ERROR'
        #   process: Popen object (if RUNNING)
        #   next_run_time: timestamp (if DELAYING)
        #   current_loop: int
        self.profiles_state = {}
        
        # Tự động sinh thời gian đếm ngược ngẫu nhiên cho mỗi active profile khi khởi động
        try:
            self._init_startup_delays()
        except Exception as e:
            print("Lỗi khi tạo delay khởi động:", e)
            
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()

    def _init_startup_delays(self):
        config = self._load_config()
        threads = config.get("threads", 2)
        profiles = config.get("profiles", [f"Profile_{i+1}" for i in range(threads)])
        
        global_cfg = db_manager.get_global_config()
        try:
            min_s = int(global_cfg.get("delay_rand_ind_min", 3600))
            max_s = int(global_cfg.get("delay_rand_ind_max", 7200))
        except Exception:
            min_s = 3600
            max_s = 7200

        for p in profiles:
            profiles_cfg = db_manager.get_profile_config(p)
            if profiles_cfg.get('is_active') is False:
                continue
                
            # Kiểm tra cấu hình tối thiểu để tránh lỗi khi tự chạy
            missing = []
            if not profiles_cfg.get("status_base", "").strip(): missing.append("Status mẫu")
            if not profiles_cfg.get("prompt_base", "").strip(): missing.append("Prompt viết status")
            if not profiles_cfg.get("output_txt_dir", "").strip(): missing.append("Thư mục lưu Text")
            if not profiles_cfg.get("input_img_dir", "").strip(): missing.append("Thư mục ảnh mẫu")
            if not profiles_cfg.get("prompt_img", "").strip(): missing.append("Prompt tạo ảnh")
            if not profiles_cfg.get("output_img_dir", "").strip(): missing.append("Thư mục lưu Ảnh")
            if not profiles_cfg.get("fanpage_url", "").strip(): missing.append("Link Fanpage")
            
            if missing:
                self.profiles_state[p] = {
                    "status": "ERROR",
                    "process": None,
                    "next_run_time": 0,
                    "current_loop": 1,
                    "error_detail": f"Thiếu cấu hình: {', '.join(missing)}"
                }
                db_manager.set_status(p, f"Missing: {', '.join(missing)}")
                continue

            # Sinh thời gian random ngẫu nhiên riêng lẻ cho mỗi profile
            d = random.randint(min_s, max_s) if max_s >= min_s else 0
            self.profiles_state[p] = {
                "status": "DELAYING",
                "process": None,
                "next_run_time": time.time() + d,
                "current_loop": 1,
                "error_detail": ""
            }
            db_manager.init_profile_log(p)
            db_manager.log_msg(p, f"[{p}] Tự động kích hoạt khi bật Server. Thời gian chờ ngẫu nhiên vòng đầu: {d} giây.")

    def _load_config(self):
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def get_status(self):
        config = self._load_config()
        threads = config.get("threads", 2)
        profiles = config.get("profiles", [f"Profile_{i+1}" for i in range(threads)])
        
        # Lấy log từ DB, nhưng status sẽ ưu tiên từ RAM của controller
        db_data = db_manager.get_all_status(profiles)
        
        with self.lock:
            for p in profiles:
                state = self.profiles_state.get(p)
                if not state:
                    db_data[p]["status"] = "Idle"
                else:
                    st = state["status"]
                    if st == "DELAYING":
                        rem = int(state["next_run_time"] - time.time())
                        if rem < 0: rem = 0
                        m, s = divmod(rem, 60)
                        h, m = divmod(m, 60)
                        detail = state.get("error_detail", "")
                        if "Hết hạn GPT" in detail or "hết hạn GPT" in detail:
                            db_data[p]["status"] = f"Chờ thử lại (Hết hạn GPT) (Wait: {h:02d}:{m:02d}:{s:02d})"
                        else:
                            db_data[p]["status"] = f"Wait: {h:02d}:{m:02d}:{s:02d}"
                    elif st == "WAITING_FOR_SLOT":
                        db_data[p]["status"] = "Waiting"
                    elif st == "RUNNING":
                        db_data[p]["status"] = "Running"
                    elif st == "ERROR":
                        detail = state.get("error_detail", "")
                        db_data[p]["status"] = f"❌ Lỗi: {detail}" if detail else "❌ Lỗi"
                    else:
                        db_data[p]["status"] = "Idle"
        return db_data

    def start_profile(self, profile_name, profile_cfg, global_cfg):
        with self.lock:
            state = self.profiles_state.get(profile_name)
            # Chỉ chặn nếu profile đang chạy hoặc đang nằm trong hàng đợi chạy
            if state and state["status"] in ["RUNNING", "WAITING_FOR_SLOT"]:
                return False, "Profile is already active"
                
            db_manager.init_profile_log(profile_name)
            self.profiles_state[profile_name] = {
                "status": "WAITING_FOR_SLOT",
                "process": None,
                "next_run_time": 0,
                "current_loop": 1,
                "error_detail": ""
            }
            return True, f"Queued {profile_name}"

    def stop_profile(self, profile_name):
        with self.lock:
            state = self.profiles_state.get(profile_name)
            if not state:
                return False, "Profile not active"
                
            if state["status"] == "RUNNING" and state["process"]:
                self._kill_process(state["process"])
                db_manager.log_msg(profile_name, f"[{profile_name}] Đã đóng cưỡng bức.")
                
            state["status"] = "STOPPED"
            state["process"] = None
            return True, f"Stopped {profile_name}"

    def force_stop_all(self):
        count = 0
        with self.lock:
            for p, state in self.profiles_state.items():
                if state["status"] != "STOPPED":
                    if state["status"] == "RUNNING" and state["process"]:
                        self._kill_process(state["process"])
                        db_manager.log_msg(p, f"[{p}] Đã dập tắt khẩn cấp.")
                    state["status"] = "STOPPED"
                    state["process"] = None
                    count += 1
        return True, f"Forced stop {count} profiles."

    def _kill_process(self, proc):
        try:
            parent = psutil.Process(proc.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
        except:
            proc.terminate()

    def _scheduler_loop(self):
        while self.scheduler_running:
            time.sleep(1)
            global_cfg = db_manager.get_global_config()
            try:
                max_threads = int(global_cfg.get("max_threads", 3))
            except:
                max_threads = 3
                
            loop_type = global_cfg.get("loop_type", "1")
            try:
                loop_count = int(global_cfg.get("loop_count", 1))
            except:
                loop_count = 1
                
            delay_type = global_cfg.get("delay_type", "fixed")

            with self.lock:
                # 1. Update status of running processes
                active_count = 0
                for p, state in self.profiles_state.items():
                    if state["status"] == "RUNNING":
                        proc = state["process"]
                        if proc and proc.poll() is not None:
                            # Finished
                            ret_code = proc.poll()
                            state["process"] = None
                            
                            # Nếu ret_code == 1 -> Lỗi nặng (Missing config / Empty images), dừng profile
                            if ret_code == 1:
                                state["status"] = "ERROR"
                                # Đọc log gần nhất từ DB để hiển lý do lỗi rõ hơn
                                try:
                                    db_log = db_manager.get_all_status([p])
                                    last_status = db_log.get(p, {}).get("status", "")
                                    state["error_detail"] = last_status or "Worker exited with error (code 1)"
                                except:
                                    state["error_detail"] = "Worker exited with error (code 1)"
                                continue
                                
                            # Nếu ret_code == 2 -> Policy violation, chạy lại loop hiện tại
                            if ret_code == 2:
                                state["status"] = "DELAYING"
                                state["next_run_time"] = time.time() + 10 # Nghỉ tạm 10s rồi chạy lại
                                continue
                                
                            # Nếu ret_code == 3 -> Hết hạn hạn mức GPT, nghỉ theo delay cấu hình rồi thử lại loop hiện tại
                            if ret_code == 3:
                                state["status"] = "DELAYING"
                                state["error_detail"] = "Chờ thử lại (Hết hạn GPT)"
                                
                                # Tính delay theo cấu hình của người dùng (không đổi loop count)
                                if delay_type == "fixed":
                                    d = int(global_cfg.get("delay_fixed", 0))
                                    state["next_run_time"] = time.time() + d
                                elif delay_type == "random_individual":
                                    min_s = int(global_cfg.get("delay_rand_ind_min", 0))
                                    max_s = int(global_cfg.get("delay_rand_ind_max", 0))
                                    d = random.randint(min_s, max_s) if max_s >= min_s else 0
                                    state["next_run_time"] = time.time() + d
                                elif delay_type == "random_all":
                                    min_s = int(global_cfg.get("delay_rand_all_min", 0))
                                    max_s = int(global_cfg.get("delay_rand_all_max", 0))
                                    d = random.randint(min_s, max_s) if max_s >= min_s else 0
                                    state["next_run_time"] = time.time() + d
                                else:
                                    state["next_run_time"] = time.time() + 300 # Mặc định 5 phút
                                continue

                            # Thành công, tiến tới loop tiếp theo
                            state["current_loop"] += 1
                            if loop_type == "1" and state["current_loop"] > 1:
                                state["status"] = "STOPPED"
                            elif loop_type == "n" and state["current_loop"] > loop_count:
                                state["status"] = "STOPPED"
                            else:
                                state["status"] = "DELAYING"
                                # Tính delay riêng lẻ nếu không phải random_all
                                if delay_type == "fixed":
                                    d = int(global_cfg.get("delay_fixed", 0))
                                    state["next_run_time"] = time.time() + d
                                elif delay_type == "random_individual":
                                    min_s = int(global_cfg.get("delay_rand_ind_min", 0))
                                    max_s = int(global_cfg.get("delay_rand_ind_max", 0))
                                    d = random.randint(min_s, max_s) if max_s >= min_s else 0
                                    state["next_run_time"] = time.time() + d
                                elif delay_type == "random_all":
                                    # Sẽ được tính sau khi tất cả hoàn thành
                                    state["next_run_time"] = 0
                                elif delay_type == "time":
                                    state["next_run_time"] = -1 # Đặc biệt: -1 nghĩa là đang đợi giờ cụ thể
                                    state["target_times"] = global_cfg.get("delay_times", [])
                        else:
                            active_count += 1
                
                # 2. Xử lý "Random All" - Đợi tất cả xong thì mới bắt đầu đếm giờ cùng lúc
                if delay_type == "random_all":
                    # Kiểm tra xem có ai đang chạy không
                    any_running = any(s["status"] == "RUNNING" for s in self.profiles_state.values())
                    if not any_running:
                        # Tất cả đều đã xong, kiểm tra những ai đang đợi random_all (next_run_time == 0)
                        waiting_sync = [p for p, s in self.profiles_state.items() if s["status"] == "DELAYING" and s["next_run_time"] == 0]
                        if waiting_sync:
                            min_s = int(global_cfg.get("delay_rand_all_min", 0))
                            max_s = int(global_cfg.get("delay_rand_all_max", 0))
                            d = random.randint(min_s, max_s) if max_s >= min_s else 0
                            sync_time = time.time() + d
                            for p in waiting_sync:
                                self.profiles_state[p]["next_run_time"] = sync_time

                # 3. Chuyển từ DELAYING sang WAITING_FOR_SLOT nếu hết giờ
                now_str = datetime.now().strftime("%H:%M")
                for p, state in self.profiles_state.items():
                    if state["status"] == "DELAYING":
                        if state["next_run_time"] > 0 and time.time() >= state["next_run_time"]:
                            state["status"] = "WAITING_FOR_SLOT"
                            state["next_run_time"] = 0
                        elif state["next_run_time"] == -1: # Chế độ hẹn giờ
                            if now_str in state.get("target_times", []) and now_str != state.get("last_time_str"):
                                state["status"] = "WAITING_FOR_SLOT"
                                state["next_run_time"] = 0
                                state["last_time_str"] = now_str
                                db_manager.log_msg(p, f"[{p}] Đã đến giờ: {now_str}. Bắt đầu chạy!")

                # 4. Pop từ hàng đợi WAITING_FOR_SLOT lên RUNNING nếu còn slot
                for p, state in self.profiles_state.items():
                    if active_count >= max_threads:
                        break
                    if state["status"] == "WAITING_FOR_SLOT":
                        state["status"] = "RUNNING"
                        state["error_detail"] = "" # Clear error detail when starting run
                        active_count += 1
                        
                        proc = subprocess.Popen(
                            [sys.executable, "worker_process.py", p, str(state["current_loop"])],
                            cwd=os.getcwd(),
                            creationflags=subprocess.CREATE_NEW_CONSOLE
                        )
                        state["process"] = proc

# Removed _calc_next_time

bot_controller_instance = BotController()
