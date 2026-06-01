import os
import inspect
import importlib.util
from typing import Dict, Any
from core.logger import get_module_logger

logger = get_module_logger("PluginRegistry")

class PluginRegistry:
    def __init__(self, plugins_dir="plugins"):
        self.plugins_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), plugins_dir)
        os.makedirs(self.plugins_dir, exist_ok=True)
        self.plugins: Dict[str, Any] = {}
        self._loaded_files: Dict[str, float] = {}  # file_path -> mtime

    def load_plugins(self, force: bool = False):
        """Dynamically loads all plugins from the directory."""
        # logger.info(f"Scanning for plugins in {self.plugins_dir}...")
        for filename in os.listdir(self.plugins_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                plugin_name = filename[:-3]
                self._load_plugin(plugin_name, force=force)
        return self.plugins

    def _load_plugin(self, plugin_name, force=False):
        file_path = os.path.join(self.plugins_dir, f"{plugin_name}.py")
        if not os.path.exists(file_path):
            return

        mtime = os.path.getmtime(file_path)
        if not force and self._loaded_files.get(file_path) == mtime:
            return
        spec = importlib.util.spec_from_file_location(plugin_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                # Look for a class named 'Plugin'
                if hasattr(module, 'Plugin'):
                    plugin_instance = module.Plugin()
                    self.plugins[plugin_name] = plugin_instance
                    self._loaded_files[file_path] = mtime
                    logger.info(f"Loaded plugin: {plugin_name}")
                else:
                    logger.warning(f"Plugin {plugin_name} skipped: No 'Plugin' class found.")
            except Exception as e:
                logger.error(f"Error loading plugin {plugin_name}: {e}")

    def get_plugin(self, name):
        return self.plugins.get(name)

# Global instance
plugin_registry = PluginRegistry()
plugin_registry.load_plugins()
