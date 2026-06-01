import os
import psutil
from core.logger import get_module_logger

logger = get_module_logger("SystemMonitor")

class SystemMonitor:
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.last_cpu_warning = 0
        self._cached_cpu = 0
        self._last_cpu_time = 0

    def get_stats(self):
        """Gets CPU, RAM, and Disk usage."""
        import time
        try:
            now = time.time()
            # Cache CPU for 2 seconds to avoid blocking FastAPI workers too often
            if now - self._last_cpu_time > 2:
                self._cached_cpu = psutil.cpu_percent(interval=0.1) # Reduced interval
                self._last_cpu_time = now
                
            cpu = self._cached_cpu
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
            
            stats = {
                "cpu_percent": cpu,
                "ram_percent": memory_info.percent,
                "disk_percent": disk_info.percent,
                "process_memory_mb": self.process.memory_info().rss / (1024 * 1024)
            }
            
            # Check for warnings (throttled to once per 60s)
            if stats["cpu_percent"] > 85:
                if now - self.last_cpu_warning > 60:
                    logger.warning(f"High CPU Usage detected: {stats['cpu_percent']}%")
                    self.last_cpu_warning = now
            
            if stats["ram_percent"] > 90:
                logger.critical(f"Critical RAM Usage detect: {stats['ram_percent']}%")
                
            return stats
        except Exception as e:
            logger.error(f"Failed to monitor system: {e}")
            return None

    def run(self):
        """Standard run method for engines."""
        return self.get_stats()

# Global instance
system_monitor = SystemMonitor()
