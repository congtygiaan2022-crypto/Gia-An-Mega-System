import importlib
import time
from core.log_manager import LogManager
from core.memory_manager import MemoryManager
from core.debugger import capture_error, send_to_antigravity

log_manager = LogManager()
memory_manager = MemoryManager()

def run_plugin(plugin_name, task_id, run_id, *args, **kwargs):
    """
    Dynamically loads and executes a plugin.
    If it fails, it triggers the self-healing debugger.
    """
    log_manager.log_step(run_id, "Execution", "INFO", f"Starting plugin {plugin_name}")
    
    try:
        # Import module dynamically from plugins package
        module = importlib.import_module(f"plugins.{plugin_name}")
        
        # Execute the run() function or the Plugin class run method
        if hasattr(module, 'run'):
            # Provide kwargs if the plugin accepts them, else just call run()
            try:
                result = module.run(**kwargs)
            except TypeError:
                # If plugin run() takes no arguments
                result = module.run()
        elif hasattr(module, 'Plugin'):
            plugin_instance = module.Plugin()
            if hasattr(plugin_instance, 'run'):
                try:
                    result = plugin_instance.run(**kwargs)
                except TypeError:
                    result = plugin_instance.run()
            else:
                raise AttributeError(f"Plugin class in {plugin_name} is missing a run() method.")
        else:
            raise AttributeError(f"Plugin {plugin_name} is missing a run() function or a Plugin class.")
            
        log_manager.log_step(run_id, "Execution", "SUCCESS", f"Plugin {plugin_name} finished")
        
        # Remember successful run
        memory_manager.add_plugin_run({
            "plugin": plugin_name,
            "task_id": task_id,
            "run_id": run_id,
            "timestamp": time.time(),
            "status": "success"
        })
        
        return result
        
    except Exception as e:
        err_trace = capture_error(e)
        
        log_manager.log_step(run_id, "Execution Error", "ERROR", f"Plugin {plugin_name} crashed: {str(e)}")
        
        # Remember error
        memory_manager.add_error({
            "plugin": plugin_name,
            "task_id": task_id,
            "run_id": run_id,
            "timestamp": time.time(),
            "error_type": type(e).__name__,
            "message": str(e),
            "traceback": err_trace
        })
        
        # Self-healing request to Antigravity
        log_manager.log_step(run_id, "Self-Healing", "WARNING", f"Sending {plugin_name} traceback to AI Code Generator")
        send_to_antigravity(plugin_name, err_trace)
        
        raise e
