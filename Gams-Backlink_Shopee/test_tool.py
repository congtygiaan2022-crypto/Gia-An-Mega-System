#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
os.environ["PYTHONIOENCODING"] = "utf-8"
"""Test nhanh bang cach chay main tool tren 6 links dau tien"""

import sys
import shutil
from pathlib import Path

# Import backlink_tool
import backlink_tool as bt

BASE_DIR = Path(__file__).parent

# Tao file input test chi chua 6 link dau
input_orig = BASE_DIR / "Link_shopee.txt"
input_test = BASE_DIR / "test_input_links.txt"
output_test = BASE_DIR / "test_ket_qua.txt"

# Xoa file ket qua cu neu co
output_test.unlink(missing_ok=True)

# Ghi 6 link dau tien tu file goc vao file test
with open(input_orig, "r", encoding="utf-8") as f_in:
    lines = [f_in.readline() for _ in range(6)]

with open(input_test, "w", encoding="utf-8") as f_out:
    for line in lines:
        if line.strip():
            f_out.write(line)

print(f"Da tao file link test: {input_test}")

# Cấu hình tham số test
bt.INPUT_FILE = "test_input_links.txt"
bt.OUTPUT_FILE = "test_ket_qua.txt"
bt.NUM_THREADS = 2
bt.HEADLESS = False  # Chạy Chrome nổi để dễ quan sát

print("\n--- KHOI CHAY TEST TOOL MAIN FLOW ---")
try:
    bt.main()
finally:
    # Xoa file link test tam thoi
    input_test.unlink(missing_ok=True)

# Doc va in ket qua
print(f"\n=== KET QUA LUU TRONG FILE {bt.OUTPUT_FILE} ===")
if output_test.exists():
    with open(output_test, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if content:
            for line in content.split("\n"):
                try:
                    print(line)
                except UnicodeEncodeError:
                    print(line.encode("ascii", errors="replace").decode("ascii"))
        else:
            print("(File rong)")
else:
    print("(Khong tim thay file ket qua)")

print("\n[OK] Test hoan tat!\n")
