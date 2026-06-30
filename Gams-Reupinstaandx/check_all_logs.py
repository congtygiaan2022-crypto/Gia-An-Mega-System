import sqlite3, json, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute('SELECT profile_name, status, logs_json FROM profile_logs')
rows = cursor.fetchall()
conn.close()

print(f"=== STATUS OF ALL PROFILES (Total: {len(rows)}) ===")
for name, status, logs_json in rows:
    print(f"\nProfile: {name} | Status: {status}")
    try:
        logs = json.loads(logs_json)
        print("Last 5 logs:")
        for log in logs[-5:]:
            print("  -", log)
    except Exception as e:
        print("  Error parsing logs:", e)
print("=============================================")
