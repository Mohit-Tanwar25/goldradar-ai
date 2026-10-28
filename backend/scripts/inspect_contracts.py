import os
import re
import csv
from datetime import datetime
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "mcx_gold_raw_data")

def detailed_audit():
    contract_files = []
    for root, dirs, files in os.walk(RAW_DIR):
        for f in files:
            if f.endswith('.csv') and f != 'download_log.csv':
                contract_files.append(os.path.join(root, f))
    
    print(f"Contract CSV files to audit: {len(contract_files)}")
    
    # 1. Check exact headers and whitespace in column names
    header_sets = set()
    col_whitespace_issues = set()
    for f in contract_files:
        with open(f, 'r', encoding='utf-8') as fp:
            reader = csv.reader(fp)
            cols = next(reader)
            header_sets.add(tuple(cols))
            for c in cols:
                if c != c.strip():
                    col_whitespace_issues.add(c)
                    
    print(f"Distinct header tuples: {len(header_sets)}")
    for h in header_sets:
        print("Header columns:", h)
    print("Column names with whitespace:", col_whitespace_issues)

    # 2. Audit rows across all files
    all_rows = []
    file_stats = []
    
    total_raw_rows = 0
    symbols_found = set()
    instruments_found = set()
    option_types_found = set()
    strike_prices_found = set()
    
    date_formats_found = set()
    expiry_formats_found = set()
    
    ohlc_issues = []
    non_positive_prices = []
    null_value_counts = {c: 0 for c in list(header_sets)[0]}
    
    # Let's inspect each file
    for f in contract_files:
        rel_path = os.path.relpath(f, RAW_DIR)
        f_size = os.path.getsize(f)
        
        # Parse CSV
        df = pd.read_csv(f, dtype=str)
        num_rows, num_cols = df.shape
        total_raw_rows += num_rows
        
        # Check missing values
        for c in df.columns:
            null_count = df[c].isna().sum() + (df[c] == '').sum()
            null_value_counts[c] += null_count
            
        # Symbols and whitespace
        for s in df['Symbol'].unique():
            symbols_found.add(s)
        for inst in df['Instrument Name'].unique():
            instruments_found.add(inst)
        for opt in df['Option Type'].unique():
            option_types_found.add(opt)
        for stk in df['Strike Price'].unique():
            strike_prices_found.add(stk)
            
        # Expiries
        for exp in df['Expiry Date'].unique():
            expiry_formats_found.add(exp)
            
        # Dates
        dates = df['Date'].tolist()
        parsed_dates = []
        for d in dates:
            # check format
            try:
                dt = datetime.strptime(d.strip(), "%d %b %Y")
                parsed_dates.append(dt)
                date_formats_found.add("%d %b %Y")
            except Exception as e:
                try:
                    dt = pd.to_datetime(d)
                    parsed_dates.append(dt)
                    date_formats_found.add("other")
                except:
                    parsed_dates.append(None)
                    date_formats_found.add("unparseable")
                    
        valid_dates = [d for d in parsed_dates if d is not None]
        min_date = min(valid_dates).strftime('%Y-%m-%d') if valid_dates else None
        max_date = max(valid_dates).strftime('%Y-%m-%d') if valid_dates else None
        
        # Filename date comparison
        # e.g. GOLDM_2024-01-01_to_2024-01-05_expiry_05JAN2024.csv
        basename = os.path.basename(f)
        m = re.search(r'_(\d{4}-\d{2}-\d{2})_to_(\d{4}-\d{2}-\d{2})_expiry_([A-Za-z0-9]+)\.csv', basename)
        fn_match = False
        fn_start, fn_end, fn_exp = None, None, None
        if m:
            fn_start, fn_end, fn_exp = m.groups()
            fn_match = (fn_start == min_date) and (fn_end == max_date)
        
        file_stats.append({
            'file': rel_path,
            'size': f_size,
            'rows': num_rows,
            'cols': num_cols,
            'min_date': min_date,
            'max_date': max_date,
            'fn_start': fn_start,
            'fn_end': fn_end,
            'fn_exp': fn_exp,
            'fn_match': fn_match,
            'symbols': list(df['Symbol'].str.strip().unique()),
            'expiries': list(df['Expiry Date'].str.strip().unique())
        })
        
        # Add to all_rows for global checks
        df['_source_file'] = rel_path
        df['_source_row_index'] = df.index + 2 # 1-based header is line 1
        all_rows.append(df)
        
    print(f"Total raw rows across all 165 contract CSVs: {total_raw_rows}")
    print(f"Unique symbols raw: {symbols_found}")
    print(f"Unique symbols stripped: {[s.strip() for s in symbols_found]}")
    print(f"Unique instruments: {instruments_found}")
    print(f"Unique Option Types: {option_types_found}")
    print(f"Unique Strike Prices: {strike_prices_found}")
    print(f"Date formats found: {date_formats_found}")
    print(f"Expiry formats sample (total {len(expiry_formats_found)}): {list(expiry_formats_found)[:10]}")
    print(f"Missing value counts across all contract files: {null_value_counts}")
    
    # Filename date mismatch check
    mismatches = [fs for fs in file_stats if not fs['fn_match']]
    print(f"Filename date mismatches: {len(mismatches)}")
    if mismatches:
        for mm in mismatches[:5]:
            print("  Mismatch:", mm['file'], "fn:", mm['fn_start'], "to", mm['fn_end'], "actual:", mm['min_date'], "to", mm['max_date'])

if __name__ == '__main__':
    detailed_audit()
