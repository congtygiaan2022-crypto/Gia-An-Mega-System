import os
import json
import time
import logging
import sys
from dotenv import load_dotenv
load_dotenv()
import google.generativeai as genai
from openai import OpenAI
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

def generate_code_via_llm(prompt: str) -> str:
    """Gọi LLM (Gemini hoặc OpenAI) để sinh mã nguồn Python."""
    # 1. Thử Gemini API
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key and gemini_key != "YOUR_GEMINI_KEY":
        try:
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except Exception as e:
            bridge_logger.warning(f"Gemini API Error: {e}")

    # 2. Thử OpenAI/Freemodel API
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key != "YOUR_OPENAI_KEY":
        try:
            base_url = os.getenv("OPENAI_BASE_URL")
            model = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
            if base_url:
                if "freemodel.dev" in base_url:
                    if not base_url.endswith("/v1"):
                        base_url = base_url.rstrip("/") + "/v1"
                    model = "gpt-5.4"
                client = OpenAI(api_key=openai_key, base_url=base_url)
            else:
                if not model.startswith("gpt"):
                    model = "gpt-4o-mini"
                client = OpenAI(api_key=openai_key)

            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            if response and response.choices:
                return response.choices[0].message.content
        except Exception as e:
            bridge_logger.warning(f"OpenAI API Error: {e}")

    return None

def extract_python_code(llm_output: str) -> str:
    """Trích xuất mã nguồn Python từ code block ```python ... ``` của LLM."""
    if not llm_output:
        return ""
    import re
    match = re.search(r"```python\s*(.*?)\s*```", llm_output, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r"```\s*(.*?)\s*```", llm_output, re.DOTALL)
    if match:
        return match.group(1).strip()
    return llm_output.strip()

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
                bridge_logger.info(f"Generating code for '{tool_name}' using Antigravity AI Engine...")
                
                plugin_dir = os.path.join(PROJECT_ROOT, "plugins")
                plugin_path = os.path.join(plugin_dir, f"{tool_name}.py")
                
                if task_type == "fix_plugin":
                    error_trace = data.get("error", "")
                    
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
                    
                    # Đọc code cũ nếu có
                    original_code = ""
                    if os.path.exists(plugin_path):
                        try:
                            with open(plugin_path, "r", encoding="utf-8") as f:
                                original_code = f.read()
                        except Exception as read_err:
                            bridge_logger.warning(f"Could not read original code: {read_err}")
                    
                    # Construct prompt for LLM
                    prompt = f"""
You are Antigravity, an expert AI developer agent.
You are tasked with fixing a bug in the Python plugin '{tool_name}.py'.

Here is the original source code of the plugin:
```python
{original_code}
```

Here is the error traceback and log details:
{error_trace}

Please analyze the error and output the entire corrected python code.
Your output must contain only the valid python code inside a single ```python ``` code block. Do not write any other explanation or text outside the code block.
"""
                    
                    llm_response = generate_code_via_llm(prompt)
                    if not llm_response:
                        raise Exception("LLM returned empty response or API call failed.")
                        
                    fixed_code = extract_python_code(llm_response)
                    if not fixed_code:
                        raise Exception("Failed to extract python code from LLM response.")
                    
                    # Backup the original file
                    if os.path.exists(plugin_path):
                        backup_path = plugin_path + ".bak"
                        try:
                            import shutil
                            shutil.copy2(plugin_path, backup_path)
                            bridge_logger.info(f"Created backup of {tool_name}.py at {backup_path}")
                        except Exception as backup_err:
                            bridge_logger.warning(f"Failed to create backup: {backup_err}")
                            
                    # Overwrite the original plugin file
                    os.makedirs(plugin_dir, exist_ok=True)
                    with open(plugin_path, "w", encoding="utf-8") as f:
                        f.write(fixed_code)
                    bridge_logger.info(f"Successfully fixed and updated plugin: {plugin_path}")
                    
                    # Save a copy as proposed fix just in case the UI panel monitors it
                    proposed_path = os.path.join(plugin_dir, f"{tool_name}_proposed_fix.py")
                    try:
                        with open(proposed_path, "w", encoding="utf-8") as f:
                            f.write(fixed_code)
                    except:
                        pass

                    # Log kết quả sau khi sửa
                    self._write_selfrepair_log(
                        role="ai",
                        plugin=tool_name,
                        message=f"✅ Đã sửa thành công lỗi của plugin `{tool_name}`. Đã cập nhật file trực tiếp."
                    )
                else:
                    self._write_selfrepair_log(
                        role="system",
                        plugin=tool_name,
                        message=f"🛠️ Đang tạo mới plugin `{tool_name}` theo yêu cầu: {requirement}"
                    )
                    
                    # Construct prompt for LLM to generate tool from scratch
                    prompt = f"""
You are Antigravity, an expert AI developer agent.
You are tasked with generating a Python plugin '{tool_name}.py' based on the following requirement:
{requirement}

Requirements for the plugin:
- It must have a `Plugin` class or a top-level `run` function.
- If it uses a `Plugin` class, it must have an `__init__(self)` initializing `self.name` and `self.description` and a `run(self, **kwargs)` method returning a dict with "status": "success"/"error".
- Ensure clean code, appropriate logging (using core.logger.get_module_logger), and error handling.
- Output the entire python code inside a single ```python ``` code block. Do not write any other explanation or text outside the code block.
"""
                    llm_response = generate_code_via_llm(prompt)
                    if not llm_response:
                        raise Exception("LLM returned empty response or API call failed.")
                        
                    generated_code = extract_python_code(llm_response)
                    if not generated_code:
                        raise Exception("Failed to extract python code from LLM response.")
                        
                    os.makedirs(plugin_dir, exist_ok=True)
                    with open(plugin_path, "w", encoding="utf-8") as f:
                        f.write(generated_code)
                    bridge_logger.info(f"Successfully generated new plugin: {plugin_path}")
                    
                    self._write_selfrepair_log(
                        role="ai",
                        plugin=tool_name,
                        message=f"✅ Đã tạo thành công plugin `{tool_name}`."
                    )
                    
                # Update registry
                tool_generator._update_registry(tool_name)
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
