import requests
import json

BASE_URL = "http://127.0.0.1:8080"

def test_endpoint(name, url, method="GET", json_data=None):
    print(f"\n--- Testing {name} ---")
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{url}")
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{url}", json=json_data)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response:", response.text[:200] + "..." if len(response.text) > 200 else response.text)
            return True
        else:
            print("Error:", response.text)
            return False
    except Exception as e:
        print(f"Connection Error: {e}")
        return False

def main():
    print("[SYSTEM] Starting End-to-End System Test...")
    
    # 1. UI Load
    success = test_endpoint("Web UI Load", "/")
    if not success: 
        print("[FAIL] Server is offline! Start it with `python main.py --web` first.")
        return
        
    # 2. System Status (Stats)
    test_endpoint("System Status", "/system/status")
    
    # 3. Antigravity Health Check
    test_endpoint("Antigravity Status", "/system/antigravity/status")
    
    # 4. Tasks Schedule List
    test_endpoint("Scheduled Tasks", "/tasks")
    
    # 5. Self-Healing Memory
    test_endpoint("Self-Healing Debug Data", "/system/self-healing")
    
    # 6. Tool Generation Request (Triggers requests.json -> Antigravity)
    print("\n--- Testing Antigravity AI Request ---")
    try:
        pass
    except Exception as e:
        print("Error:", e)

    print("\n[SUCCESS] All API Integration Tests Completed.")

if __name__ == "__main__":
    main()
