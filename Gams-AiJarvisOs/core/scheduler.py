import schedule
import time
import threading
import uuid
import sys
import os
import json
from core.logger import get_module_logger
from core.task_manager import TaskManager
from core.log_manager import LogManager

logger = get_module_logger("Scheduler")

class Scheduler:
    def __init__(self):
        self.task_manager = TaskManager()
        self.log_manager = LogManager()
        self._stop_event = threading.Event()
        self.thread = None

    def reload_jobs(self):
        schedule.clear()
        tasks = self.task_manager.get_all_tasks()
        count = 0
        for t in tasks:
            if t.get("status") == "active":
                self._schedule_task(t)
                count += 1
        logger.info(f"Reloaded {count} active scheduled tasks.")

    def _schedule_task(self, task_data):
        time_str = task_data.get("schedule", "07:00")
        if ":" in time_str and len(time_str) == 5:
            # 07:00 daily
            schedule.every().day.at(time_str).do(self.run_task_wrapper, task_data)
        elif "phút" in time_str.lower() or "minutes" in time_str.lower():
            try:
                mins = int(''.join(filter(str.isdigit, time_str)))
                schedule.every(mins).minutes.do(self.run_task_wrapper, task_data)
            except:
                logger.error(f"Invalid minute schedule: {time_str}")
        else:
            logger.error(f"Unsupported schedule format: {time_str}")
            
    def run_task_wrapper(self, task_data):
        threading.Thread(target=self._execute_task, args=(task_data,)).start()

    def _execute_task(self, task_data):
        run_id = "run_" + str(uuid.uuid4())[:8]
        task_id = task_data.get("id")
        task_name = task_data.get("name")
        self.log_manager.start_run(run_id, str(task_id), str(task_name))
        
        plugin_name = task_data.get("plugin", "")
        accounts = task_data.get("accounts", {})
        
        try:
            if plugin_name.startswith("wf:"):
                # Run as a workflow using workflow_engine
                from core.workflow_engine import run_workflow
                from core.task_queue import global_task_queue
                
                # Register in task queue for monitoring
                q_id = global_task_queue.submit_task(f"Workflow: {plugin_name[3:]}")
                global_task_queue.tasks[q_id]["status"] = "running"
                
                flow_name = plugin_name[3:] # Remove "wf:" prefix
                try:
                    wf_result = run_workflow(q_id, f"Workflow {flow_name} run", global_task_queue)
                    global_task_queue.tasks[q_id]["status"] = "completed"
                    global_task_queue.tasks[q_id]["result"] = wf_result
                    self.log_manager.finish_run(run_id, "SUCCESS")
                except Exception as e:
                    global_task_queue.tasks[q_id]["status"] = "failed"
                    global_task_queue.tasks[q_id]["result"] = str(e)
                    self.log_manager.finish_run(run_id, "ERROR")
                    raise e
            else:
                # Run as a single plugin (ISOLATED)
                import subprocess
                from core.task_queue import global_task_queue
                
                # Register in task queue for monitoring
                q_id = global_task_queue.submit_task(f"Plugin: {plugin_name}")
                global_task_queue.tasks[q_id]["status"] = "running"
                
                # Auto-close existing instance of this plugin to prevent duplicates
                # pass task_id and kill_service=False so the background bot service itself is not terminated during auto-monitoring runs
                self.terminate_task(plugin_name, task_id, kill_service=False)
                
                # Launch in new CMD window
                # Create a temporary file for arguments to avoid escaping issues in CMD
                arg_file = os.path.join("tmp", f"args_{run_id}.json")
                os.makedirs("tmp", exist_ok=True)
                with open(arg_file, "w", encoding="utf-8") as f:
                    json.dump({"accounts": accounts}, f)
                
                # Use /k to stay open if requested, else /c to close after execution
                stay_open = task_data.get("stay_open", False)
                cmd_flag = "/k" if stay_open else "/c"
                
                import sys
                script_path = os.path.abspath("core/isolated_runner.py")
                arg_file_abs = os.path.abspath(arg_file)
                title = f"Jarvis_Auto_{plugin_name}_{task_id}"
                
                if sys.platform == "win32":
                    cmd_args = f'cmd.exe {cmd_flag} "title {title} && \"{sys.executable}\" \"{script_path}\" --plugin {plugin_name} --task_id {task_id} --run_id {run_id} --args \"{arg_file_abs}\""'
                    creationflags = subprocess.CREATE_NEW_CONSOLE
                else:
                    cmd_args = [
                        sys.executable,
                        script_path,
                        "--plugin", plugin_name,
                        "--task_id", str(task_id),
                        "--run_id", run_id,
                        "--args", arg_file_abs
                    ]
                    creationflags = 0
                
                subprocess.Popen(
                    cmd_args,
                    creationflags=creationflags,
                    close_fds=True
                )
                
                # Update task status to completed (meaning it was started successfully)
                # Since it's in a separate CMD, we consider the "trigger" task as done.
                global_task_queue.tasks[q_id]["status"] = "completed"
                global_task_queue.tasks[q_id]["result"] = f"Started {plugin_name} in new window with arg_file."
                
                self.log_manager.finish_run(run_id, "STARTED (Isolated)")
        except Exception as e:
            # plugin_engine internally handles logging the step and hitting the debugger
            # we just close out the run tracker
            logger.error(f"Task Execution Error: {e}")
            self.log_manager.finish_run(run_id, "ERROR")

    def terminate_task(self, plugin_name, task_id=None, kill_service=True):
        """Kills any processes or CMD windows associated with the plugin."""
        if not plugin_name:
            return
        logger.info(f"Terminating instance of {plugin_name} (Task ID: {task_id}, kill_service: {kill_service})")
        
        # 2. Hard kill associated processes using PID file if exists
        import psutil
        count = 0
        
        pid_files = []
        if task_id:
            # Specific file
            specific_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", f"{plugin_name}_{task_id}.pid")
            if os.path.exists(specific_file):
                pid_files.append(specific_file)
        else:
            # Fallback/wildcard: find all matching data/{plugin_name}_*.pid
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            if os.path.exists(data_dir):
                for filename in os.listdir(data_dir):
                    if filename.startswith(f"{plugin_name}_") and filename.endswith(".pid"):
                        pid_files.append(os.path.join(data_dir, filename))
            # Also check the old format just in case
            old_file = os.path.join(data_dir, f"{plugin_name}.pid")
            if os.path.exists(old_file):
                pid_files.append(old_file)

        for pf in pid_files:
            try:
                with open(pf, "r") as f:
                    pid = int(f.read().strip())
                if psutil.pid_exists(pid):
                    proc = psutil.Process(pid)
                    # Kill children too
                    for child in proc.children(recursive=True):
                        try: child.kill()
                        except: pass
                    try: proc.kill()
                    except: pass
                    count += 1
                    logger.info(f"Killed process {pid} ({plugin_name}) via PID file {os.path.basename(pf)}.")
                try: os.remove(pf)
                except: pass
            except Exception as e:
                logger.error(f"Error killing via PID file {pf}: {e}")

        # 3. Search for any other rogue instances via psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline') or []
                cmdline_str = " ".join(cmdline).lower()
                
                # Check for isolated_runner.py with our plugin name
                if "python" in proc.info['name'].lower() and \
                   "isolated_runner.py" in cmdline_str and \
                   f"--plugin {plugin_name}" in cmdline_str:
                    
                    if task_id and f"--task_id {task_id}" not in cmdline_str:
                        continue
                        
                    logger.info(f"Killing rogue process {proc.info['pid']} ({plugin_name})")
                    try: proc.kill()
                    except: pass
                    count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 4. Fallback to taskkill for window titles (specific to task_id if provided)
        try:
            import subprocess
            if task_id:
                subprocess.run(f'taskkill /F /FI "WINDOWTITLE eq Jarvis_Auto_{plugin_name}_{task_id}*" /T', shell=True, capture_output=True)
                if kill_service and plugin_name == "jarvis_telegram_report_assistant":
                    subprocess.run('taskkill /F /FI "WINDOWTITLE eq Jarvis_Manual_Telegram_Bot*" /T', shell=True, capture_output=True)
            else:
                subprocess.run(f'taskkill /F /FI "WINDOWTITLE eq Jarvis_Auto_{plugin_name}_*" /T', shell=True, capture_output=True)
                if kill_service:
                    subprocess.run(f'taskkill /F /FI "WINDOWTITLE eq Jarvis_Manual_{plugin_name}*" /T', shell=True, capture_output=True)
                    if plugin_name == "jarvis_telegram_report_assistant":
                        subprocess.run('taskkill /F /FI "WINDOWTITLE eq Jarvis_Manual_Telegram_Bot*" /T', shell=True, capture_output=True)
        except:
            pass
            
        logger.info(f"Termination finished for {plugin_name}. Total {count} processes cleaned up.")

    def reset_task(self, task_data):
        """Kills and then restarts a task."""
        plugin_name = task_data.get("plugin")
        self.terminate_task(plugin_name)
        time.sleep(1) # Short grace period
        self.run_task_wrapper(task_data)

    def start(self):
        logger.info("Starting background scheduler...")
        self.reload_jobs()
        
        def run_loop():
            while not self._stop_event.is_set():
                schedule.run_pending()
                time.sleep(10)
        
        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        if self._stop_event:
            self._stop_event.set()

global_scheduler = Scheduler()
