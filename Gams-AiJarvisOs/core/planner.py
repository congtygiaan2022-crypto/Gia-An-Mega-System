import re
from core.logger import get_module_logger

logger = get_module_logger("Planner")

class Planner:
    """
    Multi-Step Task Planner.
    Breaks down natural language like "mở google search gmail.com"
    into a sequence of executable step dictionaries.
    """
    
    def __init__(self):
        self.commands = {
            "open_google": [
                "mở google",
                "open google",
                "go to google"
            ],
            "search": [
                "search",
                "tìm ",
                "tìm kiếm "
            ],
            "open_gmail": [
                "mở gmail",
                "open gmail",
                "gmail.com"
            ],
            "open_youtube": [
                "mở youtube",
                "open youtube"
            ],
            "open_facebook": [
                "mở facebook",
                "open facebook"
            ],
            "open_first_result": [
                "mở link đầu tiên",
                "open first result",
                "click first result",
                "mở kết quả đầu tiên"
            ]
        }

    def _detect(self, text: str, patterns: list) -> bool:
        for p in patterns:
            if p in text:
                return True
        return False

    def _extract_search_query(self, text: str) -> str | None:
        # Match 'search <query> mở' or 'search <query>'
        match = re.search(r"search\s+(.+?)(?:\s+mở|\s+open|$)", text)
        if match: return match.group(1).strip()
        
        match = re.search(r"tìm\s+(.+?)(?:\s+mở|\s+open|$)", text)
        if match: return match.group(1).strip()
        
        match = re.search(r"tìm kiếm\s+(.+?)(?:\s+mở|\s+open|$)", text)
        if match: return match.group(1).strip()
        
        return None

    def create_plan(self, task: str) -> list[dict]:
        task = task.lower().strip()
        steps = []
        logger.info(f"Creating multi-step plan for: {task}")

        # 1. Open Browser phase
        if self._detect(task, self.commands["open_google"]):
            steps.append({"action": "open_browser", "url": "https://www.google.com"})
        elif self._detect(task, self.commands["open_youtube"]):
            steps.append({"action": "open_browser", "url": "https://www.youtube.com"})
        elif self._detect(task, self.commands["open_facebook"]):
            steps.append({"action": "open_browser", "url": "https://www.facebook.com"})
        else:
            # Generic domain fallback (e.g., "mở shopee.vn")
            match = re.search(r"mở\s+([a-z0-9.-]+\.[a-z]{2,})", task)
            if match and not any(self._detect(task, c) for c in [self.commands["open_gmail"]]):
                domain = match.group(1).strip()
                steps.append({"action": "open_browser", "url": f"https://{domain}"})

        # 2. Search phase
        if self._detect(task, self.commands["search"]):
            query = self._extract_search_query(task)
            if query:
                # If they didn't explicitly say "mở google" first, assume Google for search
                if not any(s["action"] == "open_browser" for s in steps):
                    steps.append({"action": "open_browser", "url": "https://www.google.com"})
                steps.append({"action": "google_search", "query": query})

        # 3. Post-search phase
        if self._detect(task, self.commands["open_first_result"]):
            steps.append({"action": "open_first_result", "args": None})

        # 4. Final direct opens (e.g. at the end of a chain)
        if self._detect(task, self.commands["open_gmail"]):
            steps.append({"action": "open_browser", "url": "https://gmail.com"})

        # Fallback if no rules matched: return the raw task as a single undefined step
        # This allows workflow_engine.py to pass it to the existing LLM Planner.
        if not steps:
            logger.info("No rules matched. Yielding to LLM fallback.")
            return []

        logger.info(f"Plan created: {steps}")
        return steps
