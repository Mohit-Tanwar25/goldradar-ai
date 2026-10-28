"""
Gold Contract Radar — Price Normalization Pipeline
Phase 3: Quotation Divisors, Price per Gram & Fine Gold Equivalent Calculation

This script ingests data/processed/mcx_gold_master.csv, applies verified MCX contract
specifications from config/contract_specs.json, calculates quoted price per gram
and fine-gold equivalent price per gram, preserves all original data & flags,
and outputs data/processed/mcx_gold_normalized.csv.
"""

import os
import sys
import json
import pandas as pd
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "contract_specs.json")
MASTER_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "mcx_gold_master.csv")
NORMALIZED_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "mcx_gold_normalized.csv")

def load_contract_specs(config_path=CONFIG_PATH):
    """Load and validate verified contract specifications."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Contract specs configuration missing: {config_path}")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    contracts = config.get("contracts", {})
    active_contracts = config.get("active_contracts", ["GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"])
    missing = set(active_contracts) - set(contracts.keys())
    if missing:
        raise ValueError(f"Missing contract specs for active symbols: {missing}")
    return contracts, active_contracts

def normalize_dataset(master_csv_path=MASTER_CSV_PATH, output_path=NORMALIZED_CSV_PATH):
    """Normalize master dataset prices by quotation divisor and purity factor."""
    print("=" * 65)
    print("Gold Contract Radar — Phase 3: Price Normalization Pipeline")
    print("=" * 65)
    
    if not os.path.exists(master_csv_path):
        raise FileNotFoundError(f"Input master dataset not found: {master_csv_path}")
        
    specs, active_contracts = load_contract_specs()
    df = pd.read_csv(master_csv_path)
    
    # Filter to active contracts if present
    if active_contracts:
        df = df[df['symbol'].isin(active_contracts)].copy().reset_index(drop=True)
    
    input_row_count = len(df)
    print(f"Loaded master dataset: {input_row_count} rows, {len(df.columns)} columns.")
    expected_rows = 11968 if len(active_contracts) == 4 else 16195
    if input_row_count != expected_rows:
        print(f"Note: Master rows count is {input_row_count} (expected {expected_rows}).")
        
    # Map specification parameters
    df['quotation_divisor_grams'] = df['symbol'].map(lambda s: specs[s]['quotation_divisor_grams'])
    df['purity_fineness'] = df['symbol'].map(lambda s: specs[s]['underlying_purity_fineness'])
    df['fine_gold_factor'] = df['symbol'].map(lambda s: specs[s]['fine_gold_factor'])
    
    # 1. Quoted Price per Gram: price_per_gram = quoted_price / quotation_divisor_grams
    # Missing OHLC values remain strictly NaN
    df['close_per_gram'] = df['close'] / df['quotation_divisor_grams']
    df['open_per_gram'] = df['open'] / df['quotation_divisor_grams']
    df['high_per_gram'] = df['high'] / df['quotation_divisor_grams']
    df['low_per_gram'] = df['low'] / df['quotation_divisor_grams']
    df['previous_close_per_gram'] = df['previous_close'] / df['quotation_divisor_grams']
    
    # 2. Fine Gold Equivalent Price per Gram:
    # fine_gold_price_per_gram = price_per_gram / (purity_fineness / 1000.0)
    # (Adjusts 995 vs 999 purity to standard 1000 fine gold equivalent)
    df['close_fine_per_gram'] = df['close_per_gram'] / df['fine_gold_factor']
    df['open_fine_per_gram'] = df['open_per_gram'] / df['fine_gold_factor']
    df['high_fine_per_gram'] = df['high_per_gram'] / df['fine_gold_factor']
    df['low_fine_per_gram'] = df['low_per_gram'] / df['fine_gold_factor']
    df['previous_close_fine_per_gram'] = df['previous_close_per_gram'] / df['fine_gold_factor']
    
    # 3. Explicit liquidity / eligibility flag for downstream modeling
    # Non-traded carried-forward Close values must not be treated as executable fills
    df['is_executable_traded'] = df['is_traded'] & (~df['flag_missing_ohlc'])
    
    # Verify immutability of row counts and keys
    output_row_count = len(df)
    if output_row_count != input_row_count:
        raise ValueError(f"Row count mismatch: input {input_row_count} vs output {output_row_count}")
        
    dup_keys = df.duplicated(subset=['date', 'symbol', 'expiry_date']).sum()
    if dup_keys > 0:
        raise ValueError(f"Introduced {dup_keys} duplicate keys!")
        
    # Check that missing values in open/high/low are exactly preserved
    expected_missing = 146 if len(active_contracts) == 4 else 1985
    assert df['open_per_gram'].isna().sum() == expected_missing, f"open_per_gram missing count mismatch (got {df['open_per_gram'].isna().sum()}, expected {expected_missing})!"
    assert df['high_per_gram'].isna().sum() == expected_missing, f"high_per_gram missing count mismatch (got {df['high_per_gram'].isna().sum()}, expected {expected_missing})!"
    assert df['low_per_gram'].isna().sum() == expected_missing, f"low_per_gram missing count mismatch (got {df['low_per_gram'].isna().sum()}, expected {expected_missing})!"
    assert df['close_per_gram'].isna().sum() == 0, "close_per_gram has unexpected nulls!"
    
    # Save output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Normalized dataset saved to: {output_path}")
    print(f"Output shape: {df.shape} ({len(df)} rows, {len(df.columns)} columns)")
    print("Price normalization complete and validated.")
    return df

if __name__ == '__main__':
    normalize_dataset()
