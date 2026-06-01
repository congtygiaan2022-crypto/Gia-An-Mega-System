import os
import json
from core.config import PROJECT_ROOT
from core.logger import get_module_logger

logger = get_module_logger("ReportGenerator")

class ReportGenerator:
    def generate_report(self, processed_data):
        """Generates a report from processed data."""
        logger.info("Generating report...")
        report = {
            "title": "Jarvis OS Performance Report",
            "data": processed_data,
            "status": "Final"
        }
        return report

    def export_report(self, report, format="json"):
        """Exports the report to a file and logs metadata in MySQL."""
        report_dir = os.path.join(PROJECT_ROOT, "reports")
        os.makedirs(report_dir, exist_ok=True)
        filename = f"report_{int(time.time())}.json"
        file_path = os.path.join(report_dir, filename)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=4, ensure_ascii=False)
            logger.info(f"Report exported to {file_path}")
            
            # Store metadata in MySQL
            from core.memory_system import memory_system
            memory_system.store_long_term("ReportAgent", "report_history", {
                "title": report.get("title"),
                "file_path": file_path,
                "timestamp": time.time()
            })
            
            return file_path
        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            return None
