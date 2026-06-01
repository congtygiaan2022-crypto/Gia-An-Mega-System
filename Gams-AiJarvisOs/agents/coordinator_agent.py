from agents.base_agent import BaseAgent

class CoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="CoordinatorAgent",
            instructions=(
                "Bạn là Người Điều Phối cấp cao. Nhiệm vụ của bạn là chia nhỏ yêu cầu của người dùng "
                "thành các bước khả thi và quyết định xem Agent chuyên biệt nào (BrowserAgent, "
                "ResearchAgent, AutomationAgent) nên thực hiện từng bước đó.\n"
                "QUAN TRỌNG: Chỉ trả về danh sách các bước, mỗi bước một dòng. "
                "Sử dụng định dạng: browser_search('từ khóa') hoặc đơn giản là nội dung nhiệm vụ nếu không cần công cụ cụ thể."
            )
        )
