import os
import glob
import re
import csv
from datetime import datetime
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")

def find_all_files(base_dir):
    all_files = []
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            all_files.append(os.path.join(root, f))
    return sorted(all_files)

def inspect():
    files = find_all_files(RAW_DIR)
    print(f"Total files discovered: {len(files)}")
    
    # Separate CSVs and other files
    csv_files = [f for f in files if f.endswith('.csv')]
    other_files = [f for f in files if not f.endswith('.csv')]
    
    print(f"CSV files: {len(csv_files)}")
    print(f"Other files: {len(other_files)} ({other_files})")
    
    # Check headers
    schemas = {}
    for f in csv_files:
        rel_path = os.path.relpath(f, RAW_DIR)
        with open(f, 'r', encoding='utf-8', errors='replace') as fp:
            first_line = fp.readline().strip()
            schemas.setdefault(first_line, []).append(rel_path)
            
    print(f"\nUnique CSV Headers found: {len(schemas)}")
    for header, flist in schemas.items():
        print(f"Header ({len(flist)} files): {header[:120]}...")
        if len(flist) <= 5:
            print(f"  Files: {flist}")
        else:
            print(f"  Sample files: {flist[:3]}")

if __name__ == '__main__':
    inspect()
