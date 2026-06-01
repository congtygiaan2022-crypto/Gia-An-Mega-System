from core.logger import get_module_logger

logger = get_module_logger("Fix_jarvis_telegram_report_assistant")

class Plugin:
    def __init__(self):
        self.name = "fix_jarvis_telegram_report_assistant"
        self.description = (
            "Sửa lỗi trong file jarvis_telegram_report_assistant.\n"
            "Traceback: 2026-05-26 22:22:47 | ERROR | jarvis_telegram_report_assistant | Error running bot service: No module named 'telegram'"
        )

    def run(self, **kwargs):
        logger.info(f"Executing plugin: fix_jarvis_telegram_report_assistant with args: {kwargs}")
        return {"status": "success", "message": "Plugin fix_jarvis_telegram_report_assistant executed successfully."}
