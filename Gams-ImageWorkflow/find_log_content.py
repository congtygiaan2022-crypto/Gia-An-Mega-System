import os, sys
sys.stdout.reconfigure(encoding='utf-8')

# Search in workspace
print("=== SEARCHING IN WORKSPACE ===")
for root, dirs, files in os.walk('.'):
    for f in files:
        if f.endswith('.log') or f.endswith('.txt') or f.endswith('.jsonl'):
            filepath = os.path.join(root, f)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                    content = file.read()
                if "Đã tải ảnh lên thành công (qua Menu)!" in content:
                    print(f"FOUND IN WORKSPACE: {filepath}")
            except Exception:
                pass

# Search in tasks directory
tasks_dir = r'C:\Users\admin\.gemini\antigravity\brain\15650342-fb81-4c61-a2b1-1004ae05f7aa\.system_generated\tasks'
print("\n=== SEARCHING IN TASKS DIR ===")
if os.path.exists(tasks_dir):
    for f in os.listdir(tasks_dir):
        filepath = os.path.join(tasks_dir, f)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
            if "Đã tải ảnh lên thành công (qua Menu)!" in content:
                print(f"FOUND IN TASKS DIR: {filepath}")
        except Exception:
            pass
print("=============================")
