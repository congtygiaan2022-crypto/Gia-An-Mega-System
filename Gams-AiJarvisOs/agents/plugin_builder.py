import os
from core.logger import get_module_logger
from integrations.antigravity_connector import antigravity_connector

logger = get_module_logger("PluginBuilder")

class PluginBuilder:
    def __init__(self):
        self.plugins_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugins")
        os.makedirs(self.plugins_dir, exist_ok=True)

    def request_new_plugin(self, name, description):
        """Asks Antigravity to build a new plugin."""
        logger.info(f"Requesting new plugin: {name}")
        requirement = f"Tạo một plugin Javis mới.\nTên: {name}\nMô tả: {description}\nLưu vào thư mục plugins/"
        antigravity_connector.request_tool_generation(f"plugin_{name}", requirement)
        return f"Yêu cầu tạo plugin {name} đã được gửi."

    def create_plugin_template(self, name, description):
        """Internal helper to scaffold a plugin."""
        # This can be used if Antigravity provides content or for basic scaffolding
        # Normally Antigravity would write the file directly.
        pass

# Global instance
plugin_builder = PluginBuilder()
