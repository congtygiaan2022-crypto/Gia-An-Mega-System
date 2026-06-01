from agents.base_agent import BaseAgent

class AutomationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="AutomationAgent",
            instructions=(
                "Bạn xử lý các tác vụ tự động hóa cục bộ một cách chính xác. "
                "Bạn quản lý tệp tin, định dạng dữ liệu, lưu vào Excel/CSV và tương tác với hệ thống cục bộ."
            )
        )
