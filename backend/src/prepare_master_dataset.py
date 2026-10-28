"""
Gold Contract Radar — Master Dataset Preparation Pipeline
Phase 2: Standardizing, Validating, and Building mcx_gold_master.csv

This script reads the 165 audited MCX gold futures CSV files, standardizes schemas,
parses dates explicitly, applies data quality flags, retains original quotation units,
preserves full source traceability, and outputs the deterministic master dataset.
"""

import os
import sys
import re
import csv
import json
from datetime import datetime
import pandas as pd
import numpy as np

# Resolve base directories
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "mcx_gold_raw_data")
PROCESSED_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
INVENTORY_PATH = os.path.join(PROJECT_ROOT, "reports", "file_inventory.csv")
MASTER_OUTPUT_PATH = os.path.join(PROCESSED_DATA_DIR, "mcx_gold_master.csv")

def verify_source_files_against_inventory():
    """Verify that the 165 market CSV files exactly match the Phase 1 audit inventory."""
    if not os.path.exists(INVENTORY_PATH):
        raise FileNotFoundError(f"Audit inventory not found at: {INVENTORY_PATH}")
    
    inv_df = pd.read_csv(INVENTORY_PATH)
    # Market files are those marked SUCCESS and not download_log or extraction_summary
    market_inv = inv_df[inv_df['parsing_status'] == 'SUCCESS'].copy()
    expected_files = set(
        os.path.normpath(p).replace('\\', '/') 
        for p in market_inv['filename']
    )
    
    # Discover actual market files on disk
    actual_files = set()
    for root, dirs, files in os.walk(RAW_DATA_DIR):
        for f in files:
            if f.endswith('.csv') and f != 'download_log.csv':
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, PROJECT_ROOT)
                norm_rel = os.path.normpath(rel_path).replace('\\', '/')
                actual_files.add(norm_rel)
                
    if len(expected_files) != 165:
        raise ValueError(f"Expected 165 market files in inventory, found {len(expected_files)}")
    if len(actual_files) != 165:
        raise ValueError(f"Expected 165 actual market files on disk, found {len(actual_files)}")
        
    diff = expected_files.symmetric_difference(actual_files)
    if diff:
        raise ValueError(f"Discrepancy between audit inventory and disk files ({len(diff)} mismatched): {diff}")
        
    print(f"Verified 165 audited market files match audit inventory exactly (0 mismatches).")
    return sorted(list(actual_files))

def parse_float_or_nan(val):
    """Convert value to float, preserving NaN without converting to 0."""
    if pd.isna(val) or val is None:
        return np.nan
    s = str(val).strip()
    if s == '' or s == '-' or s.lower() == 'nan':
        return np.nan
    try:
        return float(s)
    except ValueError as e:
        raise ValueError(f"Cannot parse float from '{val}': {e}")

def parse_int_or_nan(val):
    """Convert value to integer or NaN."""
    if pd.isna(val) or val is None:
        return np.nan
    s = str(val).strip()
    if s == '' or s == '-' or s.lower() == 'nan':
        return np.nan
    try:
        # float first to handle cases like "84.0"
        return int(float(s))
    except ValueError as e:
        raise ValueError(f"Cannot parse int from '{val}': {e}")

