"""
Gold Contract Radar — MCX Commodity Derivatives Intelligence
Phase 5: Liquidity & Transaction Cost Filters Engine

This module implements a transparent, reproducible screening and transaction-cost
modeling layer for MCX gold derivatives. It processes:
1. Same-expiry cross-product candidates (mcx_gold_relative_price_radar.csv)
2. Same-symbol calendar-spread candidates (mcx_gold_term_structure.csv)

Outputs:
A. mcx_gold_liquidity_filtered_candidates.csv (All screened candidates + audit flags)
B. mcx_gold_transaction_cost_scenarios.csv (Scenario-level cost breakdowns: base, low, high)
C. mcx_gold_eligible_candidates.csv (Subset passing all data, expiry, and liquidity filters)
"""

import os
import sys
import json
import math
from datetime import datetime
from typing import Dict, Any, Tuple, List
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")

def get_lcm(a: int, b: int) -> int:
    """Compute Least Common Multiple of two integers."""
    if a <= 0 or b <= 0:
        return 0
    return abs(a * b) // math.gcd(a, b)

def load_configurations(config_dir: str = CONFIG_DIR) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Load and validate all Phase 5 configuration files."""
    specs_path = os.path.join(config_dir, "contract_specs.json")
    liq_path = os.path.join(config_dir, "liquidity_filters.json")
    costs_path = os.path.join(config_dir, "transaction_costs.json")

    for p in [specs_path, liq_path, costs_path]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Required configuration file missing: {p}")

    with open(specs_path, 'r', encoding='utf-8') as f:
        specs_cfg = json.load(f)
    with open(liq_path, 'r', encoding='utf-8') as f:
        liq_cfg = json.load(f)
    with open(costs_path, 'r', encoding='utf-8') as f:
        costs_cfg = json.load(f)

    return specs_cfg, liq_cfg, costs_cfg

def load_input_datasets(data_dir: str = DATA_DIR) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load validated input datasets from Phase 3 and Phase 4."""
    norm_path = os.path.join(data_dir, "mcx_gold_normalized.csv")
    radar_path = os.path.join(data_dir, "mcx_gold_relative_price_radar.csv")
    term_path = os.path.join(data_dir, "mcx_gold_term_structure.csv")

    for p in [norm_path, radar_path, term_path]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Required processed dataset missing: {p}")

    norm_df = pd.read_csv(norm_path)
    radar_df = pd.read_csv(radar_path)
    term_df = pd.read_csv(term_path)

    # Validate non-emptiness dynamically based on active contracts
    specs_path = os.path.join(CONFIG_DIR, "contract_specs.json")
    is_four_universe = False
    if os.path.exists(specs_path):
        with open(specs_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
            if len(cfg.get("active_contracts", [])) == 4:
                is_four_universe = True

    exp_norm = 11968 if is_four_universe else 16195
    exp_radar = 7672 if is_four_universe else 9059
    exp_term = 23811 if is_four_universe else 34086

    if len(norm_df) != exp_norm:
        print(f"Normalized dataset row count: {len(norm_df)} (expected {exp_norm})")
    if len(radar_df) != exp_radar:
        print(f"Radar dataset row count: {len(radar_df)} (expected {exp_radar})")
    if len(term_df) != exp_term:
        print(f"Term structure dataset row count: {len(term_df)} (expected {exp_term})")

    return norm_df, radar_df, term_df

def build_contract_lookup(norm_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a clean lookup dataframe indexed by (date, symbol, expiry_date)
    containing all required leg-level trading, liquidity, and data-quality attributes.
    """
    df = norm_df.copy()
    
    # Calculate days to expiry explicitly
    d_trade = pd.to_datetime(df['date'])
    d_exp = pd.to_datetime(df['expiry_date'])
    df['days_to_expiry'] = (d_exp - d_trade).dt.days

    cols = [
        'date', 'symbol', 'expiry_date', 'contract_key',
        'close', 'close_per_gram', 'close_fine_per_gram',
        'volume_lots', 'open_interest_lots', 'days_to_expiry',
        'is_executable_traded', 'flag_missing_ohlc', 'flag_zero_volume',
        'flag_invalid_price', 'source_file'
    ]
    return df[cols].copy()

def screen_candidates(
    radar_df: pd.DataFrame,
    term_df: pd.DataFrame,
    norm_df: pd.DataFrame,
    liq_cfg: Dict[str, Any],
    specs_cfg: Dict[str, Any]
) -> pd.DataFrame:
    """
    Merge leg-level attributes onto candidate pairs, evaluate data eligibility,
    expiry filters, and liquidity thresholds, and record machine-readable exclusion reasons.
    """
    lookup = build_contract_lookup(norm_df)
    contracts_meta = specs_cfg.get("contracts", {})
    global_cfg = liq_cfg.get("global_defaults", {})
    sym_overrides = liq_cfg.get("symbol_overrides", {})
    use_overrides = global_cfg.get("enable_per_symbol_overrides", True)
    min_dte_global = global_cfg.get("min_days_to_expiry", 5)
    merged_dfs = []
    leg_a_cols = {c: f"{c}_leg_a" for c in lookup.columns if c not in ['date']}
    leg_b_cols = {c: f"{c}_leg_b" for c in lookup.columns if c not in ['date']}

    # -------------------------------------------------------------
    # 1. Process Strategy A: Cross-Product Same-Expiry Candidates
    # -------------------------------------------------------------
    if len(radar_df) > 0 and 'date' in radar_df.columns:
        r_df = radar_df.copy()
        r_df['candidate_type'] = 'same_expiry_cross_product'
        r_df['candidate_id'] = (
            "RADAR_" + r_df['date'] + "_" + 
            r_df['symbol_a'] + "_" + r_df['expiry_a'] + "_" + 
            r_df['symbol_b'] + "_" + r_df['expiry_b']
        )

        r_merged = r_df.merge(
            lookup.rename(columns=leg_a_cols),
            left_on=['date', 'symbol_a', 'expiry_a'],
            right_on=['date', 'symbol_leg_a', 'expiry_date_leg_a'],
            how='left'
        )

        r_merged = r_merged.merge(
            lookup.rename(columns=leg_b_cols),
            left_on=['date', 'symbol_b', 'expiry_b'],
            right_on=['date', 'symbol_leg_b', 'expiry_date_leg_b'],
            how='left'
        )

        r_merged['quoted_price_spread_per_gram'] = r_merged['quoted_price_difference_per_gram']
        r_merged['quoted_relative_spread_pct'] = r_merged['quoted_relative_difference_pct']
        r_merged['fine_price_spread_per_gram'] = r_merged['fine_price_difference_per_gram']
        r_merged['fine_relative_spread_pct'] = r_merged['fine_relative_difference_pct']
        r_merged['calendar_days_between_expiries'] = 0
        r_merged['fine_annualized_spread_pct'] = np.nan
        merged_dfs.append(r_merged)

    # -------------------------------------------------------------
    # 2. Process Strategy B: Same-Symbol Calendar Spreads
    # -------------------------------------------------------------
    if len(term_df) > 0 and 'date' in term_df.columns:
        t_df = term_df.copy()
        t_df['candidate_type'] = 'same_symbol_calendar_spread'
        t_df['candidate_id'] = (
            "CAL_" + t_df['date'] + "_" + 
            t_df['symbol'] + "_" + t_df['nearer_expiry'] + "_" + 
            t_df['deferred_expiry']
        )

        t_merged = t_df.merge(
            lookup.rename(columns=leg_a_cols),
            left_on=['date', 'symbol', 'nearer_expiry'],
            right_on=['date', 'symbol_leg_a', 'expiry_date_leg_a'],
            how='left'
        )

        t_merged = t_merged.merge(
            lookup.rename(columns=leg_b_cols),
            left_on=['date', 'symbol', 'deferred_expiry'],
            right_on=['date', 'symbol_leg_b', 'expiry_date_leg_b'],
            how='left'
        )

        t_merged['quoted_price_spread_per_gram'] = t_merged['quoted_calendar_spread_per_gram']
        t_merged['quoted_relative_spread_pct'] = t_merged['quoted_relative_calendar_spread_pct']
        t_merged['fine_price_spread_per_gram'] = t_merged['fine_calendar_spread_per_gram']
        t_merged['fine_relative_spread_pct'] = t_merged['fine_relative_calendar_spread_pct']
        merged_dfs.append(t_merged)

    # -------------------------------------------------------------
    # 3. Combine Candidates & Standardize Columns
    # -------------------------------------------------------------
    if not merged_dfs:
        return pd.DataFrame(columns=[
            'candidate_id', 'candidate_type', 'date',
            'symbol_leg_a', 'expiry_date_leg_a', 'contract_key_leg_a',
            'close_per_gram_leg_a', 'close_fine_per_gram_leg_a',
            'volume_lots_leg_a', 'open_interest_lots_leg_a', 'days_to_expiry_leg_a',
            'is_executable_traded_leg_a', 'flag_missing_ohlc_leg_a', 'flag_zero_volume_leg_a', 'flag_invalid_price_leg_a',
            'passes_volume_leg_a', 'passes_open_interest_leg_a',
            'symbol_leg_b', 'expiry_date_leg_b', 'contract_key_leg_b',
            'close_per_gram_leg_b', 'close_fine_per_gram_leg_b',
            'volume_lots_leg_b', 'open_interest_lots_leg_b', 'days_to_expiry_leg_b',
            'is_executable_traded_leg_b', 'flag_missing_ohlc_leg_b', 'flag_zero_volume_leg_b', 'flag_invalid_price_leg_b',
            'passes_volume_leg_b', 'passes_open_interest_leg_b',
            'quoted_price_spread_per_gram', 'quoted_relative_spread_pct',
            'fine_price_spread_per_gram', 'fine_relative_spread_pct',
            'calendar_days_between_expiries', 'fine_annualized_spread_pct',
            'is_both_data_eligible', 'passes_expiry_filter', 'passes_volume_filter',
            'passes_open_interest_filter', 'passes_liquidity_filter',
            'is_all_filters_eligible', 'exclusion_reasons',
            'quantity_matching_status', 'cost_model_status',
            'source_file_leg_a', 'source_file_leg_b'
        ])

    candidates = pd.concat(merged_dfs, ignore_index=True)

    # -------------------------------------------------------------
    # 4. Vectorized Threshold & Filter Evaluation
    # -------------------------------------------------------------
    def get_thresh_series(sym_series, key, default_val):
        if use_overrides:
            return sym_series.map(lambda s: sym_overrides.get(s, {}).get(key, default_val))
        return pd.Series(default_val, index=sym_series.index)

    min_vol_a = get_thresh_series(candidates['symbol_leg_a'], 'min_volume_lots', global_cfg.get("min_volume_lots", 10))
    min_vol_b = get_thresh_series(candidates['symbol_leg_b'], 'min_volume_lots', global_cfg.get("min_volume_lots", 10))
    min_oi_a = get_thresh_series(candidates['symbol_leg_a'], 'min_open_interest_lots', global_cfg.get("min_open_interest_lots", 25))
    min_oi_b = get_thresh_series(candidates['symbol_leg_b'], 'min_open_interest_lots', global_cfg.get("min_open_interest_lots", 25))
    min_dte_a = get_thresh_series(candidates['symbol_leg_a'], 'min_days_to_expiry', min_dte_global)
    min_dte_b = get_thresh_series(candidates['symbol_leg_b'], 'min_days_to_expiry', min_dte_global)

    # Volume and Open Interest filters
    passes_volume_leg_a = candidates['volume_lots_leg_a'] >= min_vol_a
    passes_volume_leg_b = candidates['volume_lots_leg_b'] >= min_vol_b
    passes_volume_filter = passes_volume_leg_a & passes_volume_leg_b

    passes_oi_leg_a = candidates['open_interest_lots_leg_a'] >= min_oi_a
    passes_oi_leg_b = candidates['open_interest_lots_leg_b'] >= min_oi_b
    passes_open_interest_filter = passes_oi_leg_a & passes_oi_leg_b

    passes_liquidity_filter = passes_volume_filter & passes_open_interest_filter

    # Expiry filters
    not_expired_a = candidates['days_to_expiry_leg_a'] > 0
    not_expired_b = candidates['days_to_expiry_leg_b'] > 0
    not_expired = not_expired_a & not_expired_b

    sufficient_dte_a = candidates['days_to_expiry_leg_a'] >= min_dte_a
    sufficient_dte_b = candidates['days_to_expiry_leg_b'] >= min_dte_b
    sufficient_dte = sufficient_dte_a & sufficient_dte_b

    cal_order_ok = (candidates['candidate_type'] != 'same_symbol_calendar_spread') | (
        (candidates['calendar_days_between_expiries'] > 0) & 
        (candidates['days_to_expiry_leg_a'] < candidates['days_to_expiry_leg_b'])
    )

    passes_expiry_filter = not_expired & sufficient_dte & cal_order_ok

    # Data eligibility
    valid_ohlc_a = ~candidates['flag_missing_ohlc_leg_a']
    valid_ohlc_b = ~candidates['flag_missing_ohlc_leg_b']
    non_zero_vol_a = (~candidates['flag_zero_volume_leg_a']) & (candidates['volume_lots_leg_a'] > 0)
    non_zero_vol_b = (~candidates['flag_zero_volume_leg_b']) & (candidates['volume_lots_leg_b'] > 0)
    valid_price_a = (~candidates['flag_invalid_price_leg_a']) & candidates['close_per_gram_leg_a'].notna()
    valid_price_b = (~candidates['flag_invalid_price_leg_b']) & candidates['close_per_gram_leg_b'].notna()
    exec_a = candidates['is_executable_traded_leg_a'].fillna(False).astype(bool)
    exec_b = candidates['is_executable_traded_leg_b'].fillna(False).astype(bool)

    is_both_data_eligible = (
        valid_ohlc_a & valid_ohlc_b &
        non_zero_vol_a & non_zero_vol_b &
        valid_price_a & valid_price_b &
        exec_a & exec_b
    )

    is_all_filters_eligible = is_both_data_eligible & passes_expiry_filter & passes_liquidity_filter

    # Assemble machine-readable exclusion reasons via fast zip
    cond_ohlc_a = ~valid_ohlc_a
    cond_ohlc_b = ~valid_ohlc_b
    cond_zv_a = ~non_zero_vol_a
    cond_zv_b = ~non_zero_vol_b
    cond_inv_a = ~valid_price_a
    cond_inv_b = ~valid_price_b
    cond_exp = ~not_expired
    cond_ins_dte = not_expired & (~sufficient_dte)
    cond_vol_fail_a = ~passes_volume_leg_a
    cond_vol_fail_b = ~passes_volume_leg_b
    cond_oi_fail_a = ~passes_oi_leg_a
    cond_oi_fail_b = ~passes_oi_leg_b
    cond_ord_fail = ~cal_order_ok

    exclusion_reasons_list = []
    for c_ohlc_a, c_ohlc_b, c_zv_a, c_zv_b, c_inv_a, c_inv_b, c_exp, c_ins_dte, c_v_a, c_v_b, c_o_a, c_o_b, c_ord in zip(
        cond_ohlc_a, cond_ohlc_b, cond_zv_a, cond_zv_b, cond_inv_a, cond_inv_b,
        cond_exp, cond_ins_dte, cond_vol_fail_a, cond_vol_fail_b, cond_oi_fail_a, cond_oi_fail_b, cond_ord_fail
    ):
        reasons = []
        if c_ohlc_a: reasons.append("incomplete_ohlc_leg_a")
        if c_ohlc_b: reasons.append("incomplete_ohlc_leg_b")
        if c_zv_a: reasons.append("zero_volume_leg_a")
        if c_zv_b: reasons.append("zero_volume_leg_b")
        if c_inv_a: reasons.append("invalid_price_leg_a")
        if c_inv_b: reasons.append("invalid_price_leg_b")
        if c_exp: reasons.append("expired_or_expiry_day")
        elif c_ins_dte: reasons.append("insufficient_days_to_expiry")
        if c_v_a: reasons.append("volume_below_threshold_leg_a")
        if c_v_b: reasons.append("volume_below_threshold_leg_b")
        if c_o_a: reasons.append("open_interest_below_threshold_leg_a")
        if c_o_b: reasons.append("open_interest_below_threshold_leg_b")
        if c_ord: reasons.append("invalid_expiry_ordering")
        exclusion_reasons_list.append(";".join(reasons) if reasons else "NONE")

    candidates['is_both_data_eligible'] = is_both_data_eligible
    candidates['passes_expiry_filter'] = passes_expiry_filter
    candidates['passes_volume_leg_a'] = passes_volume_leg_a
    candidates['passes_volume_leg_b'] = passes_volume_leg_b
    candidates['passes_volume_filter'] = passes_volume_filter
    candidates['passes_open_interest_leg_a'] = passes_oi_leg_a
    candidates['passes_open_interest_leg_b'] = passes_oi_leg_b
    candidates['passes_open_interest_filter'] = passes_open_interest_filter
    candidates['passes_liquidity_filter'] = passes_liquidity_filter
    candidates['is_all_filters_eligible'] = is_all_filters_eligible
    candidates['exclusion_reasons'] = exclusion_reasons_list

    # Quantity matching status
    candidates['quantity_matching_status'] = np.where(
        candidates['candidate_type'] == 'same_symbol_calendar_spread',
        'exact_1_to_1_lot',
        'integer_lot_lcm_matched'
    )

    # Cost model status
    candidates['cost_model_status'] = np.where(
        is_both_data_eligible,
        'available',
        np.where(
            candidates['flag_zero_volume_leg_a'] | candidates['flag_zero_volume_leg_b'],
            'unavailable_zero_volume',
            'unavailable_missing_or_invalid_price'
        )
    )

    final_cols = [
        'candidate_id', 'candidate_type', 'date',
        'symbol_leg_a', 'expiry_date_leg_a', 'contract_key_leg_a',
        'close_per_gram_leg_a', 'close_fine_per_gram_leg_a',
        'volume_lots_leg_a', 'open_interest_lots_leg_a', 'days_to_expiry_leg_a',
        'is_executable_traded_leg_a', 'flag_missing_ohlc_leg_a', 'flag_zero_volume_leg_a', 'flag_invalid_price_leg_a',
        'passes_volume_leg_a', 'passes_open_interest_leg_a',
        'symbol_leg_b', 'expiry_date_leg_b', 'contract_key_leg_b',
        'close_per_gram_leg_b', 'close_fine_per_gram_leg_b',
        'volume_lots_leg_b', 'open_interest_lots_leg_b', 'days_to_expiry_leg_b',
        'is_executable_traded_leg_b', 'flag_missing_ohlc_leg_b', 'flag_zero_volume_leg_b', 'flag_invalid_price_leg_b',
        'passes_volume_leg_b', 'passes_open_interest_leg_b',
        'quoted_price_spread_per_gram', 'quoted_relative_spread_pct',
        'fine_price_spread_per_gram', 'fine_relative_spread_pct',
        'calendar_days_between_expiries', 'fine_annualized_spread_pct',
        'is_both_data_eligible', 'passes_expiry_filter', 'passes_volume_filter',
        'passes_open_interest_filter', 'passes_liquidity_filter',
        'is_all_filters_eligible', 'exclusion_reasons',
        'quantity_matching_status', 'cost_model_status',
        'source_file_leg_a', 'source_file_leg_b'
    ]

    return candidates[final_cols].copy()

def compute_single_leg_cost(
    turnover: float,
    orders: int,
    scenario_cfg: Dict[str, Any],
    entry_side: str = "buy"
) -> Dict[str, float]:
    """
    Calculate statutory, exchange, broker, and tax charges for a single leg completing a round trip.
    A complete round trip comprises 1 entry transaction and 1 exit transaction (1 Buy + 1 Sell).
    Turnover is assumed identical on entry and exit for reference spread costing.
    entry_side: 'buy' if entered long (Stamp on entry, CTT on exit), 'sell' if entered short (CTT on entry, Stamp on exit).
    """
    if np.isnan(turnover) or turnover <= 0:
        return {
            'turnover': np.nan, 'entry_cost': np.nan, 'exit_cost': np.nan,
            'total_cost': np.nan, 'brokerage': np.nan, 'exchange_fee': np.nan,
            'sebi_fee': np.nan, 'stamp_duty': np.nan, 'ctt': np.nan, 'gst': np.nan
        }

    exch_rate = scenario_cfg.get("exchange_transaction_charge_rate", 0.000021)
    sebi_rate = scenario_cfg.get("sebi_rate", 0.000001)
    stamp_rate = scenario_cfg.get("stamp_duty_rate", 0.00002)
    ctt_rate = scenario_cfg.get("ctt_rate", 0.0001)
    gst_rate = scenario_cfg.get("gst_rate", 0.18)
    brok_model = scenario_cfg.get("brokerage_model", "discount_flat_or_percent_min")
    brok_flat = scenario_cfg.get("brokerage_flat_per_order", 20.0)
    brok_pct = scenario_cfg.get("brokerage_percent_rate", 0.0003)

    # Brokerage calculation per side
    if brok_model == "percentage_of_turnover":
        brok_side = turnover * brok_pct
    else:  # discount_flat_or_percent_min
        brok_side = min(brok_flat, turnover * brok_pct) * orders

    total_brokerage = 2.0 * brok_side

    # Exchange and SEBI charges on both sides
    exch_side = turnover * exch_rate
    total_exch = 2.0 * exch_side

    sebi_side = turnover * sebi_rate
    total_sebi = 2.0 * sebi_side

    # Statutory Taxes: Stamp Duty on Buy, CTT on Sell
    total_stamp = turnover * stamp_rate
    total_ctt = turnover * ctt_rate

    # GST on service charges (Brokerage + Exchange + SEBI)
    gst_side = (brok_side + exch_side + sebi_side) * gst_rate
    total_gst = (total_brokerage + total_exch + total_sebi) * gst_rate

    # Per-side costs based on entry orientation
    service_side = brok_side + exch_side + sebi_side + gst_side
    if entry_side == "sell":
        entry_cost = service_side + total_ctt
        exit_cost = service_side + total_stamp
    else:  # default 'buy'
        entry_cost = service_side + total_stamp
        exit_cost = service_side + total_ctt
    total_cost = entry_cost + exit_cost

    return {
        'turnover': turnover,
        'entry_cost': entry_cost,
        'exit_cost': exit_cost,
        'total_cost': total_cost,
        'brokerage': total_brokerage,
        'exchange_fee': total_exch,
        'sebi_fee': total_sebi,
        'stamp_duty': total_stamp,
        'ctt': total_ctt,
        'gst': total_gst
    }

def model_transaction_costs(
    candidates_df: pd.DataFrame,
    costs_cfg: Dict[str, Any],
    specs_cfg: Dict[str, Any]
) -> pd.DataFrame:
    """
    Generate Output B: Scenario-level transaction cost calculations across
    'base', 'low', and 'high' cost schedules for every screened candidate (vectorized).
    """
    contracts_meta = specs_cfg.get("contracts", {})
    scenarios = costs_cfg.get("scenarios", {})
    cfg_version = costs_cfg.get("metadata", {}).get("version", "1.0.0")

    # Map trading units in grams
    tu_map = {sym: meta.get("trading_unit_grams", 10.0) for sym, meta in contracts_meta.items()}
    tu_a = candidates_df['symbol_leg_a'].map(tu_map).fillna(10.0).values
    tu_b = candidates_df['symbol_leg_b'].map(tu_map).fillna(10.0).values

    # Determine matched integer lots and matched exposure grams
    is_cal = (candidates_df['candidate_type'] == 'same_symbol_calendar_spread').values
    
    # Precompute LCM for all pairs
    matched_lots_a = np.ones(len(candidates_df), dtype=int)
    matched_lots_b = np.ones(len(candidates_df), dtype=int)
    matched_exposure_grams = tu_a.copy()

    for idx, (sym_a, sym_b, cal_flag, t_a, t_b) in enumerate(zip(
        candidates_df['symbol_leg_a'], candidates_df['symbol_leg_b'], is_cal, tu_a, tu_b
    )):
        if not cal_flag:
            lcm_g = get_lcm(int(t_a), int(t_b))
            matched_lots_a[idx] = lcm_g // int(t_a)
            matched_lots_b[idx] = lcm_g // int(t_b)
            matched_exposure_grams[idx] = lcm_g

    p_a = candidates_df['close_per_gram_leg_a'].values
    p_b = candidates_df['close_per_gram_leg_b'].values
    cost_status = candidates_df['cost_model_status'].values
    is_avail = (cost_status == 'available') & (~np.isnan(p_a)) & (~np.isnan(p_b))

    notional_a = np.where(is_avail, matched_lots_a * tu_a * p_a, np.nan)
    notional_b = np.where(is_avail, matched_lots_b * tu_b * p_b, np.nan)
    comb_notional = notional_a + notional_b

    gross_spread = candidates_df['quoted_price_spread_per_gram'].values
    c_ids = candidates_df['candidate_id'].values
    c_types = candidates_df['candidate_type'].values
    q_statuses = candidates_df['quantity_matching_status'].values

    scenario_dfs = []

    for sc_name, sc_cfg in scenarios.items():
        exch_rate = sc_cfg.get("exchange_transaction_charge_rate", 0.000021)
        sebi_rate = sc_cfg.get("sebi_rate", 0.000001)
        stamp_rate = sc_cfg.get("stamp_duty_rate", 0.00002)
        ctt_rate = sc_cfg.get("ctt_rate", 0.0001)
        gst_rate = sc_cfg.get("gst_rate", 0.18)
        brok_model = sc_cfg.get("brokerage_model", "discount_flat_or_percent_min")
        brok_flat = sc_cfg.get("brokerage_flat_per_order", 20.0)
        brok_pct = sc_cfg.get("brokerage_percent_rate", 0.0003)

        # Brokerage per side (1 order per leg entry/exit)
        if brok_model == "percentage_of_turnover":
            brok_side_a = notional_a * brok_pct
            brok_side_b = notional_b * brok_pct
        else:
            brok_side_a = np.minimum(brok_flat, notional_a * brok_pct)
            brok_side_b = np.minimum(brok_flat, notional_b * brok_pct)

        total_brok_a = 2.0 * brok_side_a
        total_brok_b = 2.0 * brok_side_b

        # Exchange fees
        exch_a = 2.0 * notional_a * exch_rate
        exch_b = 2.0 * notional_b * exch_rate
        total_exch = exch_a + exch_b

        # SEBI fees
        sebi_a = 2.0 * notional_a * sebi_rate
        sebi_b = 2.0 * notional_b * sebi_rate
        total_sebi = sebi_a + sebi_b

        # Statutory Taxes: Stamp duty on Buy, CTT on Sell
        stamp_a = notional_a * stamp_rate
        stamp_b = notional_b * stamp_rate
        total_stamp = stamp_a + stamp_b

        ctt_a = notional_a * ctt_rate
        ctt_b = notional_b * ctt_rate
        total_ctt = ctt_a + ctt_b

        # GST on service fees
        gst_a = (total_brok_a + exch_a + sebi_a) * gst_rate
        gst_b = (total_brok_b + exch_b + sebi_b) * gst_rate
        total_gst = gst_a + gst_b

        total_brok = total_brok_a + total_brok_b
        total_cost_a = total_brok_a + exch_a + sebi_a + stamp_a + ctt_a + gst_a
        total_cost_b = total_brok_b + exch_b + sebi_b + stamp_b + ctt_b + gst_b
        total_round_trip = total_cost_a + total_cost_b

        # Entry and Exit breakdown based on spread trade orientation:
        # In a spread position, one leg is sold and the other leg is bought on entry.
        # Calendar spreads: Nearer (Leg A) is SELL on entry; Deferred (Leg B) is BUY on entry.
        # Cross-product pairs: If gross_spread >= 0, Leg A is SELL and Leg B is BUY on entry;
        #                      If gross_spread < 0, Leg A is BUY and Leg B is SELL on entry.
        leg_a_sell_entry = np.where(is_cal, True, gross_spread >= 0)
        leg_b_sell_entry = ~leg_a_sell_entry

        tax_entry_a = np.where(leg_a_sell_entry, ctt_a, stamp_a)
        tax_exit_a = np.where(leg_a_sell_entry, stamp_a, ctt_a)
        tax_entry_b = np.where(leg_b_sell_entry, ctt_b, stamp_b)
        tax_exit_b = np.where(leg_b_sell_entry, stamp_b, ctt_b)

        service_side_a = brok_side_a + (notional_a * exch_rate) + (notional_a * sebi_rate)
        gst_side_a = service_side_a * gst_rate
        service_side_b = brok_side_b + (notional_b * exch_rate) + (notional_b * sebi_rate)
        gst_side_b = service_side_b * gst_rate

        entry_a = service_side_a + gst_side_a + tax_entry_a
        exit_a = service_side_a + gst_side_a + tax_exit_a
        entry_b = service_side_b + gst_side_b + tax_entry_b
        exit_b = service_side_b + gst_side_b + tax_exit_b

        total_entry = entry_a + entry_b
        total_exit = exit_a + exit_b

        cost_per_gram = total_round_trip / matched_exposure_grams

        # Net spread calculation
        net_spread = np.where(
            is_cal,
            gross_spread - cost_per_gram,
            np.abs(gross_spread) - cost_per_gram
        )
        gross_exceeds = np.where(
            is_avail,
            np.where(is_cal, gross_spread > cost_per_gram, np.abs(gross_spread) > cost_per_gram),
            False
        )

        unavail_reason = np.where(
            is_avail,
            'NONE',
            'Costs unavailable due to: ' + candidates_df['cost_model_status']
        )

        sc_df = pd.DataFrame({
            'candidate_id': c_ids,
            'candidate_type': c_types,
            'scenario_name': sc_name,
            'config_version': cfg_version,
            'matched_lots_leg_a': matched_lots_a,
            'matched_lots_leg_b': matched_lots_b,
            'exposure_grams_leg_a': np.where(is_cal, tu_a, matched_exposure_grams),
            'exposure_grams_leg_b': np.where(is_cal, tu_b, matched_exposure_grams),
            'notional_inr_leg_a': np.round(notional_a, 2),
            'notional_inr_leg_b': np.round(notional_b, 2),
            'combined_notional_inr': np.round(comb_notional, 2),
            'entry_cost_inr_leg_a': np.round(entry_a, 4),
            'entry_cost_inr_leg_b': np.round(entry_b, 4),
            'total_entry_cost_inr': np.round(total_entry, 4),
            'exit_cost_inr_leg_a': np.round(exit_a, 4),
            'exit_cost_inr_leg_b': np.round(exit_b, 4),
            'total_exit_cost_inr': np.round(total_exit, 4),
            'total_round_trip_cost_inr': np.round(total_round_trip, 4),
            'exchange_fee_inr': np.round(total_exch, 4),
            'sebi_fee_inr': np.round(total_sebi, 4),
            'stamp_duty_inr': np.round(total_stamp, 4),
            'ctt_inr': np.round(total_ctt, 4),
            'brokerage_inr': np.round(total_brok, 4),
            'gst_inr': np.round(total_gst, 4),
            'modeled_round_trip_cost_per_gram': np.round(cost_per_gram, 6),
            'gross_spread_per_gram': np.round(gross_spread, 6),
            'modeled_net_spread_per_gram': np.round(net_spread, 6),
            'gross_exceeds_modeled_costs': gross_exceeds,
            'quantity_matching_status': q_statuses,
            'cost_model_status': np.where(is_avail, 'available', cost_status),
            'unavailable_reason': unavail_reason
        })

        scenario_dfs.append(sc_df)

    return pd.concat(scenario_dfs, ignore_index=True)

def run_pipeline(
    output_dir: str = DATA_DIR,
    config_dir: str = CONFIG_DIR
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Execute the full Phase 5 screening and transaction-cost modeling pipeline."""
    print("================================================================================", flush=True)
    print("Gold Contract Radar — Phase 5: Liquidity & Transaction Cost Filters Engine", flush=True)
    print("================================================================================", flush=True)
    
    # 1. Load inputs
    print("[1/5] Loading configurations and verified inputs...", flush=True)
    specs_cfg, liq_cfg, costs_cfg = load_configurations(config_dir)
    norm_df, radar_df, term_df = load_input_datasets(output_dir)
    print(f"      Normalized records: {len(norm_df):,} | Radar pairs: {len(radar_df):,} | Calendar spreads: {len(term_df):,}", flush=True)

    # 2. Screen candidates
    print("[2/5] Screening candidates against data eligibility, expiry, and liquidity filters...", flush=True)
    candidates_df = screen_candidates(radar_df, term_df, norm_df, liq_cfg, specs_cfg)
    print(f"      Total candidates screened: {len(candidates_df):,}", flush=True)
    print(f"      Data eligible candidates: {candidates_df['is_both_data_eligible'].sum():,}", flush=True)
    print(f"      Passing expiry filter:    {candidates_df['passes_expiry_filter'].sum():,}", flush=True)
    print(f"      Passing volume filter:    {candidates_df['passes_volume_filter'].sum():,}", flush=True)
    print(f"      Passing open int filter:  {candidates_df['passes_open_interest_filter'].sum():,}", flush=True)
    print(f"      Passing all filters:      {candidates_df['is_all_filters_eligible'].sum():,}", flush=True)

    # 3. Model transaction costs across scenarios
    print("[3/5] Modeling transaction costs across configured scenarios (base, low, high)...", flush=True)
    scenarios_df = model_transaction_costs(candidates_df, costs_cfg, specs_cfg)
    print(f"      Total scenario calculations: {len(scenarios_df):,}", flush=True)
    base_sc = scenarios_df[scenarios_df['scenario_name'] == 'base']
    base_exceeds = (base_sc['gross_exceeds_modeled_costs'] & base_sc['candidate_id'].isin(
        candidates_df[candidates_df['is_all_filters_eligible']]['candidate_id']
    )).sum()
    print(f"      Eligible candidates where gross spread exceeds base costs: {base_exceeds:,}", flush=True)

    # 4. Extract eligible candidates subset (Output C)
    print("[4/5] Extracting eligible candidate subset...", flush=True)
    eligible_df = candidates_df[candidates_df['is_all_filters_eligible']].copy()
    print(f"      Eligible candidate rows: {len(eligible_df):,}", flush=True)

    # 5. Save outputs
    print("[5/5] Exporting Phase 5 datasets to data/processed/...", flush=True)
    out_a_path = os.path.join(output_dir, "mcx_gold_liquidity_filtered_candidates.csv")
    out_b_path = os.path.join(output_dir, "mcx_gold_transaction_cost_scenarios.csv")
    out_c_path = os.path.join(output_dir, "mcx_gold_eligible_candidates.csv")

    candidates_df.to_csv(out_a_path, index=False)
    print(f"      [PASS] Output A saved: {out_a_path} ({len(candidates_df):,} rows)", flush=True)

    scenarios_df.to_csv(out_b_path, index=False)
    print(f"      [PASS] Output B saved: {out_b_path} ({len(scenarios_df):,} rows)", flush=True)

    eligible_df.to_csv(out_c_path, index=False)
    print(f"      [PASS] Output C saved: {out_c_path} ({len(eligible_df):,} rows)", flush=True)

    print("================================================================================", flush=True)
    print("Phase 5 Pipeline Execution Complete.", flush=True)
    print("================================================================================", flush=True)

    return candidates_df, scenarios_df, eligible_df

if __name__ == "__main__":
    run_pipeline()
