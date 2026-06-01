import importlib
import time
import os
from core.log_manager import LogManager
from core.memory_system import memory_system
from core.debugger import capture_error
from core.config import PROJECT_ROOT

log_manager = LogManager()

class PluginExecutionEngine:
    """
    Jarvis OS Plugin Execution Engine
    - Plugin Loader: dynamically load .py files
    - Plugin Validator: check for required function run()
    - Plugin Executor: run plugin with args
    - Result Handler: log results, store memory, handle errors
    """
    def __init__(self):
        self.plugin_dir = os.path.join(PROJECT_ROOT, "plugins")

    def _load_plugin(self, plugin_name):
        """Plugin Loader: Imports module dynamically."""
        try:
            return importlib.import_module(f"plugins.{plugin_name}")
        except Exception as e:
            return e

    def _validate_plugin(self, module):
        """Plugin Validator: Checks for run() function."""
        if isinstance(module, Exception):
            return False, f"Import error: {module}"
        if not hasattr(module, 'run') and not hasattr(module, 'Plugin'):
            return False, "Missing run() function or Plugin class"
        return True, None

    def execute(self, plugin_name, task_id, run_id, **kwargs):
        """Plugin Executor & Result Handler."""
        log_manager.log_step(run_id, "PluginExecution", "INFO", f"Executing plugin: {plugin_name}")
        
        module = self._load_plugin(plugin_name)
        valid, error = self._validate_plugin(module)
        
        if not valid:
            log_manager.log_step(run_id, "PluginError", "ERROR", error)
            memory_system.store_long_term("System", "errors", {
                "plugin": plugin_name,
                "task_id": task_id,
                "error": error,
                "status": "failed"
            })
            return {"status": "error", "message": error}

        try:
            # Execute
            start_time = time.time()
            if hasattr(module, 'run'):
                try:
                    result = module.run(**kwargs)
                except TypeError:
                    result = module.run()
            elif hasattr(module, 'Plugin'):
                plugin_instance = module.Plugin()
                try:
                    result = plugin_instance.run(**kwargs)
                except TypeError:
                    result = plugin_instance.run()
            duration = time.time() - start_time
            
            # Result Handler
            log_manager.log_step(run_id, "PluginExecution", "SUCCESS", f"Plugin {plugin_name} finished in {duration:.2f}s")
            memory_system.store_long_term("System", "plugin_execution", {
                "plugin": plugin_name,
                "task_id": task_id,
                "status": "success",
                "duration": duration
            })
            return {"status": "success", "result": result}
            
        except Exception as e:
            err_trace = capture_error(e)
            log_manager.log_step(run_id, "PluginExecution", "ERROR", str(e))
            memory_system.store_long_term("System", "errors", {
                "plugin": plugin_name,
                "task_id": task_id,
                "error": str(e),
                "traceback": err_trace,
                "status": "failed"
            })
            return {"status": "error", "message": str(e), "traceback": err_trace}

# Global instance
plugin_execution_engine = PluginExecutionEngine()
