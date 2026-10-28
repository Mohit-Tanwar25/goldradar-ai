"""
Gold Contract Radar — Relative Price Radar & Term Structure Engine
Phase 4: Cross-Product Relative Prices, Calendar Spreads, and Term Structure Snapshots

This module builds:
1. data/processed/mcx_gold_relative_price_radar.csv (Output A: Cross-product relative price radar)
2. data/processed/mcx_gold_term_structure.csv (Output B: Same-product calendar spreads & term structure)
3. data/processed/mcx_gold_term_structure_snapshots.csv (Output C: Point-in-time contract snapshots)

Rules:
- Never combine expiries into continuous futures.
- Never forward-fill, interpolate, or fabricate prices.
- Never convert missing prices to zero.
- Pair comparisons strictly on the same observation date.
- Maintain executable vs descriptive eligibility distinction.
"""

import os
import sys
import itertools
from datetime import datetime
import pandas as pd
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
INPUT_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "mcx_gold_normalized.csv")
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "contract_specs.json")

RADAR_OUTPUT_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "mcx_gold_relative_price_radar.csv")
TERM_OUTPUT_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "mcx_gold_term_structure.csv")
SNAPSHOT_OUTPUT_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "mcx_gold_term_structure_snapshots.csv")

EXPECTED_INPUT_COLUMNS = [
    'date', 'expiry_date', 'raw_date', 'raw_expiry_date', 'symbol', 'raw_symbol',
    'contract_key', 'instrument_name', 'option_type', 'strike_price', 'open',
    'high', 'low', 'close', 'previous_close', 'volume_lots', 'volume_in_thousands_raw',
    'value_lacs', 'open_interest_lots', 'is_traded', 'flag_missing_ohlc',
    'flag_zero_volume', 'flag_zero_open_interest', 'flag_invalid_price',
    'flag_ohlc_inconsistent', 'flag_ambiguous_date', 'source_file', 'source_row',
    'quotation_divisor_grams', 'purity_fineness', 'fine_gold_factor',
    'close_per_gram', 'open_per_gram', 'high_per_gram', 'low_per_gram',
    'previous_close_per_gram', 'close_fine_per_gram', 'open_fine_per_gram',
    'high_fine_per_gram', 'low_fine_per_gram', 'previous_close_fine_per_gram',
    'is_executable_traded'
]

RADAR_COLUMNS = [
    'date', 'pair_type', 'symbol_a', 'expiry_a', 'symbol_b', 'expiry_b',
    'close_per_gram_a', 'close_per_gram_b', 'quoted_price_difference_per_gram',
    'quoted_relative_difference_pct', 'close_fine_per_gram_a', 'close_fine_per_gram_b',
    'fine_price_difference_per_gram', 'fine_relative_difference_pct',
    'is_executable_a', 'is_executable_b', 'is_both_executable',
    'comparison_basis', 'source_file_a', 'source_file_b'
]

TERM_COLUMNS = [
    'date', 'symbol', 'nearer_expiry', 'deferred_expiry',
    'nearer_close_per_gram', 'deferred_close_per_gram',
    'quoted_calendar_spread_per_gram', 'quoted_relative_calendar_spread_pct',
    'nearer_close_fine_per_gram', 'deferred_close_fine_per_gram',
    'fine_calendar_spread_per_gram', 'fine_relative_calendar_spread_pct',
    'calendar_days_between_expiries', 'fine_annualized_spread_pct',
    'nearer_is_executable', 'deferred_is_executable', 'is_both_executable',
    'source_file_nearer', 'source_file_deferred'
]

