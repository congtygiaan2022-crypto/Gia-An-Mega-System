from core.logger import get_module_logger

logger = get_module_logger("Fake_test_tool")

class Plugin:
    def __init__(self):
        self.name = "fake_test_tool"
        self.description = "hello world"

    def run(self, **kwargs):
        if kwargs.get("action") == "stop":
            return {"status": "success", "message": "Stopped."}
        logger.info(f"Executing plugin: fake_test_tool with args: {kwargs}")
        return {"status": "success", "message": "Plugin fake_test_tool executed successfully."}
