import os
from tools.tool_registry import registry

class ToolGenerator:
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = plugins_dir

    def _update_registry(self, name: str):
        import json
        import os
        registry_path = os.path.join(self.plugins_dir, "plugin_registry.json")
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if name not in data.get("plugins", []):
                data.setdefault("plugins", []).append(name)
                with open(registry_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
        except Exception as e:
            pass # Ignore if registry doesn't exist yet

    def create_tool(self, name: str, description: str = "Tự động tạo bởi Javis", code: str = None) -> str:
        """
        Creates a new plugin file and auto-registers it.
        """
        if not code:
            code = f"""from core.logger import get_module_logger

logger = get_module_logger("{name.capitalize()}")

class Plugin:
    def __init__(self):
        self.name = "{name}"
        self.description = "{description}"

    def run(self, **kwargs):
        logger.info(f"Executing plugin: {name} with args: {{kwargs}}")
        return {{"status": "success", "message": "Plugin {name} executed successfully."}}
"""
        
        file_path = os.path.join(self.plugins_dir, f"{name}.py")
        try:
            if not os.path.exists(self.plugins_dir):
                os.makedirs(self.plugins_dir, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
            
            self._update_registry(name)
            return f"Đã tạo plugin '{name}' tại {file_path} và đăng ký thành công."
        except Exception as e:
            return f"Lỗi tạo plugin: {e}"

# Global instance
tool_generator = ToolGenerator()
