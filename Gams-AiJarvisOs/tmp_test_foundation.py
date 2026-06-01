import sys
import os
import time

# Add project root to path
sys.path.append(os.getcwd())

from computer.computer_engine import computer_engine
from core.self_repair import repair

def test_flow():
    print("--- Testing Computer Engine ---")
    try:
        # Check if playwright is installed by attempting to start
        res = computer_engine.start_browser()
        print(res)
        res = computer_engine.open_url("google.com")
        print(res)
        computer_engine.stop()
    except Exception as e:
        print(f"Computer Engine error (ensure playwright is installed): {e}")

    print("\n--- Testing Self Repair ---")
    def faulty_func():
        print("Executing faulty function...")
        # We catch NameError in repair.py and restart. 
        # For testing we can use a non-critical error to see the handle logic.
        raise ValueError("Simulated handled error")

    res = repair.repair_loop(faulty_func)
    print(f"Repair result: {res}")

if __name__ == "__main__":
    test_flow()
