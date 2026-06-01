from bs4 import BeautifulSoup

class ScreenReader:
    def analyze_dom(self, dom_content: str):
        """
        Parses DOM to find interesting elements like buttons, inputs, links.
        """
        soup = BeautifulSoup(dom_content, "html.parser")
        
        elements = {
            "buttons": [],
            "inputs": [],
            "links": []
        }
        
        # Simple extraction
        for btn in soup.find_all(["button", "a"], class_=True):
            elements["buttons"].append({
                "text": btn.get_text().strip(),
                "class": btn.get("class"),
                "id": btn.get("id")
            })
            
        for inp in soup.find_all("input"):
            elements["inputs"].append({
                "name": inp.get("name"),
                "placeholder": inp.get("placeholder"),
                "id": inp.get("id")
            })
            
        return elements

# Global instance
screen_reader = ScreenReader()
