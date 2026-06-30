import psutil, sys
sys.stdout.reconfigure(encoding='utf-8')

print("=== DETECTING CHROME PROCESSES ===")
for proc in psutil.process_iter(['pid', 'name']):
    try:
        if proc.info['name'] and 'chrome' in proc.info['name'].lower():
            pid = proc.pid
            try:
                cmdline = proc.cmdline()
                print(f"PID {pid}: cmdline={cmdline}")
            except psutil.AccessDenied:
                print(f"PID {pid}: AccessDenied")
            except Exception as e:
                print(f"PID {pid}: Error: {e}")
    except Exception as e:
        pass
print("==================================")
