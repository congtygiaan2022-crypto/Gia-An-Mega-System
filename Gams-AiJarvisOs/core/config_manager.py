import os
import json
import logging
from core.config import PROJECT_ROOT

logger = logging.getLogger("ConfigManager")

class ConfigManager:
    """
    Manages JSON configuration files in the config/ directory.
    - agent_config.json
    - api_accounts.json
    - plugin_registry.json (legacy sync)
    """
    def __init__(self):
        self.config_dir = os.path.join(PROJECT_ROOT, "config")
        os.makedirs(self.config_dir, exist_ok=True)

    def _get_path(self, filename):
        if not filename.endswith(".json"):
            filename += ".json"
        return os.path.join(self.config_dir, filename)

    def load_config(self, filename, default=None):
        path = self._get_path(filename)
        if not os.path.exists(path):
            return default if default is not None else {}
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config {filename}: {e}")
            return default if default is not None else {}

    def save_config(self, filename, data):
        path = self._get_path(filename)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving config {filename}: {e}")
            return False

# Global instance
config_manager = ConfigManager()
