"""
main.py — Jarvis v2 entry point
Usage:
  python main.py          → interactive CLI (simple mode)
  python main.py --web    → full web dashboard (requires uvicorn)
"""
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_cli():
    """Simple interactive CLI: User → LLM → Report"""
    from core.agent import jarvis

    print("\n" + "=" * 50)
    print("  JARVIS v2  |  Local AI (Ollama)")
    print("  Commands: 'save <task>' to save as report")
    print("  Type 'exit' to quit")
    print("=" * 50 + "\n")

    while True:
        try:
            task = input("Jarvis > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break

        if not task:
            continue
        if task.lower() == "exit":
            break

        if task.lower().startswith("save "):
            # Save result as report file
            actual_task = task[5:].strip()
            result = jarvis.run_and_save(actual_task)
        else:
            result = jarvis.run(task)

        print(f"\n{result}\n")


def free_port(port):
    """
    Finds and kills any processes holding the specified port to prevent bind errors on startup.
    """
    import os
    import subprocess
    import sys
    import time
    
    print(f"Checking if port {port} is already in use...")
    try:
        if sys.platform == "win32":
            cmd = "netstat -ano"
            output = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
            pids = set()
            for line in output.splitlines():
                if f":{port} " in line or f":{port}\t" in line:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        pid_str = parts[-1]
                        if pid_str.isdigit():
                            pids.add(int(pid_str))
            
            my_pid = os.getpid()
            for pid in pids:
                if pid != my_pid and pid > 0:
                    print(f"Port {port} is occupied by PID {pid}. Terminating process tree...")
                    try:
                        subprocess.run(f"taskkill /F /PID {pid} /T", shell=True, capture_output=True)
                        time.sleep(1.0)
                    except Exception as e:
                        print(f"Failed to kill process {pid}: {e}")
        else:
            try:
                cmd = f"lsof -t -i:{port}"
                output = subprocess.check_output(cmd, shell=True).decode('utf-8')
                pids = [int(p.strip()) for p in output.splitlines() if p.strip().isdigit()]
                my_pid = os.getpid()
                for pid in pids:
                    if pid != my_pid:
                        print(f"Port {port} is occupied by PID {pid}. Killing...")
                        os.kill(pid, 9)
                        time.sleep(1.0)
            except:
                pass
    except Exception as e:
        print(f"Error checking/freeing port {port}: {e}")

def run_web():
    """Launch the full web dashboard."""
    free_port(8080)
    import threading
    import time
    import webbrowser
    import uvicorn

    # Logic khởi chạy các dịch vụ (AutonomousEngine, Scheduler, Bridge) 
    # đã được chuyển vào ui/server.py (@app.on_event("startup"))
    # để đảm bảo tính duy nhất và ổn định của hệ thống.

    def open_browser():
        time.sleep(2.5) # Chờ server startup xong
        webbrowser.open("http://127.0.0.1:8080")

    threading.Thread(target=open_browser, daemon=True).start()

    print("\n" + "=" * 50)
    print("  JARVIS OS  |  Web Dashboard")
    print("  http://127.0.0.1:8080")
    print("=" * 50 + "\n")

    uvicorn.run("ui.server:app", host="127.0.0.1", port=8080, reload=False)


if __name__ == "__main__":
    if "--web" in sys.argv:
        run_web()
    else:
        run_cli()
