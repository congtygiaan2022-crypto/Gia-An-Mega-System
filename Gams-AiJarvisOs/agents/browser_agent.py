from agents.base_agent import BaseAgent

class BrowserAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="BrowserAgent",
            instructions=(
                "Bạn chuyên về tương tác với trang web. "
                "Bạn có khả năng thị giác và có thể trích xuất dữ liệu từ các trang web. "
                "Bạn quyết định nên nhấp vào đâu, nhập gì và tìm kiếm những gì."
            )
        )
