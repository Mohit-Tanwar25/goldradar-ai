import os
import re
import csv
from datetime import datetime
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "mcx_gold_raw_data")

def deep_audit():
    contract_files = []
    for root, dirs, files in os.walk(RAW_DIR):
        for f in files:
            if f.endswith('.csv') and f != 'download_log.csv':
                contract_files.append(os.path.join(root, f))
                
    dfs = []
    for f in contract_files:
        rel_path = os.path.relpath(f, RAW_DIR)
        df = pd.read_csv(f)
        df['_source_file'] = rel_path
        df['_source_row_index'] = df.index + 2
        dfs.append(df)
        
    full_df = pd.concat(dfs, ignore_index=True)
    print(f"Total rows in combined dataset: {len(full_df)}")
    
    # Clean whitespace for analysis while noting raw state
    full_df['Clean_Symbol'] = full_df['Symbol'].str.strip()
    full_df['Clean_Date'] = pd.to_datetime(full_df['Date'].str.strip(), format="%d %b %Y")
    full_df['Clean_Expiry'] = full_df['Expiry Date'].str.strip()
    
    # 1. Investigate the 1,985 missing Open, High, Low
    missing_ohl = full_df[full_df['Open'].isna() | full_df['High'].isna() | full_df['Low'].isna()]
    print(f"\n--- MISSING OHLC INVESTIGATION ---")
    print(f"Rows with missing Open/High/Low: {len(missing_ohl)}")
    print(f"Are Open, High, Low always missing together? {((full_df['Open'].isna() == full_df['High'].isna()) & (full_df['High'].isna() == full_df['Low'].isna())).all()}")
    print("Volume(Lots) values on missing OHLC rows:", missing_ohl['Volume(Lots)'].value_counts().to_dict())
    print("Value(Lacs) values on missing OHLC rows:", missing_ohl['Value(Lacs)'].value_counts().to_dict())
    print("Sample missing OHLC rows:\n", missing_ohl[['Clean_Date', 'Clean_Symbol', 'Clean_Expiry', 'Open', 'High', 'Low', 'Close', 'Previous Close', 'Volume(Lots)', 'Open Interest(Lots)']].head(5))
    
    # 2. Check Zero Volume rows
    print(f"\n--- VOLUME & OPEN INTEREST INVESTIGATION ---")
    zero_vol = full_df[full_df['Volume(Lots)'] == 0]
    print(f"Total rows with Volume(Lots) == 0: {len(zero_vol)}")
    print(f"Rows with Volume(Lots) == 0 that have missing Open: {zero_vol['Open'].isna().sum()}")
    print(f"Rows with Volume(Lots) == 0 that have non-missing Open: {(~zero_vol['Open'].isna()).sum()}")
    if (~zero_vol['Open'].isna()).sum() > 0:
        print("Sample zero volume rows with non-missing Open:\n", zero_vol[~zero_vol['Open'].isna()][['Clean_Date', 'Clean_Symbol', 'Clean_Expiry', 'Open', 'High', 'Low', 'Close', 'Volume(Lots)']].head())
    
    zero_oi = full_df[full_df['Open Interest(Lots)'] == 0]
    print(f"Total rows with Open Interest(Lots) == 0: {len(zero_oi)}")
    
    # Check negative or non-positive volume / OI
    neg_vol = full_df[full_df['Volume(Lots)'] < 0]
    neg_oi = full_df[full_df['Open Interest(Lots)'] < 0]
    print(f"Negative Volume rows: {len(neg_vol)}, Negative OI rows: {len(neg_oi)}")
    
    # 3. Check Price Consistency (Open, High, Low, Close, Previous Close)
    print(f"\n--- PRICE VALIDATION ---")
    traded_df = full_df.dropna(subset=['Open', 'High', 'Low', 'Close'])
    print(f"Traded rows (with full OHLC): {len(traded_df)}")
    
    # Non-positive prices
    non_pos_open = (traded_df['Open'] <= 0).sum()
    non_pos_high = (traded_df['High'] <= 0).sum()
    non_pos_low = (traded_df['Low'] <= 0).sum()
    non_pos_close = (full_df['Close'] <= 0).sum()
    non_pos_prev_close = (full_df['Previous Close'] <= 0).sum()
    print(f"Non-positive Open: {non_pos_open}, High: {non_pos_high}, Low: {non_pos_low}, Close: {non_pos_close}, Prev Close: {non_pos_prev_close}")
    
    # Consistency checks: High >= Low, High >= Open, High >= Close, Low <= Open, Low <= Close
    h_lt_l = traded_df[traded_df['High'] < traded_df['Low']]
    h_lt_o = traded_df[traded_df['High'] < traded_df['Open']]
    h_lt_c = traded_df[traded_df['High'] < traded_df['Close']]
    l_gt_o = traded_df[traded_df['Low'] > traded_df['Open']]
    l_gt_c = traded_df[traded_df['Low'] > traded_df['Close']]
    
    print(f"Inconsistencies:")
    print(f"  High < Low: {len(h_lt_l)}")
    print(f"  High < Open: {len(h_lt_o)}")
    print(f"  High < Close: {len(h_lt_c)}")
    print(f"  Low > Open: {len(l_gt_o)}")
    print(f"  Low > Close: {len(l_gt_c)}")
    
    if len(h_lt_l) > 0 or len(h_lt_o) > 0 or len(h_lt_c) > 0 or len(l_gt_o) > 0 or len(l_gt_c) > 0:
        print("Anomaly sample:\n", pd.concat([h_lt_l, h_lt_o, h_lt_c, l_gt_o, l_gt_c]).drop_duplicates())
        
    # 4. Duplicate checks
    print(f"\n--- DUPLICATE CANDIDATE CHECK ---")
    # Check within the same file
    intra_file_dups = []
    for f in contract_files:
        df = pd.read_csv(f)
        d_dups = df[df.duplicated(subset=['Date', 'Symbol', 'Expiry Date'], keep=False)]
        if len(d_dups) > 0:
            intra_file_dups.append((f, len(d_dups)))
    print(f"Files with internal duplicates: {len(intra_file_dups)}")
    
    # Check across all files
    # The primary key of market bhavcopy futures record is (Date, Symbol, Expiry Date)
    cross_dups = full_df[full_df.duplicated(subset=['Clean_Date', 'Clean_Symbol', 'Clean_Expiry'], keep=False)]
    print(f"Cross-file duplicate records on (Date, Symbol, Expiry Date): {len(cross_dups)}")
    if len(cross_dups) > 0:
        print("Sample cross duplicates:\n", cross_dups[['Clean_Date', 'Clean_Symbol', 'Clean_Expiry', '_source_file', '_source_row_index', 'Close', 'Volume(Lots)']].head(10))
        
    # Check exact row duplicates
    cols_to_check = [c for c in full_df.columns if not c.startswith('_') and not c.startswith('Clean_')]
    exact_dups = full_df[full_df.duplicated(subset=cols_to_check, keep=False)]
    print(f"Exact full-row duplicates (excluding source file tracking): {len(exact_dups)}")

    # 5. Overlapping trading dates across contracts (term structure)
    print(f"\n--- OVERLAPPING TRADING DATES (TERM STRUCTURE) ---")
    date_contracts = full_df.groupby(['Clean_Symbol', 'Clean_Date'])['Clean_Expiry'].nunique().reset_index()
    print("Contract count distribution per (Symbol, Date):")
    print(date_contracts.groupby('Clean_Symbol')['Clean_Expiry'].describe())
    max_contracts = date_contracts.groupby('Clean_Symbol')['Clean_Expiry'].max()
    print("Max concurrent expiries trading on a single date per symbol:")
    print(max_contracts)

    # 6. Symbol statistics
    print(f"\n--- SYMBOL STATISTICS ---")
    sym_summary = full_df.groupby('Clean_Symbol').agg(
        row_count=('Clean_Symbol', 'count'),
        unique_expiries=('Clean_Expiry', 'nunique'),
        min_date=('Clean_Date', 'min'),
        max_date=('Clean_Date', 'max'),
        unique_dates=('Clean_Date', 'nunique'),
        zero_vol_count=('Volume(Lots)', lambda x: (x == 0).sum()),
        missing_ohl_count=('Open', lambda x: x.isna().sum())
    )
    print(sym_summary)

if __name__ == '__main__':
    deep_audit()
