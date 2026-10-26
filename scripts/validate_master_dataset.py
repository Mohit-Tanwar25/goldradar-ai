"""
Master Dataset Comprehensive Validation Script
Validates the generated master dataset (data/processed/mcx_gold_master.csv)
against all Phase 2 criteria and the Phase 1 baseline.
"""

import os
import csv
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER_CSV = os.path.join(PROJECT_ROOT, "data", "processed", "mcx_gold_master.csv")
INVENTORY_CSV = os.path.join(PROJECT_ROOT, "reports", "file_inventory.csv")
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "mcx_gold_raw_data")

def run_validations():
    print("=" * 70)
    print("VALIDATING MASTER DATASET: data/processed/mcx_gold_master.csv")
    print("=" * 70)
    
    if not os.path.exists(MASTER_CSV):
        raise FileNotFoundError(f"Master dataset missing: {MASTER_CSV}")
        
    # Read master dataset
    df = pd.read_csv(MASTER_CSV)
    print(f"Loaded master dataset: {len(df)} rows, {len(df.columns)} columns.")
    
    # 1. Number of source files imported
    unique_sources = df['source_file'].nunique()
    print(f"\n1. Source files imported: {unique_sources} (Expected: 165)")
    assert unique_sources == 165, f"Expected 165 source files, got {unique_sources}"
    
    # 2. Total imported rows and row counts by symbol
    print(f"\n2. Total imported rows: {len(df)} (Expected: 16,195)")
    assert len(df) == 16195, f"Expected 16195 rows, got {len(df)}"
    
    sym_counts = df['symbol'].value_counts().to_dict()
    print("   Row counts by symbol:", sym_counts)
    expected_sym_counts = {
        'GOLD': 4227,
        'GOLDGUINEA': 3454,
        'GOLDPETAL': 3454,
        'GOLDM': 3012,
        'GOLDTEN': 2048
    }
    for sym, exp_count in expected_sym_counts.items():
        act_count = sym_counts.get(sym, 0)
        assert act_count == exp_count, f"Symbol {sym}: expected {exp_count}, got {act_count}"
    print("   All symbol row counts match Phase 1 baseline perfectly.")
    
    # 3. Min and Max trading dates per symbol
    print("\n3. Trading date ranges per symbol:")
    for sym, grp in df.groupby('symbol'):
        min_d = grp['date'].min()
        max_d = grp['date'].max()
        unique_dates = grp['date'].nunique()
        print(f"   {sym:12s}: {min_d} to {max_d} ({unique_dates} trading days)")
        if sym == 'GOLDTEN':
            assert min_d == '2025-03-31', f"GOLDTEN expected 2025-03-31, got {min_d}"
            assert max_d == '2026-10-22', f"GOLDTEN expected 2026-10-22, got {max_d}"
            assert unique_dates == 403, f"GOLDTEN expected 403 days, got {unique_dates}"
        else:
            assert min_d == '2024-01-01', f"{sym} expected 2024-01-01, got {min_d}"
            assert max_d == '2026-10-22', f"{sym} expected 2026-10-22, got {max_d}"
            assert unique_dates == 724, f"{sym} expected 724 days, got {unique_dates}"
            
    # 4. Unique contract expiries per symbol
    print("\n4. Unique contract expiries per symbol:")
    exp_counts = df.groupby('symbol')['expiry_date'].nunique().to_dict()
    print("   Expiries by symbol:", exp_counts)
    expected_exp_counts = {
        'GOLD': 23,
        'GOLDGUINEA': 39,
        'GOLDPETAL': 39,
        'GOLDM': 40,
        'GOLDTEN': 24
    }
    for sym, exp_c in expected_exp_counts.items():
        act_c = exp_counts.get(sym, 0)
        assert act_c == exp_c, f"Symbol {sym}: expected {exp_c} expiries, got {act_c}"
    print("   All expiry counts match Phase 1 baseline perfectly.")
    
    # 5. Duplicate keys using (date, symbol, expiry_date)
    dup_count = df.duplicated(subset=['date', 'symbol', 'expiry_date']).sum()
    print(f"\n5. Duplicate keys on (date, symbol, expiry_date): {dup_count} (Expected: 0)")
    assert dup_count == 0, f"Found {dup_count} duplicate keys!"
    
    # 6. Missing values and invalid numeric fields
    print("\n6. Missing values and numeric validation:")
    null_summary = df.isna().sum().to_dict()
    for col, n_count in null_summary.items():
        if n_count > 0:
            print(f"   Column '{col}': {n_count} nulls ({n_count/len(df)*100:.2f}%)")
    assert null_summary['open'] == 1985, f"Expected 1985 nulls in open, got {null_summary['open']}"
    assert null_summary['high'] == 1985, f"Expected 1985 nulls in high, got {null_summary['high']}"
    assert null_summary['low'] == 1985, f"Expected 1985 nulls in low, got {null_summary['low']}"
    assert null_summary['close'] == 0, f"Expected 0 nulls in close, got {null_summary['close']}"
    assert null_summary['date'] == 0, f"Expected 0 nulls in date, got {null_summary['date']}"
    assert null_summary['expiry_date'] == 0, f"Expected 0 nulls in expiry_date, got {null_summary['expiry_date']}"
    assert null_summary['symbol'] == 0, f"Expected 0 nulls in symbol, got {null_summary['symbol']}"
    assert null_summary['volume_lots'] == 0, f"Expected 0 nulls in volume_lots, got {null_summary['volume_lots']}"
    
    invalid_price_count = df['flag_invalid_price'].sum()
    print(f"   Invalid price count (<= 0): {invalid_price_count} (Expected: 0)")
    assert invalid_price_count == 0, f"Found {invalid_price_count} invalid prices!"
    
    # 7. Zero-volume records and missing OHLC counts
    print("\n7. Zero-volume records and missing OHLC validation:")
    zero_vol = df['flag_zero_volume'].sum()
    missing_ohlc = df['flag_missing_ohlc'].sum()
    is_traded_count = df['is_traded'].sum()
    print(f"   Zero volume count: {zero_vol} (Expected: 1,985)")
    print(f"   Missing OHLC count: {missing_ohlc} (Expected: 1,985)")
    print(f"   Traded sessions count: {is_traded_count} (Expected: 14,210)")
    assert zero_vol == 1985, f"Expected 1985 zero vol, got {zero_vol}"
    assert missing_ohlc == 1985, f"Expected 1985 missing ohlc, got {missing_ohlc}"
    assert is_traded_count == 14210, f"Expected 14210 traded, got {is_traded_count}"
    assert (df['flag_zero_volume'] == df['flag_missing_ohlc']).all(), "Zero vol and missing OHLC must match 100%"
    
    # 8. Symbols stripped and dates/expiries parse successfully
    print("\n8. Symbol and Date parsing checks:")
    raw_symbols = set(df['symbol'])
    print(f"   Unique symbols: {raw_symbols}")
    for s in raw_symbols:
        assert s == s.strip(), f"Symbol '{s}' has unstripped whitespace!"
    print("   Ambiguous date flag count:", df['flag_ambiguous_date'].sum(), "(Expected: 0)")
    assert df['flag_ambiguous_date'].sum() == 0, "Found ambiguous dates!"
    
    # 9. All imported rows can be traced to their source files
    print("\n9. Traceability validation:")
    # Spot-check 20 random rows against raw source files
    sample_rows = df.sample(n=20, random_state=42)
    mismatches = 0
    for _, r in sample_rows.iterrows():
        sf = os.path.join(PROJECT_ROOT, r['source_file'])
        s_row = int(r['source_row'])
        with open(sf, 'r', encoding='utf-8') as fp:
            reader = csv.reader(fp)
            for current_idx, row_vals in enumerate(reader, start=1):
                if current_idx == s_row:
                    # check Date, Symbol, Close
                    raw_d = row_vals[0].strip()
                    raw_s = row_vals[2].strip()
                    raw_c = float(row_vals[9].strip())
                    if raw_d != r['raw_date'] or raw_s != r['symbol'] or raw_c != float(r['close']):
                        mismatches += 1
                        print(f"Traceability mismatch at {r['source_file']}:{s_row}")
                    break
    print(f"   Spot-checked 20 rows across source files: {20 - mismatches}/20 perfectly matched.")
    assert mismatches == 0, f"Found {mismatches} traceability mismatches!"
    
    # 10. Original raw files unmodified
    print("\n10. Original raw files immutability check:")
    inv_df = pd.read_csv(INVENTORY_CSV)
    market_inv = inv_df[inv_df['parsing_status'] == 'SUCCESS']
    size_mismatches = 0
    for _, r in market_inv.iterrows():
        disk_path = os.path.join(PROJECT_ROOT, r['filename'])
        actual_size = os.path.getsize(disk_path)
        recorded_size = int(r['file_size_bytes'])
        if actual_size != recorded_size:
            size_mismatches += 1
            print(f"File size mismatch: {r['filename']} was {recorded_size}, now {actual_size}")
    print(f"   Verified {len(market_inv)} raw files against audit inventory file sizes: {len(market_inv) - size_mismatches}/{len(market_inv)} exact match.")
    assert size_mismatches == 0, f"Found {size_mismatches} modified raw files!"

    print("\n" + "=" * 70)
    print("ALL 10 VALIDATION CHECKS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == '__main__':
    run_validations()
