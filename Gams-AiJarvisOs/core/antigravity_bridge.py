import os
import json
import time
import logging
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.tool_generator import tool_generator

# Cấu hình Logging
bridge_logger = logging.getLogger("JARVIS_BRIDGE")
bridge_logger.setLevel(logging.INFO)
# Avoid double logging if root logger also has handlers
bridge_logger.propagate = False

if not bridge_logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - JARVIS BRIDGE: %(message)s')
    ch.setFormatter(formatter)
    bridge_logger.addHandler(ch)

PATH_TO_REQUESTS = os.path.join(PROJECT_ROOT, "bridge", "requests")
PATH_TO_RESPONSES = os.path.join(PROJECT_ROOT, "bridge", "responses")
HEARTBEAT_FILE = os.path.join(PROJECT_ROOT, "bridge", ".heartbeat")

# Đảm bảo thư mục tồn tại
os.makedirs(PATH_TO_REQUESTS, exist_ok=True)
os.makedirs(PATH_TO_RESPONSES, exist_ok=True)

class AntigravityHandler(FileSystemEventHandler):
    """Xử lý sự kiện khi có file request mới từ UI"""

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            bridge_logger.info(f"📥 Phát hiện yêu cầu mới: {event.src_path}")
            # wait a tiny bit to ensure file is fully written before reading
            time.sleep(0.1)
            self.process_request(event.src_path)

    def process_request(self, file_path):
        try:
            # 1. Đọc nội dung request
            with open(file_path, 'r', encoding='utf-8') as f:
                request_data = json.load(f)
            
            request_id = request_data.get("id", "unknown")
            action = request_data.get("task", "none")
            
            bridge_logger.info(f"🧠 Đang gửi Action '{action}' tới Antigravity Engine...")

            # 2. XỬ LÝ (Gọi LLM hoặc Code Gen)
            result = self.simulate_antigravity_engine(request_data)

            # 3. Ghi phản hồi vào responses/
            response_file = os.path.join(PATH_TO_RESPONSES, f"res_{request_id}.json")
            with open(response_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=4)
            
            bridge_logger.info(f"✅ Đã phản hồi kết quả tại: {response_file}")

            # 4. (Tùy chọn) Xóa file request sau khi xử lý xong
            os.remove(file_path)

        except Exception as e:
            bridge_logger.error(f"❌ Lỗi xử lý Bridge: {str(e)}")

    def _write_selfrepair_log(self, role, plugin, message):
        """Ghi 1 entry vào nhật ký tự sửa lỗi plugin."""
        import datetime
        log_path = os.path.join(PROJECT_ROOT, "logs", "self_repair_chatlog.json")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        logs = []
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            except:
                logs = []
        logs.append({
            "role": role,
            "plugin": plugin,
            "message": message,
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        })
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

    def simulate_antigravity_engine(self, data):
        """Thực hiện xử lý thật bằng AI Code Generator hoặc trả về ping"""
        task_type = data.get("task")
        
        if task_type == "ping" or task_type == "connection_test":
            return {
                "task_id": data.get("id"),
                "status": "success",
                "message": "Antigravity Bridge (Event-Driven) Alive and Watching!",
                "timestamp": time.time()
            }
        
        elif task_type == "simulate_task":
            return {
                "task_id": data.get("id"),
                "status": "success",
                "message": "Simulation successful. Antigravity can handle this task.",
                "dummy_result": "Simulation data 123"
            }
        
        elif task_type == "tool_generation" or task_type == "fix_plugin":
            tool_name = data.get("name", "unknown_tool")
            requirement = data.get("requirement", "")
            
            try:
                bridge_logger.info(f"Generating code for '{tool_name}'...")
                
                if task_type == "fix_plugin":
                    error_trace = data.get("error", "")
                    prompt = f"Fix the following python plugin '{tool_name}' which crashed with the stacktrace:\n{error_trace}\nYour output should overwrite the existing file entirely with the fixed version."
                    
                    # Log sự kiện phát hiện lỗi
                    self._write_selfrepair_log(
                        role="plugin",
                        plugin=tool_name,
                        message=f"⚠️ Plugin báo lỗi:\n```\n{error_trace}\n```"
                    )
                    self._write_selfrepair_log(
                        role="system",
                        plugin=tool_name,
                        message=f"🔍 Đang phân tích lỗi và gọi AI Engine sửa plugin `{tool_name}`..."
                    )
                    
                    # SAFEGUARD: Do NOT overwrite existing plugins directly.
                    # Instead, generate a proposed fix and save as _proposed_fix.py
                    plugin_dir = os.path.join(PROJECT_ROOT, "plugins")
                    existing_plugin_path = os.path.join(plugin_dir, f"{tool_name}.py")
                    proposed_path = os.path.join(plugin_dir, f"{tool_name}_proposed_fix.py")
                    
                    if os.path.exists(existing_plugin_path):
                        # Backup the real file is safe, generate fix as "proposed"
                        bridge_logger.info(f"Plugin exists. Generating proposed fix only (not overwriting).")
                        try:
                            temp_name = f"{tool_name}__fix_proposal"
                            tool_generator.create_tool(temp_name, prompt)
                            # Rename the generated file to proposed fix
                            generated = os.path.join(plugin_dir, f"{temp_name}.py")
                            if os.path.exists(generated):
                                import shutil
                                shutil.move(generated, proposed_path)
                                bridge_logger.info(f"Saved proposed fix at: {proposed_path}")
                        except Exception as proposal_err:
                            bridge_logger.warning(f"Could not generate proposed fix: {proposal_err}")
                    else:
                        # Plugin does not exist yet, safe to create
                        tool_generator.create_tool(tool_name, prompt)
                    
                    # Log kết quả sau khi sửa
                    self._write_selfrepair_log(
                        role="ai",
                        plugin=tool_name,
                        message=f"✅ Đã phân tích lỗi và tạo lại code cho plugin `{tool_name}`. Vui lòng kiểm tra và khởi động lại tác vụ."
                    )
                else:
                    self._write_selfrepair_log(
                        role="system",
                        plugin=tool_name,
                        message=f"🛠️ Đang tạo mới plugin `{tool_name}` theo yêu cầu: {requirement}"
                    )
                    tool_generator.create_tool(tool_name, requirement)
                    self._write_selfrepair_log(
                        role="ai",
                        plugin=tool_name,
                        message=f"✅ Đã tạo thành công plugin `{tool_name}`."
                    )
                    
                return {
                    "task_id": data.get("id"),
                    "status": "done",
                    "result": f"Tạo thành công script '{tool_name}.py'"
                }
            except Exception as e:
                bridge_logger.error(f"Error generating {tool_name}: {e}")
                self._write_selfrepair_log(
                    role="system",
                    plugin=tool_name,
                    message=f"❌ Lỗi khi AI cố sửa plugin `{tool_name}`: {str(e)}"
                )
                return {
                    "task_id": data.get("id"),
                    "status": "error",
                    "message": f"Code Gen Error: {str(e)}"
                }
                
        return {
            "task_id": data.get("id"),
            "status": "error",
            "message": f"Unknown task: {task_type}"
        }

    def connection_check(self):
        """Checks if the bridge is currently heartbeat-ing."""
        if not os.path.exists(HEARTBEAT_FILE):
            return False
        try:
            with open(HEARTBEAT_FILE, "r") as f:
                last_beat = float(f.read().strip())
            return (time.time() - last_beat) < 30
        except:
            return False

    def connection_test(self, task_id="test_conn"):
        """Performs a full request-response cycle test."""
        # Logic to be implemented or coordinated with server side
        pass

def run_bridge_loop():
    event_handler = AntigravityHandler()
    observer = Observer()
    observer.schedule(event_handler, PATH_TO_REQUESTS, recursive=False)
    
    bridge_logger.info(f"🚀 Jarvis Bridge đang lắng nghe tại: {PATH_TO_REQUESTS}...")
    observer.start()
    
    # Touch heartbeat immediately
    try:
        with open(HEARTBEAT_FILE, "w") as f:
            f.write(str(time.time()))
    except: pass
    
    try:
        while True:
            time.sleep(5)
            # Update heartbeat
            try:
                with open(HEARTBEAT_FILE, "w") as f:
                    f.write(str(time.time()))
            except: pass
    except KeyboardInterrupt:
        observer.stop()
        bridge_logger.info("🛑 Bridge đã dừng.")
    except Exception:
        observer.stop()
    observer.join()

def start_bridge():
    import threading
    thread = threading.Thread(target=run_bridge_loop, daemon=True)
    thread.start()
    return thread

if __name__ == "__main__":
    run_bridge_loop()
