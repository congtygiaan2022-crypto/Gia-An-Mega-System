import sys
import os
import time

# Add project root to path
sys.path.append(os.getcwd())

from core.agent import JavisAgent

def test_autonomous_loop():
    print("--- Testing Autonomous Loop ---")
    agent = JavisAgent()
    
    # We'll mock the planner's create_plan to avoid actual OpenAI calls during basic verification
    # or just let it run if the API key is valid.
    # To be safe for verification in this environment, we'll monkeypatch it briefly.
    
    original_create_plan = agent.planner.create_plan
    agent.planner.create_plan = lambda task: [
        "browser_open('https://www.google.com')",
        "browser_screenshot()",
        "print('Autonomous loop step executed')"
    ]
    
    try:
        task = "test autonomous search"
        print(f"Running autonomous task: {task}")
        results = agent.run_autonomous(task)
        
        print("\nResults:")
        for r in results:
            print(f"  Step: {r.get('step')}")
            print(f"  Result: {r.get('result') or r.get('error')}")
            
    except Exception as e:
        print(f"Autonomous Loop error: {e}")
    finally:
        agent.planner.create_plan = original_create_plan

    print("--- Autonomous Loop Test Completed ---")

if __name__ == "__main__":
    test_autonomous_loop()
