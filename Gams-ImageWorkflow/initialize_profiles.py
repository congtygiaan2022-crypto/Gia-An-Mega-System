import sqlite3
import json

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Get Yui Hatano's config
cursor.execute("SELECT config_json FROM profile_settings WHERE profile_name = 'Yui Hatano'")
row = cursor.fetchone()
if row:
    yui_config = json.loads(row[0])
    print("Yui Hatano config found.")
    
    # Configure Saitou Arimi
    saitou_config = yui_config.copy()
    # Let's adjust paths to use unique text/image folders if needed, or keep the same ones
    saitou_config['output_txt_dir'] = yui_config['output_txt_dir'].replace('Yui Hatano', 'Saitou Arimi')
    
    # Configure Profile_1
    profile1_config = yui_config.copy()
    profile1_config['output_txt_dir'] = yui_config['output_txt_dir'].replace('Yui Hatano', 'Profile_1')
    
    # Insert or replace in DB
    cursor.execute("INSERT OR REPLACE INTO profile_settings (profile_name, config_json) VALUES (?, ?)", 
                   ('Saitou Arimi', json.dumps(saitou_config, ensure_ascii=False)))
    cursor.execute("INSERT OR REPLACE INTO profile_settings (profile_name, config_json) VALUES (?, ?)", 
                   ('Profile_1', json.dumps(profile1_config, ensure_ascii=False)))
    
    # Also update their status in logs to 'Idle' so they can run
    cursor.execute("INSERT OR REPLACE INTO profile_logs (profile_name, status, logs_json) VALUES (?, 'Idle', '[]')", ('Saitou Arimi',))
    cursor.execute("INSERT OR REPLACE INTO profile_logs (profile_name, status, logs_json) VALUES (?, 'Idle', '[]')", ('Profile_1',))
    
    conn.commit()
    print("Successfully initialized configs and logs for Saitou Arimi and Profile_1.")
else:
    print("Error: Yui Hatano config not found!")

conn.close()
