"""
Gold Contract Radar — MCX Commodity Derivatives Intelligence
Data Loading, Caching, and Validation Module for Streamlit Dashboard
"""

import os
import json
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")

# --- Configuration Loaders ---

@st.cache_data(show_spinner=False)
def load_contract_specs(config_dir: str = CONFIG_DIR) -> Dict[str, Any]:
    """Load MCX gold contract specifications configuration."""
    p = os.path.join(config_dir, "contract_specs.json")
    if not os.path.exists(p):
        raise FileNotFoundError(f"Missing required config file: {p}")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data(show_spinner=False)
def load_backtest_config(config_dir: str = CONFIG_DIR) -> Dict[str, Any]:
    """Load walk-forward backtest configuration."""
    p = os.path.join(config_dir, "backtest_config.json")
    if not os.path.exists(p):
        raise FileNotFoundError(f"Missing required config file: {p}")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data(show_spinner=False)
def load_transaction_costs_config(config_dir: str = CONFIG_DIR) -> Dict[str, Any]:
    """Load transaction cost scenarios configuration."""
    p = os.path.join(config_dir, "transaction_costs.json")
    if not os.path.exists(p):
        raise FileNotFoundError(f"Missing required config file: {p}")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data(show_spinner=False)
def load_liquidity_filters_config(config_dir: str = CONFIG_DIR) -> Dict[str, Any]:
    """Load liquidity filter parameters configuration."""
    p = os.path.join(config_dir, "liquidity_filters.json")
    if not os.path.exists(p):
        raise FileNotFoundError(f"Missing required config file: {p}")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

# --- Dataset Loaders with Validation ---

def _safe_load_csv(filename: str, required_cols: Optional[List[str]] = None, parse_dates: Optional[List[str]] = None) -> pd.DataFrame:
    """Helper to safely load a CSV file, validate columns, and return an immutable copy."""
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Required production dataset '{filename}' not found at {filepath}")
    
    df = pd.read_csv(filepath, low_memory=False)
    if df.empty:
        raise ValueError(f"Dataset '{filename}' is empty.")
        
    if required_cols:
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Dataset '{filename}' is missing required columns: {missing}")
            
    if parse_dates:
        for c in parse_dates:
            if c in df.columns:
                df[c] = pd.to_datetime(df[c], errors='coerce')
                
    return df.copy()

@st.cache_data(show_spinner=False)
def load_normalized_data() -> pd.DataFrame:
    """Load Phase 3 normalized market data."""
    req = ['date', 'symbol', 'expiry_date', 'contract_key', 'open', 'high', 'low', 'close',
           'volume_lots', 'open_interest_lots', 'open_per_gram', 'close_per_gram',
           'open_fine_per_gram', 'close_fine_per_gram', 'is_executable_traded']
    df = _safe_load_csv("mcx_gold_normalized.csv", required_cols=req)
    df['date'] = pd.to_datetime(df['date'])
    df['expiry_date'] = pd.to_datetime(df['expiry_date'])
    if 'days_to_expiry' not in df.columns:
        df['days_to_expiry'] = (df['expiry_date'] - df['date']).dt.days
    return df

@st.cache_data(show_spinner=False)
def load_relative_price_radar() -> pd.DataFrame:
    """Load Phase 4 relative price radar cross-product dataset."""
    req = ['date', 'pair_type', 'symbol_a', 'symbol_b', 'expiry_a',
           'quoted_price_difference_per_gram', 'fine_price_difference_per_gram',
           'fine_relative_difference_pct', 'is_both_executable']
    df = _safe_load_csv("mcx_gold_relative_price_radar.csv", required_cols=req)
    df['date'] = pd.to_datetime(df['date'])
    df['expiry_date'] = pd.to_datetime(df['expiry_a'])
    
    # Provide alias columns for backward compatibility with candidate views
    if 'symbol_leg_a' not in df.columns:
        df['symbol_leg_a'] = df['symbol_a']
    if 'symbol_leg_b' not in df.columns:
        df['symbol_leg_b'] = df['symbol_b']
    if 'quoted_price_spread_per_gram' not in df.columns:
        df['quoted_price_spread_per_gram'] = df['quoted_price_difference_per_gram']
    if 'fine_price_spread_per_gram' not in df.columns:
        df['fine_price_spread_per_gram'] = df['fine_price_difference_per_gram']
    if 'fine_relative_spread_pct' not in df.columns:
        df['fine_relative_spread_pct'] = df['fine_relative_difference_pct']
    if 'is_both_executable_traded' not in df.columns:
        df['is_both_executable_traded'] = df['is_both_executable']
        
    return df

