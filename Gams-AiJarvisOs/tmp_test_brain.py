import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from computer.computer_brain import computer_brain

def test_brain():
    print("--- Testing Computer Brain ---")
    try:
        print("Starting brain (BrowserVision)...")
        computer_brain.start()
        
        print("Opening Google...")
        computer_brain.open_site("google.com")
        
        print("Analyzing page summary...")
        summary = computer_brain.analyze_page()
        for item in summary:
            print(f"  - {item}")
            
        print("Attempting type_text 'herbal tea'...")
        # Since Google search is usually its own input, we use general type_text
        res = computer_brain.type_text("herbal tea")
        print(f"  Result: {res}")
        
        print("Attempting to find and click 'Search'...")
        res = computer_brain.find_and_click("Search")
        print(f"  Result: {res}")
        
        print("Auto-scrolling...")
        res = computer_brain.auto_scroll("down")
        print(f"  Result: {res}")
        
        computer_brain.stop()
        print("--- Brain Test Completed ---")
    except Exception as e:
        print(f"Computer Brain error: {e}")
        try: computer_brain.stop()
        except: pass

if __name__ == "__main__":
    test_brain()
