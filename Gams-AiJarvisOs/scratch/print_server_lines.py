# -*- coding: utf-8 -*-
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open("ui/server.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i in range(1069, min(1110, len(lines))):
    print(f"{i+1}: {lines[i]}", end="")
