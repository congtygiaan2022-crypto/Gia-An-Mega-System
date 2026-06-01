from core.logger import get_module_logger

logger = get_module_logger("Fix_gams_insight_reader")

class Plugin:
    def __init__(self):
        self.name = "fix_gams_insight_reader"
        self.description = """Sửa lỗi trong file gams_insight_reader.
Traceback: 2026-03-16 16:15:42 | ERROR | gams_insight_reader | Plugin gams_insight_reader lỗi: DataManager.__init__() missing 1 required positional argument: 'data_file'"""

    def run(self, **kwargs):
        logger.info(f"Executing plugin: fix_gams_insight_reader with args: {kwargs}")
        return {"status": "success", "message": "Plugin fix_gams_insight_reader executed successfully."}
