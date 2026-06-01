# -*- coding: utf-8 -*-
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open("ui/advanced_dashboard.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

def print_range(start, end):
    print(f"\n--- Lines {start} to {end} ---")
    for i in range(start-1, min(end, len(lines))):
        print(f"{i+1}: {lines[i]}", end="")

print_range(3052, 3100)
