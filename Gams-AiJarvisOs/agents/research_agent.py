from agents.base_agent import BaseAgent

class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ResearchAgent",
            instructions=(
                "Bạn là một chuyên gia nghiên cứu. Mục tiêu của bạn là thu thập thông tin, "
                "tổng hợp kết quả và đưa ra các phân tích có cấu trúc. "
                "Bạn nên sử dụng các công cụ tìm kiếm để xác minh các sự thật."
            )
        )
