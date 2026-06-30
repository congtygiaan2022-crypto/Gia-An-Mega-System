import os
from core.logger import get_module_logger
from core.memory_system import memory_system
from database.mysql_connector import mysql_connector, AgentMemory

logger = get_module_logger("ErrorMonitor")

class ErrorMonitor:
    def __init__(self, log_file=None):
        if log_file:
            self.log_file = log_file
        else:
            self.log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs", "javis.log")

    def capture_error(self, last_n_lines=100):
        """Reads logs and MySQL for errors."""
        # 1. From MySQL
        db_errors = memory_system.get_long_term("System", category="errors", limit=10)
        
        # 2. From Log File
        file_errors = []
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in lines[-last_n_lines:]:
                        if "ERROR" in line or "CRITICAL" in line:
                            file_errors.append({"source": "log_file", "content": line.strip()})
            except Exception as e:
                logger.error(f"Failed to read log file: {e}")

        # Combine and store
        all_errors = db_errors + file_errors
        if all_errors:
             logger.info(f"Captured {len(all_errors)} errors.")
        return all_errors

    def collect_logs(self, module_name, last_n_lines=50):
        """Collects logs specific to a module."""
        # Implementation remains similar but could also query MySQL if logs are stored there
        if not os.path.exists(self.log_file):
            return ""
        
        module_logs = []
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-200:]: 
                    if module_name in line:
                        module_logs.append(line.strip())
            return "\n".join(module_logs[-last_n_lines:])
        except Exception as e:
            logger.error(f"Error collecting logs for {module_name}: {e}")
            return ""
