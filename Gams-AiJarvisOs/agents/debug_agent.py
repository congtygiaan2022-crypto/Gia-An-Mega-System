import os
import re
from core.logger import get_module_logger

logger = get_module_logger("DebugAgent")

class DebugAgent:
    def __init__(self):
        self.log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "javis.log")

    def analyze_logs(self):
        """Reads the latest logs and detects errors."""
        if not os.path.exists(self.log_file):
            return "No logs found."

        errors = []
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                # Get last 100 lines for analysis
                for line in lines[-100:]:
                    skip_keywords = [
                        "AutonomousEngine", "ErrorRegistry", "DebugAgent", 
                        "SystemMonitor", "AntigravityConnector", "server"
                    ]
                    if "ERROR" in line or "CRITICAL" in line:
                        if not any(kw in line for kw in skip_keywords):
                            errors.append(line.strip())
        except Exception as e:
            logger.error(f"Failed to read log file: {e}")
            return f"Error reading logs: {e}"

        if not errors:
            return "No recent errors detected."

        logger.info(f"Detected {len(errors)} errors in logs.")
        return errors

    CORE_MODULES = ["Scheduler", "TaskManager", "LogManager", "PluginRegistry", "SystemMonitor", "AutonomousEngine", "AntigravityConnector"]

    def identify_faulty_module(self, error_msg):
        """Attempts to identify the module from an error message."""
        # Simple regex to find module name in the log format: timestamp | level | module | message
        match = re.search(r'\|\s+\w+\s+\|\s+([^|]+?)\s+\|', error_msg)
        if match:
            module = match.group(1).strip()
            if module in self.CORE_MODULES:
                return "CoreComponent"
            return module
        return "Unknown"

    def run(self):
        """Standard run method for engines."""
        return self.analyze_logs()

# Global instance
debug_agent = DebugAgent()