def prepare_master_dataset():
    """Main function to ingest, standardize, flag, and output master dataset."""
    print("=" * 60)
    print("Gold Contract Radar — Master Dataset Preparation Pipeline")
    print("=" * 60)
    
    file_list = verify_source_files_against_inventory()
    
    all_records = []
    duplicate_rows = []
    
    total_files_read = 0
    total_rows_read = 0
    
    # Load active contract universe from configuration
    CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "contract_specs.json")
    active_contracts = None
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            specs_cfg = json.load(f)
            active_contracts = set(specs_cfg.get("active_contracts", []))
    if active_contracts:
        print(f"Applying active contract universe filter: {sorted(list(active_contracts))}")

    for rel_file in file_list:
        full_path = os.path.join(PROJECT_ROOT, rel_file)
        total_files_read += 1
        
        # Read raw CSV with string types to inspect every byte
        with open(full_path, 'r', encoding='utf-8') as fp:
            reader = csv.DictReader(fp)
            
            # Clean column headers
            fieldnames = [c.strip() for c in reader.fieldnames]
            
            row_idx = 1 # 1-based header is row 1, data starts row 2
            for raw_row in reader:
                row_idx += 1
                total_rows_read += 1
                
                # Strip keys and values
                clean_row = {k.strip(): (v.strip() if v is not None else '') for k, v in raw_row.items()}
                
                clean_symbol = clean_row.get('Symbol', '').strip()
                if active_contracts and clean_symbol not in active_contracts:
                    continue

                raw_date = clean_row.get('Date', '')
                raw_symbol = raw_row.get('Symbol', '') # keep original padded
                raw_expiry = clean_row.get('Expiry Date', '')
                instrument_name = clean_row.get('Instrument Name', '')
                option_type = clean_row.get('Option Type', '')
                raw_strike = clean_row.get('Strike Price', '')
                
                raw_open = clean_row.get('Open', '')
                raw_high = clean_row.get('High', '')
                raw_low = clean_row.get('Low', '')
                raw_close = clean_row.get('Close', '')
                raw_prev_close = clean_row.get('Previous Close', '')
                raw_vol_lots = clean_row.get('Volume(Lots)', '')
                raw_vol_000s = raw_row.get("Volume(In 000's)", '') # retain exact unit string
                raw_value_lacs = clean_row.get('Value(Lacs)', '')
                raw_oi_lots = clean_row.get('Open Interest(Lots)', '')
                
                # Explicit date parsing
                ambiguous_date_flag = False
                parsed_trade_date = None
                parsed_expiry_date = None
                
                try:
                    dt = datetime.strptime(raw_date, "%d %b %Y")
                    parsed_trade_date = dt.strftime("%Y-%m-%d")
                except Exception:
                    ambiguous_date_flag = True
                    
                try:
                    exp_dt = datetime.strptime(raw_expiry, "%d%b%Y")
                    parsed_expiry_date = exp_dt.strftime("%Y-%m-%d")
                except Exception:
                    ambiguous_date_flag = True
                    
                # Explicit numeric conversion without silent zero coercion
                strike_price = parse_float_or_nan(raw_strike)
                open_px = parse_float_or_nan(raw_open)
                high_px = parse_float_or_nan(raw_high)
                low_px = parse_float_or_nan(raw_low)
                close_px = parse_float_or_nan(raw_close)
                prev_close_px = parse_float_or_nan(raw_prev_close)
                
                vol_lots = parse_int_or_nan(raw_vol_lots)
                value_lacs = parse_float_or_nan(raw_value_lacs)
                oi_lots = parse_int_or_nan(raw_oi_lots)
                
                # Trading flag based on Volume(Lots) > 0
                is_traded = bool(vol_lots is not None and not np.isnan(vol_lots) and vol_lots > 0)
                
                # Quality flags
                flag_missing_ohlc = bool(np.isnan(open_px) or np.isnan(high_px) or np.isnan(low_px))
                flag_zero_volume = bool(vol_lots == 0)
                flag_zero_oi = bool(oi_lots == 0)
                
                # Invalid price check (<= 0 on any populated price)
                flag_invalid_price = False
                for px in [open_px, high_px, low_px, close_px, prev_close_px]:
                    if not np.isnan(px) and px <= 0:
                        flag_invalid_price = True
                        break
                        
                # OHLC consistency check
                flag_ohlc_inconsistent = False
                if is_traded and not flag_missing_ohlc:
                    if (high_px < low_px) or (high_px < open_px) or (high_px < close_px) or \
                       (low_px > open_px) or (low_px > close_px):
                        flag_ohlc_inconsistent = True
                        
                # Contract key
                contract_key = f"{clean_symbol}_{raw_expiry}"
                
                record = {
                    'date': parsed_trade_date,
                    'expiry_date': parsed_expiry_date,
                    'raw_date': raw_date,
                    'raw_expiry_date': raw_expiry,
                    'symbol': clean_symbol,
                    'raw_symbol': raw_symbol,
                    'contract_key': contract_key,
                    'instrument_name': instrument_name,
                    'option_type': option_type,
                    'strike_price': strike_price,
                    'open': open_px,
                    'high': high_px,
                    'low': low_px,
                    'close': close_px,
                    'previous_close': prev_close_px,
                    'volume_lots': vol_lots,
                    'volume_in_thousands_raw': raw_vol_000s.strip(),
                    'value_lacs': value_lacs,
                    'open_interest_lots': oi_lots,
                    'is_traded': is_traded,
                    'flag_missing_ohlc': flag_missing_ohlc,
                    'flag_zero_volume': flag_zero_volume,
                    'flag_zero_open_interest': flag_zero_oi,
                    'flag_invalid_price': flag_invalid_price,
                    'flag_ohlc_inconsistent': flag_ohlc_inconsistent,
                    'flag_ambiguous_date': ambiguous_date_flag,
                    'source_file': rel_file,
                    'source_row': row_idx
                }
                all_records.append(record)
                
    print(f"Imported {total_rows_read} rows across {total_files_read} files (Retained {len(all_records)} active rows).")
    
    df_master = pd.DataFrame(all_records)
    
    # Check for duplicate keys: (Date, Symbol, Expiry Date)
    dup_mask = df_master.duplicated(subset=['date', 'symbol', 'expiry_date'], keep=False)
    if dup_mask.any():
        dup_df = df_master[dup_mask]
        print(f"CRITICAL WARNING: Found {len(dup_df)} duplicate records on (date, symbol, expiry_date)!")
        dup_output = os.path.join(PROJECT_ROOT, "reports", "master_duplicate_investigation.csv")
        dup_df.to_csv(dup_output, index=False)
        print(f"Saved duplicates for investigation to {dup_output}")
    else:
        print("Duplicate check passed: 0 duplicate keys on (date, symbol, expiry_date).")
        
    # Sort deterministically: symbol, expiry_date, date
    df_master = df_master.sort_values(
        by=['symbol', 'expiry_date', 'date', 'source_file', 'source_row'],
        ascending=[True, True, True, True, True]
    ).reset_index(drop=True)
    
    # Save master dataset
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    df_master.to_csv(MASTER_OUTPUT_PATH, index=False)
    print(f"Master dataset successfully created at: {MASTER_OUTPUT_PATH}")
    print(f"Master dataset shape: {df_master.shape} ({df_master.shape[0]} rows, {df_master.shape[1]} columns)")
    
    # Expected count verification
    expected_rows = 11968 if active_contracts else 16195
    expected_zero_vol = 146 if active_contracts else 1985
    if len(df_master) != expected_rows:
        print(f"DISCREPANCY: Expected {expected_rows} rows, got {len(df_master)} rows!")
    else:
        print(f"Row count exactly matches expected baseline: {expected_rows} rows.")
        
    zero_vol_count = df_master['flag_zero_volume'].sum()
    if zero_vol_count != expected_zero_vol:
        print(f"DISCREPANCY: Expected {expected_zero_vol} zero-volume rows, got {zero_vol_count}!")
    else:
        print(f"Zero-volume count exactly matches expected baseline: {expected_zero_vol} rows.")
        
    return df_master

if __name__ == '__main__':
    prepare_master_dataset()
