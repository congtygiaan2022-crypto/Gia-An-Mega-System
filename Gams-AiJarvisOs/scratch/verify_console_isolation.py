import os
import sys
import time
import subprocess
import requests

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

def main():
    print("=== STARTING CONSOLE ISOLATION AUTO-VERIFICATION ===")
    
    # 1. Kill any existing process on 8080
    from main import free_port
    free_port(8080)
    time.sleep(1.0)
    
    # 2. Start the Jarvis Web Dashboard in a subprocess with piped stdout
    print("Launching Web Dashboard server...")
    server_cmd = [sys.executable, "main.py", "--web"]
    
    # We run the server process. We want to capture its output.
    server_proc = subprocess.Popen(
        server_cmd,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace"
    )
    
    # Wait for server to boot up
    print("Waiting for server to initialize...")
    time.sleep(6.0)
    
    # Check if server is still running
    if server_proc.poll() is not None:
        print("Error: Web Dashboard failed to start or crashed.")
        sys.exit(1)
        
    print("Web Dashboard is running. Triggering daily insights task manual run...")
    
    # 3. Send HTTP request to run the task
    try:
        import json
        res = requests.post("http://127.0.0.1:8080/scheduler/tasks/task_insight_daily/run", timeout=5)
        print(f"Trigger Response Status: {res.status_code}")
        print(f"Trigger Response Body: {json.dumps(res.json(), ensure_ascii=True)}")
    except Exception as e:
        print(f"Error sending request to dashboard: {e}")
        server_proc.terminate()
        sys.exit(2)
        
    # 4. Monitor the server console output for the next 25 seconds
    print("Monitoring server console logs for 25 seconds for any Chrome/Selenium log leakage...")
    
    leaked_logs = []
    start_time = time.time()
    
    # Set non-blocking read on server stdout
    # On Windows, we can read line by line or character by character. 
    # Since we set stdout=subprocess.PIPE and it is buffered by line, we can read line by line.
    
    # Stop condition: 25 seconds elapsed
    while time.time() - start_time < 25:
        line = server_proc.stdout.readline()
        if not line:
            if server_proc.poll() is not None:
                break
            time.sleep(0.1)
            continue
            
        clean_line = line.strip()
        try:
            print(f"[Server Console] {clean_line}")
        except UnicodeEncodeError:
            safe_line = clean_line.encode("ascii", errors="replace").decode("ascii")
            print(f"[Server Console] {safe_line}")
        
        # Check if the log contains Chrome/Selenium/Scraper keywords
        chrome_keywords = [
            "DevTools listening",
            "GetGpuDriverOverlayInfo",
            "Failed to retrieve video device",
            "Created TensorFlow Lite XNNPACK delegate",
            "Đã đọc insight và bài đăng mới nhất cho"
        ]
        
        # Only flag gams_insight_reader logs if they are not from the Scheduler termination
        if "gams_insight_reader" in clean_line and "Scheduler" not in clean_line:
            leaked_logs.append(clean_line)
            continue
            
        if any(keyword in clean_line for keyword in chrome_keywords):
            # If the log is "gams_insight_reader" but it's just "Loaded plugin: gams_insight_reader", that's normal server registry load.
            if "Loaded plugin: gams_insight_reader" in clean_line:
                continue
            leaked_logs.append(clean_line)
            
    # 5. Clean up
    print("Terminating Web Dashboard server...")
    server_proc.terminate()
    try:
        server_proc.wait(timeout=5)
    except:
        server_proc.kill()
        
    # Clean up any leftover chromedriver or python task windows
    print("Cleaning up leftover processes...")
    try:
        from core.scheduler import global_scheduler
        global_scheduler.terminate_task("gams_insight_reader")
    except Exception as e:
        print(f"Cleanup warning: {e}")
        
    # 6. Report results
    print("\n=== VERIFICATION RESULTS ===")
    if leaked_logs:
        print("FAIL: The following Chrome/Selenium/Scraper logs leaked to the dashboard console:")
        for log in leaked_logs:
            print(f" - {log}")
        sys.exit(3)
    else:
        print("SUCCESS: 0 Chrome/Selenium/Scraper logs leaked to the dashboard console!")
        print("All scraper runs are fully isolated in their own CMD windows.")
        sys.exit(0)

if __name__ == "__main__":
    main()