@st.cache_data(show_spinner=False)
def load_term_structure() -> pd.DataFrame:
    """Load Phase 4 term structure and calendar spreads dataset."""
    req = ['date', 'symbol', 'nearer_expiry', 'deferred_expiry',
           'calendar_days_between_expiries', 'quoted_calendar_spread_per_gram',
           'fine_calendar_spread_per_gram', 'fine_annualized_spread_pct', 'is_both_executable']
    df = _safe_load_csv("mcx_gold_term_structure.csv", required_cols=req)
    df['date'] = pd.to_datetime(df['date'])
    df['expiry_date_near'] = pd.to_datetime(df['nearer_expiry'])
    df['expiry_date_far'] = pd.to_datetime(df['deferred_expiry'])
    
    # Provide alias columns for backward compatibility
    if 'quoted_price_spread_per_gram' not in df.columns:
        df['quoted_price_spread_per_gram'] = df['quoted_calendar_spread_per_gram']
    if 'fine_price_spread_per_gram' not in df.columns:
        df['fine_price_spread_per_gram'] = df['fine_calendar_spread_per_gram']
    if 'term_structure_slope' not in df.columns:
        df['term_structure_slope'] = df['fine_calendar_spread_per_gram'] / df['calendar_days_between_expiries'].clip(lower=1)
    if 'slope_regime' not in df.columns:
        df['slope_regime'] = df['fine_annualized_spread_pct'].apply(
            lambda x: 'Contango' if x > 0 else ('Backwardation' if x < 0 else 'Flat')
        )
    return df

@st.cache_data(show_spinner=False)
def load_term_structure_snapshots() -> pd.DataFrame:
    """Load Phase 4 term structure snapshots dataset."""
    req = ['date', 'symbol', 'expiry_date', 'days_to_expiry', 'close_fine_per_gram']
    df = _safe_load_csv("mcx_gold_term_structure_snapshots.csv", required_cols=req)
    df['date'] = pd.to_datetime(df['date'])
    df['expiry_date'] = pd.to_datetime(df['expiry_date'])
    
    # Derive contract key and expiry rank if missing
    if 'contract_key' not in df.columns:
        df['contract_key'] = df['symbol'] + "_" + df['expiry_date'].dt.strftime('%d%b%Y').str.upper()
    if 'expiry_rank' not in df.columns:
        df['expiry_rank'] = df.groupby(['date', 'symbol'])['days_to_expiry'].rank(method='dense').astype(int)
        
    return df

@st.cache_data(show_spinner=False)
def load_liquidity_filtered_candidates() -> pd.DataFrame:
    """Load Phase 5 liquidity-filtered candidates dataset."""
    req = ['candidate_id', 'candidate_type', 'date', 'symbol_leg_a', 'symbol_leg_b',
           'passes_liquidity_filter', 'is_all_filters_eligible', 'exclusion_reasons']
    df = _safe_load_csv("mcx_gold_liquidity_filtered_candidates.csv", required_cols=req)
    df['date'] = pd.to_datetime(df['date'])
    return df

@st.cache_data(show_spinner=False)
def load_transaction_cost_scenarios() -> pd.DataFrame:
    """Load Phase 5 transaction cost scenarios dataset."""
    req = ['candidate_id', 'candidate_type', 'scenario_name', 'matched_lots_leg_a',
           'matched_lots_leg_b', 'total_round_trip_cost_inr', 'modeled_round_trip_cost_per_gram',
           'gross_spread_per_gram', 'modeled_net_spread_per_gram', 'gross_exceeds_modeled_costs',
           'quantity_matching_status', 'cost_model_status']
    return _safe_load_csv("mcx_gold_transaction_cost_scenarios.csv", required_cols=req)

@st.cache_data(show_spinner=False)
def load_eligible_candidates() -> pd.DataFrame:
    """Load Phase 5 fully eligible candidates dataset."""
    req = ['candidate_id', 'candidate_type', 'date', 'symbol_leg_a', 'symbol_leg_b',
           'contract_key_leg_a', 'contract_key_leg_b', 'fine_price_spread_per_gram',
           'is_all_filters_eligible']
    df = _safe_load_csv("mcx_gold_eligible_candidates.csv", required_cols=req)
    df['date'] = pd.to_datetime(df['date'])
    return df

