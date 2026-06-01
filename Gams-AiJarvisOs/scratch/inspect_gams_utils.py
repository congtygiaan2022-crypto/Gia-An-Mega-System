# -*- coding: utf-8 -*-
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open("plugins/lib/gams_utils.py", "r", encoding="utf-8") as f:
    content = f.read()

lines = content.splitlines()
print("--- Lines with logger, logging or print in gams_utils.py ---")
for idx, line in enumerate(lines):
    if "logger" in line or "print" in line or "logging" in line:
        print(f"Line {idx+1}: {line.strip()[:120]}")
