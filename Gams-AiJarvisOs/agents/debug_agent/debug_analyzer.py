import re
from core.logger import get_module_logger

logger = get_module_logger("DebugAnalyzer")

class DebugAnalyzer:
    CORE_MODULES = ["Scheduler", "TaskManager", "LogManager", "PluginRegistry", "SystemMonitor", "AutonomousEngine", "AntigravityConnector"]

    def analyze_stacktrace(self, error_msg):
        """Extracts useful information from a stacktrace/error message."""
        # Simple extraction of the main error message
        return error_msg

    def detect_bug(self, error_msg):
        """Attempts to identify the module and type of bug."""
        # Extract module name from log format: timestamp | level | module | message
        match = re.search(r'\|\s+\w+\s+\|\s+([^|]+?)\s+\|', error_msg)
        if match:
            module = match.group(1).strip()
            if module in self.CORE_MODULES:
                return {"module": "CoreComponent", "original_module": module, "type": "system_error"}
            return {"module": module, "type": "plugin_error"}
        
        return {"module": "Unknown", "type": "unknown_error"}
