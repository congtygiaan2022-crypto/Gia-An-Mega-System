import sqlite3, json, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute('SELECT profile_name, status, logs_json FROM profile_logs')
rows = cursor.fetchall()
conn.close()

for name, status, logs_json in rows:
    if name in ["Yui Hatano", "Saitou Arimi", "Akiho Yoshizawa"]:
        print(f"\n================== {name} ({status}) ==================")
        try:
            logs = json.loads(logs_json)
            # Print last 25 lines
            for log in logs[-25:]:
                print(log)
        except Exception as e:
            print("Error:", e)
print("====================================================")
