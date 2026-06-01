import json
import os
import re
import sys
import datetime

# Set encoding for output to UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

def standardize_date(date_str):
    if not date_str:
        return ""
    
    s = date_str.strip()
    s_clean = re.sub(r'\s+', ' ', s).lower()

    # Remove day of week to avoid relative time conflicts (e.g. "thứ 3 ngày 6" -> "ngày 6")
    s_clean = re.sub(r'\bthứ\s+\d+\b', '', s_clean)
    s_clean = re.sub(r'\bthứ\s+(?:hai|ba|tư|năm|sáu|bảy)\b', '', s_clean)
    s_clean = re.sub(r'\bchủ\s+nhật\b', '', s_clean)

    now = datetime.datetime.now()
    year = now.year

    # Check relative hours
    m = re.search(r'(\d+)\s*(?:giờ|h|hrs|hours?)\b', s_clean)
    if m:
        h = int(m.group(1))
        val = now - datetime.timedelta(hours=h)
        return val.strftime("%H:%M %d/%m/%Y")

    # Check relative days
    m = re.search(r'(\d+)\s*(?:ngày|d|days?)\b', s_clean)
    if m:
        d = int(m.group(1))
        val = now - datetime.timedelta(days=d)
        return val.strftime("%H:%M %d/%m/%Y")

    if any(k in s_clean for k in ["vừa xong", "vừa mới", "just now", "vài giây"]):
        return now.strftime("%H:%M %d/%m/%Y")

    # Extract time
    time_match = re.search(r'(\d{1,2}):(\d{2})', s_clean)
    hours = 0
    mins = 0
    if time_match:
        hours = int(time_match.group(1))
        mins = int(time_match.group(2))
        if "pm" in s_clean and hours < 12:
            hours += 12
        if "am" in s_clean and hours == 12:
            hours = 0

    # Extract year
    yr_match = re.search(r'\b(20\d{2})\b', s_clean)
    if yr_match:
        year = int(yr_match.group(1))

    # Extract month
    months_en = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    month = now.month
    
    m_vn = re.search(r'(?:tháng|thg)\s*(\d{1,2})', s_clean)
    if m_vn:
        month = int(m_vn.group(1))
    else:
        for idx, m_en in enumerate(months_en):
            if m_en in s_clean:
                month = idx + 1
                break

    # Extract day
    day = now.day
    s_temp = s_clean
    if yr_match:
        s_temp = s_temp.replace(yr_match.group(1), "")
    if time_match:
        s_temp = s_temp.replace(time_match.group(0), "")
        
    m_vn_full = re.search(r'(?:tháng|thg)\s*\d{1,2}', s_temp)
    if m_vn_full:
        s_temp = s_temp.replace(m_vn_full.group(0), "")
    else:
        for m_en in months_en:
            s_temp = s_temp.replace(m_en, "")
            
    day_match = re.search(r'\b(\d{1,2})\b', s_temp)
    if day_match:
        day = int(day_match.group(1))
    else:
        all_nums = re.findall(r'\b(\d{1,2})\b', s_clean)
        for num in all_nums:
            val = int(num)
            if 1 <= val <= 31 and val != month:
                day = val
                break

    try:
        # If we got a weird "06 Tháng 3:23" -> month=3, day=6, hours=3, mins=23. Year=2026.
        dt = datetime.datetime(year, month, day, hours, mins)
        if dt > now and not yr_match:
            dt = dt.replace(year=year - 1)
        return dt.strftime("%H:%M %d/%m/%Y")
    except:
        return s

links_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plugins', 'data', 'gams_insight', 'links.json')

if os.path.exists(links_path):
    with open(links_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    found_changes = False
    for item in data:
        if 'latest_post_date' in item:
            old = item['latest_post_date']
            # Only clean if not already in the correct format HH:MM DD/MM/YYYY
            if old and not re.match(r'^\d{2}:\d{2}\s+\d{2}/\d{2}/\d{4}$', old):
                new = standardize_date(old)
                if old != new:
                    item['latest_post_date'] = new
                    found_changes = True
    
    if found_changes:
        with open(links_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print("links.json cleanup complete.")
    else:
        print("No changes needed in links.json.")
else:
    print(f"links.json not found at {links_path}")
