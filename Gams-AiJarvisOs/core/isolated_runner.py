import sys
import os
import json
import argparse
import time
import importlib
import traceback

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import get_module_logger
from core.log_manager import LogManager
from core.memory_manager import MemoryManager
from core.debugger import capture_error, send_to_antigravity
import logging

class SQLiteLogHandler(logging.Handler):
    def __init__(self, run_id, log_manager):
        super().__init__()
        self.run_id = run_id
        self.log_manager = log_manager

    def emit(self, record):
        try:
            msg = self.format(record)
            status = "INFO"
            if record.levelno >= logging.ERROR:
                status = "ERROR"
            elif record.levelno >= logging.WARNING:
                status = "WARNING"
            self.log_manager.log_step(self.run_id, record.name, status, msg)
        except Exception:
            self.handleError(record)

logger = get_module_logger("IsolatedRunner")
log_manager = LogManager()
memory_manager = MemoryManager()

def main():
    parser = argparse.ArgumentParser(description="Jarvis Isolated Plugin Runner")
    parser.add_argument("--plugin", required=True, help="Plugin name to run")
    parser.add_argument("--task_id", required=True, help="Task ID")
    parser.add_argument("--run_id", required=True, help="Run ID")
    parser.add_argument("--args", help="Arguments in JSON format")

    args = parser.parse_args()
    
    plugin_name = args.plugin
    task_id = args.task_id
    run_id = args.run_id
    
    kwargs = {}
    if args.args:
        if args.args.endswith(".json") and os.path.exists(args.args):
            try:
                with open(args.args, "r", encoding="utf-8") as f:
                    kwargs = json.load(f)
            except Exception as e:
                print(f"Error loading args from file: {e}")
                kwargs = {}
        else:
            try:
                kwargs = json.loads(args.args)
            except:
                kwargs = {}

    print(f"\n{'='*60}")
    print(f"JARVIS ISOLATED RUNNER | Plugin: {plugin_name}")
    print(f"Run ID: {run_id} | Task ID: {task_id}")
    print(f"{'='*60}\n")

    # Configure root logger to output to console with detailed timestamps
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)
        
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Clean and configure target loggers to propagate to root
    for logger_name in [plugin_name, "GamsUtils", "gams_insight_reader", "gams_utils"]:
        l = logging.getLogger(logger_name)
        l.setLevel(logging.INFO)
        l.propagate = True
        for h in list(l.handlers):
            l.removeHandler(h)

    # Setup SQLite logging capture for this run (added to root logger)
    sqlite_handler = SQLiteLogHandler(run_id, log_manager)
    sqlite_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    sqlite_handler.setFormatter(formatter)
    root_logger.addHandler(sqlite_handler)

    # Create PID file for the scheduler to track
    pid_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    os.makedirs(pid_dir, exist_ok=True)
    pid_file = os.path.join(pid_dir, f"{plugin_name}_{task_id}.pid")
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))

    log_manager.log_step(run_id, "Isolation", "INFO", f"Starting isolated process for {plugin_name}")

    try:
        # Import module dynamically
        module = importlib.import_module(f"plugins.{plugin_name}")
        
        result = None
        if hasattr(module, 'run'):
            # Pattern 1: Top-level run() function
            try:
                result = module.run(**kwargs)
            except TypeError:
                result = module.run()
        elif hasattr(module, 'Plugin'):
            # Pattern 2: Plugin class
            plugin_instance = module.Plugin()
            if hasattr(plugin_instance, 'run'):
                try:
                    result = plugin_instance.run(**kwargs)
                except TypeError:
                    result = plugin_instance.run()
            else:
                raise AttributeError(f"Plugin class in {plugin_name} is missing a run() method.")
        else:
            raise AttributeError(f"Plugin {plugin_name} is missing a top-level run() function or a Plugin class.")

        log_manager.log_step(run_id, "Execution", "SUCCESS", f"Plugin {plugin_name} finished successfully")
        
        # Mark run as success in memory
        memory_manager.add_plugin_run({
            "plugin": plugin_name,
            "task_id": task_id,
            "run_id": run_id,
            "timestamp": time.time(),
            "status": "success"
        })
        
        print(f"\n[SUCCESS] {plugin_name} completed.")

        # Check if result contains error status and report to find_bug.json
        if isinstance(result, dict) and result.get("status") == "error":
            try:
                from core.global_logger import report_bug
                report_bug(
                    project="JarvisOS",
                    module=plugin_name,
                    exception_details=result.get("message", "Unknown plugin error"),
                    context_data={
                        "task_id": task_id,
                        "run_id": run_id,
                        "result": result
                    }
                )
            except Exception as re:
                print(f"Error reporting plugin error to find_bug.json: {re}")

    except Exception as e:
        err_trace = traceback.format_exc()
        print(f"\n[CRASH] {plugin_name} failed: {e}")
        print(f"\nStacktrace:\n{err_trace}")
        
        log_manager.log_step(run_id, "Execution Error", "ERROR", f"Plugin {plugin_name} crashed: {str(e)}")
        
        # Record error to memory
        memory_manager.add_error({
            "plugin": plugin_name,
            "task_id": task_id,
            "run_id": run_id,
            "timestamp": time.time(),
            "error_type": type(e).__name__,
            "message": str(e),
            "traceback": err_trace
        })
        
        # Record error to logs/find_bug.json for self-healing
        try:
            from core.global_logger import report_bug
            report_bug(
                project="JarvisOS",
                module=plugin_name,
                exception_details=str(e),
                context_data={
                    "task_id": task_id,
                    "run_id": run_id,
                    "traceback": err_trace
                }
            )
        except Exception as re:
            print(f"Error reporting bug to find_bug.json: {re}")
            
        # Self-healing trigger
        send_to_antigravity(plugin_name, err_trace)
    
    finally:
        # Final cleanup PID file
        pid_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", f"{plugin_name}_{task_id}.pid")
        if os.path.exists(pid_file):
            try: os.remove(pid_file)
            except: pass

        # Final cleanup delay to allow user to see output if they want (but we use /c so it will close)
        print("\nProcess finished. Closing in 3 seconds...")
        time.sleep(3)
        sys.exit(0)

if __name__ == "__main__":
    main()