@st.cache_data(show_spinner=False)
def load_backtest_trades() -> pd.DataFrame:
    """Load Phase 6 simulated trades ledger."""
    req = ['trade_id', 'candidate_id', 'strategy_name', 'signal_date', 'entry_date',
           'exit_date', 'fold_id', 'symbol_leg_a', 'symbol_leg_b', 'matched_exposure_grams',
           'signal_direction', 'gross_pnl_inr', 'total_modeled_cost_inr', 'net_pnl_inr',
           'cost_scenario', 'trade_completion_status', 'rejection_or_exclusion_reason']
    df = _safe_load_csv("mcx_gold_backtest_trades.csv", required_cols=req)
    df['signal_date'] = pd.to_datetime(df['signal_date'])
    df['entry_date'] = pd.to_datetime(df['entry_date'])
    df['exit_date'] = pd.to_datetime(df['exit_date'])
    return df

@st.cache_data(show_spinner=False)
def load_walk_forward_metrics() -> pd.DataFrame:
    """Load Phase 6 walk-forward fold metrics."""
    req = ['fold_id', 'strategy_name', 'cost_scenario', 'train_start_date', 'train_end_date',
           'test_start_date', 'test_end_date', 'trade_attempts', 'completed_trades',
           'rejected_trades', 'winning_trades', 'losing_trades', 'win_rate_pct',
           'gross_pnl_inr', 'total_costs_inr', 'net_pnl_inr', 'profit_factor',
           'realized_max_drawdown_inr', 'mean_holding_days']
    return _safe_load_csv("mcx_gold_walk_forward_metrics.csv", required_cols=req)

@st.cache_data(show_spinner=False)
def load_backtest_summary() -> pd.DataFrame:
    """Load Phase 6 strategy summary performance metrics."""
    req = ['strategy_name', 'cost_scenario', 'total_trade_attempts', 'completed_trades',
           'rejected_trades', 'win_rate_pct', 'gross_pnl_inr', 'total_costs_inr',
           'net_pnl_inr', 'mean_net_pnl_per_trade_inr', 'profit_factor',
           'realized_max_drawdown_inr', 'mean_holding_days']
    return _safe_load_csv("mcx_gold_backtest_summary.csv", required_cols=req)

@st.cache_data(show_spinner=False)
def load_execution_diagnostics() -> pd.DataFrame:
    """Load Phase 6 execution diagnostics breakdown."""
    req = ['diagnostic_category', 'metric_name', 'count', 'description']
    return _safe_load_csv("mcx_gold_execution_diagnostics.csv", required_cols=req)

def get_dataset_inventory() -> List[Dict[str, Any]]:
    """Return status inventory for all 12 Phase 1-6 production datasets."""
    files = [
        ("mcx_gold_master.csv", "Phase 2 Master Dataset"),
        ("mcx_gold_normalized.csv", "Phase 3 Normalized Market Data"),
        ("mcx_gold_relative_price_radar.csv", "Phase 4 Relative Price Radar"),
        ("mcx_gold_term_structure.csv", "Phase 4 Calendar Spreads & Term Structure"),
        ("mcx_gold_term_structure_snapshots.csv", "Phase 4 Expiry Curve Snapshots"),
        ("mcx_gold_liquidity_filtered_candidates.csv", "Phase 5 Liquidity Screened Candidates"),
        ("mcx_gold_transaction_cost_scenarios.csv", "Phase 5 Transaction Cost Scenarios"),
        ("mcx_gold_eligible_candidates.csv", "Phase 5 Fully Eligible Candidates"),
        ("mcx_gold_backtest_trades.csv", "Phase 6 Walk-Forward Simulated Trades Ledger"),
        ("mcx_gold_walk_forward_metrics.csv", "Phase 6 Walk-Forward Fold Metrics"),
        ("mcx_gold_backtest_summary.csv", "Phase 6 Strategy Performance Summary"),
        ("mcx_gold_execution_diagnostics.csv", "Phase 6 Execution Diagnostics & Overlap Audit")
    ]
    inventory = []
    for fn, desc in files:
        fp = os.path.join(DATA_DIR, fn)
        exists = os.path.exists(fp)
        sz = os.path.getsize(fp) if exists else 0
        rows = 0
        if exists:
            try:
                # Fast row count
                with open(fp, 'r', encoding='utf-8') as f:
                    rows = sum(1 for _ in f) - 1
            except Exception:
                rows = -1
        inventory.append({
            'filename': fn,
            'description': desc,
            'exists': exists,
            'size_bytes': sz,
            'rows': rows,
            'status': "ONLINE" if exists else "MISSING"
        })
    return inventory
