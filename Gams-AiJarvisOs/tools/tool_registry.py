import inspect
import os
import importlib.util
from typing import Callable, Any, Dict

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._descriptions: Dict[str, str] = {}
        self._loaded_files: Dict[str, float] = {}  # file_path -> mtime

    def register(self, name: str = None, description: str = None):
        """Decorator to register a tool."""
        def decorator(func: Callable):
            tool_name = name or func.__name__
            self._tools[tool_name] = func
            self._descriptions[tool_name] = description or inspect.getdoc(func) or "No description provided."
            return func
        return decorator

    def get_tool(self, name: str) -> Callable:
        return self._tools.get(name)

    def get_all_tools(self) -> Dict[str, Callable]:
        return self._tools

    def get_tool_descriptions(self) -> str:
        desc = []
        for name, doc in self._descriptions.items():
            desc.append(f"{name}: {doc}")
        return "\n".join(desc)

    def auto_load_tools(self, tools_dir: str = "tools", force: bool = False):
        """Dynamically load all tool modules in the specified directory."""
        if not os.path.exists(tools_dir):
            return

        for filename in os.listdir(tools_dir):
            if filename.endswith(".py") and filename != "tool_registry.py" and not filename.startswith("__"):
                module_name = filename[:-3]
                file_path = os.path.join(tools_dir, filename)
                mtime = os.path.getmtime(file_path)
                
                # Only load if forced or mtime changed
                if not force and self._loaded_files.get(file_path) == mtime:
                    continue

                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    try:
                        spec.loader.exec_module(module)
                        self._loaded_files[file_path] = mtime
                    except Exception as e:
                        print(f"Registry: Error loading {module_name}: {e}")

# Global registry instance
registry = ToolRegistry()

def tool(name: str = None, description: str = None):
    """Convenience decorator for registering a tool."""
    return registry.register(name, description)

def load_tools(tools_dir: str = "tools"):
    """Convenience function to trigger auto-loading."""
    registry.auto_load_tools(tools_dir)

def reload_tools():
    """Wipes the current registry and re-scans the directory."""
    print("Registry: Reloading tools...")
    registry._tools = {}
    registry._descriptions = {}
    load_tools()

# Auto-load tools on startup
load_tools()
