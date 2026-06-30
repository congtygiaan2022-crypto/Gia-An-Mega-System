import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print("Tables:", tables)

for t in tables:
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{t}'")
    print(f"\nSchema for {t}:")
    print(cursor.fetchone()[0])
    
    # Let's print row count
    cursor.execute(f"SELECT COUNT(*) FROM {t}")
    print("Row count:", cursor.fetchone()[0])

    # Sample rows
    cursor.execute(f"SELECT * FROM {t} LIMIT 5")
    print("Sample rows:")
    for r in cursor.fetchall():
        print(" ", r)

# Test comment for hot-reloading verification.