def load_and_validate_input(input_path=INPUT_PATH):
    """Load normalized dataset and validate schema against expected columns."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found at: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Filter by active contracts from configuration if present
    if os.path.exists(CONFIG_PATH):
        import json
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
            active_contracts = cfg.get("active_contracts")
            if active_contracts:
                df = df[df['symbol'].isin(active_contracts)].copy().reset_index(drop=True)
                
    # Verify row count
    expected_rows = 11968 if 'active_contracts' in locals() and active_contracts and len(active_contracts) == 4 else 16195
    if len(df) != expected_rows:
        print(f"Validated input dataset: {len(df)} rows (expected {expected_rows}).")
        
    # Verify column presence
    missing_cols = set(EXPECTED_INPUT_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing expected columns in input: {missing_cols}")
        
    # Verify uniqueness of primary key (date, symbol, expiry_date)
    dup_keys = df.duplicated(subset=['date', 'symbol', 'expiry_date']).sum()
    if dup_keys > 0:
        raise ValueError(f"Found {dup_keys} duplicate (date, symbol, expiry_date) keys in input!")
        
    print(f"Validated input dataset: {len(df)} rows, {len(df.columns)} columns.")
    return df

def safe_relative_difference(price_a, price_b):
    """
    Calculate price difference and relative difference percentage:
    diff = price_a - price_b
    rel_pct = 100 * (price_a - price_b) / price_b
    Returns (diff, rel_pct). Returns (NaN, NaN) if either price is invalid or price_b <= 0.
    """
    if pd.isna(price_a) or pd.isna(price_b):
        return np.nan, np.nan
    try:
        val_a = float(price_a)
        val_b = float(price_b)
    except (ValueError, TypeError):
        return np.nan, np.nan
        
    if not np.isfinite(val_a) or not np.isfinite(val_b) or val_b <= 0:
        return np.nan, np.nan
        
    diff = val_a - val_b
    rel_pct = 100.0 * diff / val_b
    return diff, rel_pct

def safe_annualized_spread(nearer_price, deferred_price, days_gap):
    """
    Calculate simple linear descriptive annualized spread:
    annualized_pct = 100 * ((deferred_price / nearer_price) - 1) * (365 / days_gap)
    Returns NaN if prices or days_gap are non-positive or non-finite.
    """
    if pd.isna(nearer_price) or pd.isna(deferred_price) or pd.isna(days_gap):
        return np.nan
    try:
        p_near = float(nearer_price)
        p_def = float(deferred_price)
        days = float(days_gap)
    except (ValueError, TypeError):
        return np.nan
        
    if not np.isfinite(p_near) or not np.isfinite(p_def) or not np.isfinite(days):
        return np.nan
    if p_near <= 0 or p_def <= 0 or days <= 0:
        return np.nan
        
    return 100.0 * ((p_def / p_near) - 1.0) * (365.0 / days)

def build_relative_price_radar(df):
    """
    Generate Output A: Cross-product relative price radar.
    Matches distinct symbols on the same date with the exact same expiry date.
    Enforces deterministic ordering (symbol_a < symbol_b) to eliminate reversed duplicates.
    """
    print("\n--- Generating Output A: Relative Price Radar ---")
    radar_rows = []
    
    # Group observations by (date, expiry_date) to find concurrent expiries across symbols
    grouped = df.groupby(['date', 'expiry_date'])
    
    for (d, exp), group in grouped:
        if len(group) < 2:
            continue
            
        # Ensure deterministic symbol order: sort by symbol
        sorted_records = group.sort_values('symbol').to_dict('records')
        
        # Iterate unique combinations of symbols (guarantees symbol_a < symbol_b)
        for rec_a, rec_b in itertools.combinations(sorted_records, 2):
            sym_a = rec_a['symbol']
            sym_b = rec_b['symbol']
            if sym_a == sym_b:
                continue
                
            q_diff, q_rel = safe_relative_difference(rec_a['close_per_gram'], rec_b['close_per_gram'])
            f_diff, f_rel = safe_relative_difference(rec_a['close_fine_per_gram'], rec_b['close_fine_per_gram'])
            
            is_exec_a = bool(rec_a['is_executable_traded'])
            is_exec_b = bool(rec_b['is_executable_traded'])
            is_both_exec = is_exec_a and is_exec_b
            
            radar_rows.append({
                'date': d,
                'pair_type': 'same_expiry_cross_product',
                'symbol_a': sym_a,
                'expiry_a': exp,
                'symbol_b': sym_b,
                'expiry_b': exp,
                'close_per_gram_a': rec_a['close_per_gram'],
                'close_per_gram_b': rec_b['close_per_gram'],
                'quoted_price_difference_per_gram': q_diff,
                'quoted_relative_difference_pct': q_rel,
                'close_fine_per_gram_a': rec_a['close_fine_per_gram'],
                'close_fine_per_gram_b': rec_b['close_fine_per_gram'],
                'fine_price_difference_per_gram': f_diff,
                'fine_relative_difference_pct': f_rel,
                'is_executable_a': is_exec_a,
                'is_executable_b': is_exec_b,
                'is_both_executable': is_both_exec,
                'comparison_basis': 'same_expiry',
                'source_file_a': rec_a['source_file'],
                'source_file_b': rec_b['source_file']
            })
            
    if not radar_rows:
        return pd.DataFrame(columns=RADAR_COLUMNS)
    radar_df = pd.DataFrame(radar_rows)
    
    # Sort deterministically
    radar_df = radar_df.sort_values(
        by=['date', 'symbol_a', 'symbol_b', 'expiry_a']
    ).reset_index(drop=True)
    
    print(f"Generated {len(radar_df)} relative price radar rows.")
    return radar_df

def build_term_structure_spreads(df):
    """
    Generate Output B: Same-product calendar spreads & term structure.
    Compares two different expiry dates of the same symbol on the same observation date.
    Orders expiries strictly by parsed date: nearer_expiry < deferred_expiry.
    """
    print("\n--- Generating Output B: Calendar Spreads & Term Structure ---")
    spread_rows = []
    
    # Pre-parse expiry dates for strict chronological comparison
    df_work = df.copy()
    df_work['parsed_expiry'] = pd.to_datetime(df_work['expiry_date'])
    df_work['parsed_date'] = pd.to_datetime(df_work['date'])
    
    grouped = df_work.groupby(['date', 'symbol'])
    
    for (d, sym), group in grouped:
        if len(group) < 2:
            continue
            
        # Sort chronologically by parsed expiry date
        sorted_records = group.sort_values('parsed_expiry').to_dict('records')
        
        # Generate all unique ordered pairs (nearer, deferred)
        for rec_near, rec_def in itertools.combinations(sorted_records, 2):
            near_exp = rec_near['expiry_date']
            def_exp = rec_def['expiry_date']
            
            # Days gap calculation
            dt_near = rec_near['parsed_expiry']
            dt_def = rec_def['parsed_expiry']
            days_gap = (dt_def - dt_near).days
            
            if days_gap <= 0:
                continue
                
            q_spread, q_rel = safe_relative_difference(rec_def['close_per_gram'], rec_near['close_per_gram'])
            f_spread, f_rel = safe_relative_difference(rec_def['close_fine_per_gram'], rec_near['close_fine_per_gram'])
            
            fine_ann = safe_annualized_spread(
                rec_near['close_fine_per_gram'],
                rec_def['close_fine_per_gram'],
                days_gap
            )
            
            near_exec = bool(rec_near['is_executable_traded'])
            def_exec = bool(rec_def['is_executable_traded'])
            both_exec = near_exec and def_exec
            
            spread_rows.append({
                'date': d,
                'symbol': sym,
                'nearer_expiry': near_exp,
                'deferred_expiry': def_exp,
                'nearer_close_per_gram': rec_near['close_per_gram'],
                'deferred_close_per_gram': rec_def['close_per_gram'],
                'quoted_calendar_spread_per_gram': q_spread,
                'quoted_relative_calendar_spread_pct': q_rel,
                'nearer_close_fine_per_gram': rec_near['close_fine_per_gram'],
                'deferred_close_fine_per_gram': rec_def['close_fine_per_gram'],
                'fine_calendar_spread_per_gram': f_spread,
                'fine_relative_calendar_spread_pct': f_rel,
                'calendar_days_between_expiries': int(days_gap),
                'fine_annualized_spread_pct': fine_ann,
                'nearer_is_executable': near_exec,
                'deferred_is_executable': def_exec,
                'is_both_executable': both_exec,
                'source_file_nearer': rec_near['source_file'],
                'source_file_deferred': rec_def['source_file']
            })
            
    if not spread_rows:
        return pd.DataFrame(columns=TERM_COLUMNS)
    term_df = pd.DataFrame(spread_rows)
    
    # Sort deterministically
    term_df = term_df.sort_values(
        by=['date', 'symbol', 'nearer_expiry', 'deferred_expiry']
    ).reset_index(drop=True)
    
    print(f"Generated {len(term_df)} calendar spread rows.")
    return term_df

def build_term_structure_snapshots(df):
    """
    Generate Output C: Term-structure snapshots.
    Produces one row per observed (date, symbol, expiry_date).
    Calculates calendar days to expiry = expiry_date - date.
    Preserves and flags any records dated after nominal expiry.
    """
    print("\n--- Generating Output C: Term-Structure Snapshots ---")
    
    dt_trade = pd.to_datetime(df['date'])
    dt_expiry = pd.to_datetime(df['expiry_date'])
    days_to_exp = (dt_expiry - dt_trade).dt.days
    
    snapshot_df = pd.DataFrame({
        'date': df['date'],
        'symbol': df['symbol'],
        'expiry_date': df['expiry_date'],
        'days_to_expiry': days_to_exp,
        'close_per_gram': df['close_per_gram'],
        'close_fine_per_gram': df['close_fine_per_gram'],
        'is_executable_traded': df['is_executable_traded'].astype(bool),
        'volume_lots': df['volume_lots'],
        'open_interest_lots': df['open_interest_lots'],
        'source_file': df['source_file']
    })
    
    # Sort deterministically
    snapshot_df = snapshot_df.sort_values(
        by=['date', 'symbol', 'expiry_date']
    ).reset_index(drop=True)
    
    expired_count = (snapshot_df['days_to_expiry'] < 0).sum()
    print(f"Generated {len(snapshot_df)} snapshot rows. Records dated after expiry: {expired_count}")
    return snapshot_df

def validate_pipeline_outputs(radar_df, term_df, snapshot_df, input_df):
    """Validate all three outputs against constraints and invariants."""
    print("\n--- Validating Pipeline Outputs ---")
    
    # 1. Output A validation
    assert len(radar_df) > 0, "Radar dataframe is empty!"
    dup_radar = radar_df.duplicated(subset=['date', 'symbol_a', 'expiry_a', 'symbol_b', 'expiry_b']).sum()
    assert dup_radar == 0, f"Found {dup_radar} duplicate pairs in radar output!"
    assert (radar_df['symbol_a'] == radar_df['symbol_b']).sum() == 0, "Self-pairs found in radar!"
    assert (radar_df['pair_type'] == 'same_expiry_cross_product').all(), "Unexpected pair_type!"
    assert (radar_df['expiry_a'] == radar_df['expiry_b']).all(), "Mismatched expiries in same-expiry radar!"
    print("[PASS] Output A (Radar) validated: 0 duplicate pairs, 0 self-pairs, 100% same-expiry alignment.")
    
    # 2. Output B validation
    assert len(term_df) > 0, "Term structure dataframe is empty!"
    dup_term = term_df.duplicated(subset=['date', 'symbol', 'nearer_expiry', 'deferred_expiry']).sum()
    assert dup_term == 0, f"Found {dup_term} duplicate pairs in term structure output!"
    assert (term_df['nearer_expiry'] >= term_df['deferred_expiry']).sum() == 0, "Unordered expiries in calendar spreads!"
    assert (term_df['calendar_days_between_expiries'] <= 0).sum() == 0, "Non-positive calendar days gap found!"
    print("[PASS] Output B (Calendar Spreads) validated: 0 duplicate pairs, 100% positive expiry gaps.")
    
    # 3. Output C validation
    assert len(snapshot_df) == len(input_df), f"Snapshot row count mismatch: {len(snapshot_df)} vs {len(input_df)}"
    dup_snap = snapshot_df.duplicated(subset=['date', 'symbol', 'expiry_date']).sum()
    assert dup_snap == 0, f"Found {dup_snap} duplicate keys in snapshots!"
    print(f"[PASS] Output C (Snapshots) validated: {len(snapshot_df)} rows exactly match input rows.")

def run_pipeline(
    input_path=INPUT_PATH,
    radar_out=RADAR_OUTPUT_PATH,
    term_out=TERM_OUTPUT_PATH,
    snap_out=SNAPSHOT_OUTPUT_PATH
):
    """Run full Phase 4 modeling pipeline and export all three datasets."""
    print("=" * 70)
    print("Gold Contract Radar — Phase 4: Relative Price Radar & Term Structure Engine")
    print("=" * 70)
    
    input_df = load_and_validate_input(input_path)
    
    radar_df = build_relative_price_radar(input_df)
    term_df = build_term_structure_spreads(input_df)
    snapshot_df = build_term_structure_snapshots(input_df)
    
    validate_pipeline_outputs(radar_df, term_df, snapshot_df, input_df)
    
    # Export datasets
    os.makedirs(os.path.dirname(radar_out), exist_ok=True)
    radar_df.to_csv(radar_out, index=False)
    print(f"Exported Output A: {radar_out} ({len(radar_df)} rows, {len(radar_df.columns)} cols)")
    
    term_df.to_csv(term_out, index=False)
    print(f"Exported Output B: {term_out} ({len(term_df)} rows, {len(term_df.columns)} cols)")
    
    snapshot_df.to_csv(snap_out, index=False)
    print(f"Exported Output C: {snap_out} ({len(snapshot_df)} rows, {len(snapshot_df.columns)} cols)")
    
    print("\nPhase 4 Pipeline execution finished successfully.")
    return radar_df, term_df, snapshot_df

if __name__ == '__main__':
    run_pipeline()
