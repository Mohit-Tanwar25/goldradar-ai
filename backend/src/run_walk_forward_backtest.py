"""
Gold Contract Radar — MCX Commodity Derivatives Intelligence
Phase 6: Walk-Forward Backtesting Engine (Audited & Refined)

This module implements a strictly leakage-free, chronological walk-forward
backtest evaluating:
1. Strategy A: Same-Expiry Cross-Product Price Differences
2. Strategy B: Same-Symbol Calendar Spreads

Key Architectural Principles:
- Strict Chronological Ordering: Decision at date t close -> Execution at date t+1 OPEN.
- Two-Leg Execution Enforcement: Both legs must have valid, positive traded volume and complete OHLC at next-session open.
- Position Overlap Enforcement: Active positions track pair occupancies; concurrent trades on the same pair are rejected.
- Minimum Training History Rule: Pairs or symbols with < 20 training samples in the fold's training window are quarantined.
- Strict Open Exit Execution: Exits occur strictly at OPEN. Unexecutable boundary exits are marked UNRESOLVED with NaN P&L.
- Dynamic Transaction Costs: Recalculated from simulated entry and exit open prices across 'base', 'low', and 'high' fee scenarios.
"""

import os
import sys
import json
import math
from datetime import datetime
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from typing import Dict, Any, Tuple, List, Optional
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")

def load_all_configs(config_dir: str = CONFIG_DIR) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Load and validate all configuration files."""
    specs_p = os.path.join(config_dir, "contract_specs.json")
    liq_p = os.path.join(config_dir, "liquidity_filters.json")
    costs_p = os.path.join(config_dir, "transaction_costs.json")
    bt_p = os.path.join(config_dir, "backtest_config.json")

    for p in [specs_p, liq_p, costs_p, bt_p]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Missing required config file: {p}")

    with open(specs_p, 'r', encoding='utf-8') as f:
        specs_cfg = json.load(f)
    with open(liq_p, 'r', encoding='utf-8') as f:
        liq_cfg = json.load(f)
    with open(costs_p, 'r', encoding='utf-8') as f:
        costs_cfg = json.load(f)
    with open(bt_p, 'r', encoding='utf-8') as f:
        bt_cfg = json.load(f)

    return specs_cfg, liq_cfg, costs_cfg, bt_cfg

def load_data(data_dir: str = DATA_DIR) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load normalized market data and eligible candidates."""
    norm_p = os.path.join(data_dir, "mcx_gold_normalized.csv")
    elig_p = os.path.join(data_dir, "mcx_gold_eligible_candidates.csv")

    for p in [norm_p, elig_p]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Missing required dataset: {p}")

    norm_df = pd.read_csv(norm_p)
    elig_df = pd.read_csv(elig_p)
    return norm_df, elig_df

def compute_walk_forward_folds(
    all_dates: List[str],
    train_months: int = 6,
    test_months: int = 3,
    step_months: int = 3
) -> List[Dict[str, Any]]:
    """Generate strictly chronological, rolling walk-forward fold date boundaries."""
    min_date = pd.to_datetime(all_dates[0])
    max_date = pd.to_datetime(all_dates[-1])

    folds = []
    cur_start = min_date
    fold_idx = 1

    while True:
        train_end = cur_start + relativedelta(months=train_months) - relativedelta(days=1)
        test_start = cur_start + relativedelta(months=train_months)
        test_end = test_start + relativedelta(months=test_months) - relativedelta(days=1)

        if test_start > max_date:
            break
        if test_end > max_date:
            test_end = max_date

        tr_dates = [d for d in all_dates if cur_start.strftime('%Y-%m-%d') <= d <= train_end.strftime('%Y-%m-%d')]
        te_dates = [d for d in all_dates if test_start.strftime('%Y-%m-%d') <= d <= test_end.strftime('%Y-%m-%d')]

        if len(tr_dates) >= 20 and len(te_dates) >= 5:
            folds.append({
                'fold_id': f"FOLD_{fold_idx:02d}",
                'train_start_date': tr_dates[0],
                'train_end_date': tr_dates[-1],
                'train_sessions': len(tr_dates),
                'test_start_date': te_dates[0],
                'test_end_date': te_dates[-1],
                'test_sessions': len(te_dates)
            })
            fold_idx += 1

        cur_start = cur_start + relativedelta(months=step_months)

    return folds

def calculate_single_leg_cost(
    turnover: float,
    side: str,
    scenario_cfg: Dict[str, Any]
) -> Dict[str, float]:
    """Calculate actual transaction cost for a single trade leg execution."""
    if np.isnan(turnover) or turnover <= 0:
        return {
            'turnover': 0.0, 'brokerage': 0.0, 'exchange_fee': 0.0,
            'sebi_fee': 0.0, 'stamp_duty': 0.0, 'ctt': 0.0, 'gst': 0.0, 'total_cost': 0.0
        }

    exch_rate = scenario_cfg.get("exchange_transaction_charge_rate", 0.000021)
    sebi_rate = scenario_cfg.get("sebi_rate", 0.000001)
    stamp_rate = scenario_cfg.get("stamp_duty_rate", 0.00002)
    ctt_rate = scenario_cfg.get("ctt_rate", 0.0001)
    gst_rate = scenario_cfg.get("gst_rate", 0.18)
    brok_model = scenario_cfg.get("brokerage_model", "discount_flat_or_percent_min")
    brok_flat = scenario_cfg.get("brokerage_flat_per_order", 20.0)
    brok_pct = scenario_cfg.get("brokerage_percent_rate", 0.0003)

    if brok_model == "percentage_of_turnover":
        brokerage = turnover * brok_pct
    else:
        brokerage = min(brok_flat, turnover * brok_pct)

    exchange_fee = turnover * exch_rate
    sebi_fee = turnover * sebi_rate
    stamp_duty = turnover * stamp_rate if side.lower() == "buy" else 0.0
    ctt = turnover * ctt_rate if side.lower() == "sell" else 0.0
    gst = (brokerage + exchange_fee + sebi_fee) * gst_rate
    total_cost = brokerage + exchange_fee + sebi_fee + stamp_duty + ctt + gst

    return {
        'turnover': turnover,
        'brokerage': brokerage,
        'exchange_fee': exchange_fee,
        'sebi_fee': sebi_fee,
        'stamp_duty': stamp_duty,
        'ctt': ctt,
        'gst': gst,
        'total_cost': total_cost
    }

def run_backtest_simulation() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Execute complete leakage-free walk-forward backtest across all folds."""
    specs_cfg, liq_cfg, costs_cfg, bt_cfg = load_all_configs()
    norm_df, elig_df = load_data()

    contracts_meta = specs_cfg.get("contracts", {})
    cost_scenarios = costs_cfg.get("scenarios", {})
    exec_rules = bt_cfg.get("execution_rules", {})
    max_holding_period = exec_rules.get("max_holding_period_days", 10)
    tender_safety_dte = exec_rules.get("tender_safety_exit_dte", 5)
    allow_overlap = exec_rules.get("allow_overlapping_positions", False)

    exposure_limits = bt_cfg.get("portfolio_exposure_limits", {})
    allow_shared_contract_overlap = exposure_limits.get("allow_shared_contract_overlap", False)
    max_concurrent_positions_per_contract = exposure_limits.get("max_concurrent_positions_per_contract", 1)
    max_gross_lots_per_contract = exposure_limits.get("max_gross_lots_per_contract", 10)
    max_net_lots_per_contract = exposure_limits.get("max_net_lots_per_contract", 10)
    max_underlying_grams_per_contract = exposure_limits.get("max_underlying_grams_per_contract", 1000)
    allow_multi_strategy_sharing = exposure_limits.get("allow_multi_strategy_contract_sharing", False)
    allow_opposing_positions = exposure_limits.get("allow_opposing_contract_positions", False)

    # Build fast O(1) market data index from normalized records
    # Key: (contract_key, date) -> dict of row values
    norm_indexed = {}
    for _, row in norm_df.iterrows():
        key = (row['contract_key'], row['date'])
        norm_indexed[key] = {
            'open_per_gram': row['open_per_gram'],
            'close_per_gram': row['close_per_gram'],
            'volume_lots': row['volume_lots'],
            'open_interest_lots': row['open_interest_lots'],
            'is_executable_traded': bool(row['is_executable_traded']),
            'flag_missing_ohlc': bool(row['flag_missing_ohlc']),
            'flag_zero_volume': bool(row['flag_zero_volume']),
            'days_to_expiry': (pd.to_datetime(row['expiry_date']) - pd.to_datetime(row['date'])).days
        }

    all_trading_dates = sorted(norm_df['date'].unique())
    date_to_idx = {d: i for i, d in enumerate(all_trading_dates)}

    # Generate walk-forward folds
    wf_splits = bt_cfg.get("walk_forward_splits", {})
    min_training_samples = wf_splits.get("min_training_samples", 20)

    folds = compute_walk_forward_folds(
        all_trading_dates,
        train_months=wf_splits.get("training_window_months", 6),
        test_months=wf_splits.get("test_window_months", 3),
        step_months=wf_splits.get("step_size_months", 3)
    )

    print(f"Generated {len(folds)} Chronological Walk-Forward Folds.")

    # Storage for output tables
    all_trade_records = []
    diagnostics_counts = {
        'total_candidates_screened': 0,
        'candidates_in_test_windows': 0,
        'signals_triggered': 0,
        'rejected_existing_contract_position': 0,
        'rejected_multi_strategy_contract_conflict': 0,
        'rejected_opposing_contract_position': 0,
        'rejected_gross_exposure_limit': 0,
        'rejected_net_exposure_limit': 0,
        'rejected_contract_gram_limit': 0,
        'rejected_existing_active_position': 0,
        'rejected_insufficient_training_history': 0,
        'rejected_missing_next_session': 0,
        'rejected_missing_next_open_leg_a': 0,
        'rejected_missing_next_open_leg_b': 0,
        'rejected_zero_volume_next_session_leg_a': 0,
        'rejected_zero_volume_next_session_leg_b': 0,
        'rejected_non_executable_next_session': 0,
        'rejected_tender_window_at_entry': 0,
        'rejected_fold_boundary_censored': 0,
        'trades_filled': 0,
        'trades_completed': 0,
        'trades_unresolved': 0,
        'exits_due_to_max_holding': 0,
        'exits_due_to_tender_safety': 0,
        'exits_due_to_fold_boundary': 0
    }

    # Process each fold chronologically
    for fold in folds:
        fid = fold['fold_id']
        tr_start, tr_end = fold['train_start_date'], fold['train_end_date']
        te_start, te_end = fold['test_start_date'], fold['test_end_date']

        print(f"\nProcessing {fid}: Train [{tr_start} to {tr_end}] -> Test [{te_start} to {te_end}]")

        # 1. Train Window: Fit Signal Thresholds strictly on training data
        tr_cands = elig_df[(elig_df['date'] >= tr_start) & (elig_df['date'] <= tr_end)]
        tr_radar = tr_cands[tr_cands['candidate_type'] == 'same_expiry_cross_product']
        tr_cal = tr_cands[tr_cands['candidate_type'] == 'same_symbol_calendar_spread']

        # Sample counts per pair/symbol for training history verification
        tr_rad_pairs = tr_radar.groupby(['symbol_leg_a', 'symbol_leg_b']).size().to_dict()
        tr_cal_symbols = tr_cal.groupby('symbol_leg_a').size().to_dict()

        # Threshold Strategy A: 75th percentile of spread magnitude
        if len(tr_radar) > 10:
            strat_a_threshold = float(np.percentile(np.abs(tr_radar['fine_price_spread_per_gram'].dropna()), 75.0))
        else:
            strat_a_threshold = 20.0

        # Threshold Strategy B: 75th percentile of annualized spread
        if len(tr_cal) > 10:
            strat_b_upper = float(np.percentile(tr_cal['fine_annualized_spread_pct'].dropna(), 75.0))
            strat_b_lower = float(np.percentile(tr_cal['fine_annualized_spread_pct'].dropna(), 25.0))
        else:
            strat_b_upper = 12.0
            strat_b_lower = 5.0

        print(f"  Fitted Thresholds: Strat A Spread >= Rs.{strat_a_threshold:.2f}/g | Strat B Contango >= {strat_b_upper:.2f}% (Lower: {strat_b_lower:.2f}%)")

        # 2. Test Window: Evaluate candidates strictly in test window
        te_cands = elig_df[(elig_df['date'] >= te_start) & (elig_df['date'] <= te_end)].copy()
        diagnostics_counts['candidates_in_test_windows'] += len(te_cands)

        # Pre-score candidates deterministically for tie-breaking
        scored_candidates = []
        for cand in te_cands.to_dict('records'):
            ctype = cand['candidate_type']
            if ctype == 'same_expiry_cross_product':
                strat_name = "strategy_a_cross_product"
                sig_metric_val = cand['fine_price_spread_per_gram']
                threshold_val = strat_a_threshold
                if sig_metric_val >= strat_a_threshold:
                    signal_triggered = True
                    signal_direction = "SELL_A_BUY_B"
                elif sig_metric_val <= -strat_a_threshold:
                    signal_triggered = True
                    signal_direction = "BUY_A_SELL_B"
                else:
                    signal_triggered = False
                    signal_direction = None
                strength = abs(sig_metric_val) / strat_a_threshold if strat_a_threshold > 0 else 0.0
            else:
                strat_name = "strategy_b_calendar_spread"
                sig_metric_val = cand['fine_annualized_spread_pct']
                threshold_val = strat_b_upper
                if sig_metric_val >= strat_b_upper:
                    signal_triggered = True
                    signal_direction = "SELL_B_BUY_A"
                else:
                    signal_triggered = False
                    signal_direction = None
                strength = sig_metric_val / strat_b_upper if strat_b_upper > 0 else 0.0

            cand['strat_name'] = strat_name
            cand['sig_metric_val'] = sig_metric_val
            cand['threshold_val'] = threshold_val
            cand['signal_triggered'] = signal_triggered
            cand['signal_direction'] = signal_direction
            cand['strength'] = strength
            scored_candidates.append(cand)

        # Sort deterministically: date ASC, strength DESC (higher relative deviation prioritized), candidate_id ASC
        scored_candidates.sort(key=lambda x: (x['date'], -x['strength'], x['candidate_id']))

        # Contract-level active position tracking across the entire portfolio:
        # Key: contract_key -> list of active position records
        active_contract_positions = defaultdict(list)

        for cand in scored_candidates:
            diagnostics_counts['total_candidates_screened'] += 1
            cid = cand['candidate_id']
            ctype = cand['candidate_type']
            strat_name = cand['strat_name']
            sig_date = cand['date']
            sig_metric_val = cand['sig_metric_val']
            threshold_val = cand['threshold_val']
            signal_triggered = cand['signal_triggered']
            signal_direction = cand['signal_direction']
            sig_idx = date_to_idx.get(sig_date)

            if sig_idx is None or sig_idx + 1 >= len(all_trading_dates):
                continue  # End of dataset

            sym_a = cand['symbol_leg_a']
            sym_b = cand['symbol_leg_b']
            key_a = cand['contract_key_leg_a']
            key_b = cand['contract_key_leg_b']
            u_a = contracts_meta[sym_a]['trading_unit_grams']
            u_b = contracts_meta[sym_b]['trading_unit_grams']

            # Determine Matched Lots and Exposure
            if ctype == 'same_symbol_calendar_spread':
                lots_a = 1
                lots_b = 1
                matched_grams = u_a
            else:
                lcm_g = abs(u_a * u_b) // math.gcd(int(u_a), int(u_b))
                lots_a = lcm_g // int(u_a)
                lots_b = lcm_g // int(u_b)
                matched_grams = lcm_g

            if not signal_triggered:
                continue

            diagnostics_counts['signals_triggered'] += 1

            # Entry Execution Scheduling: Date t+1 OPEN
            entry_date = all_trading_dates[sig_idx + 1]
            entry_idx = date_to_idx[entry_date]
            te_end_idx = date_to_idx[te_end]

            # 1. Prune expired active positions (exit_date < entry_date)
            # Position release timing: next session after exit
            for c_key in list(active_contract_positions.keys()):
                active_contract_positions[c_key] = [
                    p for p in active_contract_positions[c_key] if p['exit_date'] >= entry_date
                ]
                if len(active_contract_positions[c_key]) == 0:
                    del active_contract_positions[c_key]

            # Determine signed lots and leg directions for exposure tracking
            if signal_direction in ["SELL_A_BUY_B"]:
                dir_a, dir_b = "SELL", "BUY"
                signed_lots_a, signed_lots_b = -lots_a, +lots_b
            elif signal_direction in ["BUY_A_SELL_B"]:
                dir_a, dir_b = "BUY", "SELL"
                signed_lots_a, signed_lots_b = +lots_a, -lots_b
            elif signal_direction in ["SELL_B_BUY_A"]:
                dir_a, dir_b = "BUY", "SELL"
                signed_lots_a, signed_lots_b = +lots_a, -lots_b
            else:
                dir_a, dir_b = "SELL", "BUY"
                signed_lots_a, signed_lots_b = -lots_a, +lots_b

            grams_a = u_a * lots_a
            grams_b = u_b * lots_b

            rejection_reason = "NONE"

            # 2. Check Training History (Audit 5)
            if ctype == 'same_expiry_cross_product':
                n_tr_samples = tr_rad_pairs.get((sym_a, sym_b), 0)
            else:
                n_tr_samples = tr_cal_symbols.get(sym_a, 0)

            if n_tr_samples < min_training_samples:
                rejection_reason = "rejected_insufficient_training_history"
                diagnostics_counts['rejected_insufficient_training_history'] += 1

            # 3. Portfolio Exposure & Shared-Contract Overlap Checks
            if rejection_reason == "NONE":
                for leg_key, leg_dir, leg_lots, leg_signed_lots, leg_grams in [
                    (key_a, dir_a, lots_a, signed_lots_a, grams_a),
                    (key_b, dir_b, lots_b, signed_lots_b, grams_b)
                ]:
                    active_list = active_contract_positions.get(leg_key, [])
                    if len(active_list) > 0:
                        if not allow_shared_contract_overlap or len(active_list) >= max_concurrent_positions_per_contract:
                            rejection_reason = "rejected_existing_contract_position"
                            diagnostics_counts['rejected_existing_contract_position'] += 1
                            break
                        if not allow_multi_strategy_sharing and any(p['strategy_name'] != strat_name for p in active_list):
                            rejection_reason = "rejected_multi_strategy_contract_conflict"
                            diagnostics_counts['rejected_multi_strategy_contract_conflict'] += 1
                            break
                        if not allow_opposing_positions and any(p['direction'] != leg_dir for p in active_list):
                            rejection_reason = "rejected_opposing_contract_position"
                            diagnostics_counts['rejected_opposing_contract_position'] += 1
                            break
                        tot_gross = sum(p['lots'] for p in active_list) + leg_lots
                        if tot_gross > max_gross_lots_per_contract:
                            rejection_reason = "rejected_gross_exposure_limit"
                            diagnostics_counts['rejected_gross_exposure_limit'] += 1
                            break
                        tot_net = abs(sum(p['signed_lots'] for p in active_list) + leg_signed_lots)
                        if tot_net > max_net_lots_per_contract:
                            rejection_reason = "rejected_net_exposure_limit"
                            diagnostics_counts['rejected_net_exposure_limit'] += 1
                            break
                        tot_g = sum(p['grams'] for p in active_list) + leg_grams
                        if tot_g > max_underlying_grams_per_contract:
                            rejection_reason = "rejected_contract_gram_limit"
                            diagnostics_counts['rejected_contract_gram_limit'] += 1
                            break

            # 4. Next-Session Execution Feasibility
            leg_a_entry_info = norm_indexed.get((key_a, entry_date))
            leg_b_entry_info = norm_indexed.get((key_b, entry_date))

            if rejection_reason == "NONE":
                if leg_a_entry_info is None or leg_b_entry_info is None:
                    rejection_reason = "rejected_missing_next_session"
                    diagnostics_counts['rejected_missing_next_session'] += 1
                elif not leg_a_entry_info['is_executable_traded']:
                    if leg_a_entry_info['flag_zero_volume']:
                        rejection_reason = "rejected_zero_volume_next_session_leg_a"
                        diagnostics_counts['rejected_zero_volume_next_session_leg_a'] += 1
                    else:
                        rejection_reason = "rejected_missing_next_open_leg_a"
                        diagnostics_counts['rejected_missing_next_open_leg_a'] += 1
                elif not leg_b_entry_info['is_executable_traded']:
                    if leg_b_entry_info['flag_zero_volume']:
                        rejection_reason = "rejected_zero_volume_next_session_leg_b"
                        diagnostics_counts['rejected_zero_volume_next_session_leg_b'] += 1
                    else:
                        rejection_reason = "rejected_missing_next_open_leg_b"
                        diagnostics_counts['rejected_missing_next_open_leg_b'] += 1
                elif leg_a_entry_info['days_to_expiry'] <= tender_safety_dte or leg_b_entry_info['days_to_expiry'] <= tender_safety_dte:
                    rejection_reason = "rejected_tender_window_at_entry"
                    diagnostics_counts['rejected_tender_window_at_entry'] += 1
                elif entry_idx >= te_end_idx:
                    rejection_reason = "rejected_fold_boundary_censored"
                    diagnostics_counts['rejected_fold_boundary_censored'] += 1

            # If rejected, record trade attempt as REJECTED across all 3 scenarios
            if rejection_reason != "NONE":
                for sc_name in ["base", "low", "high"]:
                    trade_id = f"TRADE_{fid}_{cid}_{sc_name}"
                    all_trade_records.append({
                        'trade_id': trade_id,
                        'candidate_id': cid,
                        'candidate_type': ctype,
                        'strategy_name': strat_name,
                        'signal_date': sig_date,
                        'signal_available_at': f"{sig_date} 23:59:59",
                        'entry_date': entry_date,
                        'exit_date': np.nan,
                        'fold_id': fid,
                        'train_start_date': tr_start,
                        'train_end_date': tr_end,
                        'test_start_date': te_start,
                        'test_end_date': te_end,
                        'symbol_leg_a': sym_a,
                        'expiry_date_leg_a': cand['expiry_date_leg_a'],
                        'contract_key_leg_a': key_a,
                        'lots_leg_a': lots_a,
                        'symbol_leg_b': sym_b,
                        'expiry_date_leg_b': cand['expiry_date_leg_b'],
                        'contract_key_leg_b': key_b,
                        'lots_leg_b': lots_b,
                        'matched_exposure_grams': matched_grams,
                        'signal_metric_name': cand.get('signal_metric', 'spread'),
                        'signal_value': sig_metric_val,
                        'threshold_applied': threshold_val,
                        'signal_direction': signal_direction,
                        'entry_price_leg_a': np.nan,
                        'entry_price_leg_b': np.nan,
                        'exit_price_leg_a': np.nan,
                        'exit_price_leg_b': np.nan,
                        'execution_status_leg_a': 'REJECTED',
                        'execution_status_leg_b': 'REJECTED',
                        'overall_execution_status': 'REJECTED',
                        'rejection_or_exclusion_reason': rejection_reason,
                        'exit_trigger_reason': 'NONE',
                        'holding_period_days': 0,
                        'gross_pnl_inr': np.nan,
                        'gross_pnl_per_gram': np.nan,
                        'entry_cost_inr': np.nan,
                        'exit_cost_inr': np.nan,
                        'total_modeled_cost_inr': np.nan,
                        'total_modeled_cost_per_gram': np.nan,
                        'net_pnl_inr': np.nan,
                        'net_pnl_per_gram': np.nan,
                        'notional_exposure_inr': np.nan,
                        'cost_scenario': sc_name,
                        'cost_model_completeness': 'INCOMPLETE_REJECTED_EXECUTION',
                        'trade_completion_status': 'REJECTED'
                    })
                continue

            # Successful Entry Fill
            diagnostics_counts['trades_filled'] += 1
            p_entry_a = leg_a_entry_info['open_per_gram']
            p_entry_b = leg_b_entry_info['open_per_gram']
            notional_entry = (p_entry_a * u_a * lots_a) + (p_entry_b * u_b * lots_b)

            # Determine leg transaction sides at entry and exit
            if signal_direction in ["SELL_A_BUY_B"]:
                side_ent_a, side_ent_b = "sell", "buy"
                side_ext_a, side_ext_b = "buy", "sell"
            elif signal_direction in ["BUY_A_SELL_B"]:
                side_ent_a, side_ent_b = "buy", "sell"
                side_ext_a, side_ext_b = "sell", "buy"
            elif signal_direction in ["SELL_B_BUY_A"]:
                side_ent_a, side_ent_b = "buy", "sell"
                side_ext_a, side_ext_b = "sell", "buy"
            else:  # BUY_B_SELL_A
                side_ent_a, side_ent_b = "sell", "buy"
                side_ext_a, side_ext_b = "buy", "sell"

            # Position Monitoring: Daily Step-Forward strictly up to te_end
            holding_days = 0
            exit_date = None
            p_exit_a = np.nan
            p_exit_b = np.nan
            exit_reason = "NONE"

            for cur_idx in range(entry_idx + 1, min(entry_idx + max_holding_period + 1, te_end_idx + 1)):
                cur_date = all_trading_dates[cur_idx]
                holding_days += 1

                info_a = norm_indexed.get((key_a, cur_date))
                info_b = norm_indexed.get((key_b, cur_date))

                dte_a = info_a['days_to_expiry'] if info_a else 0
                dte_b = info_b['days_to_expiry'] if info_b else 0

                should_exit = False
                trigger = "NONE"

                if dte_a <= tender_safety_dte or dte_b <= tender_safety_dte:
                    should_exit = True
                    trigger = "expiry_tender_safety"
                    diagnostics_counts['exits_due_to_tender_safety'] += 1
                elif cur_date >= te_end:
                    should_exit = True
                    trigger = "fold_boundary_close"
                    diagnostics_counts['exits_due_to_fold_boundary'] += 1
                elif holding_days >= max_holding_period:
                    should_exit = True
                    trigger = "max_holding_period"
                    diagnostics_counts['exits_due_to_max_holding'] += 1

                if should_exit:
                    # Execute Exit at cur_date OPEN if executable
                    if info_a and info_b and info_a['is_executable_traded'] and info_b['is_executable_traded']:
                        exit_date = cur_date
                        p_exit_a = info_a['open_per_gram']
                        p_exit_b = info_b['open_per_gram']
                        exit_reason = trigger
                        break
                    else:
                        # Defer 1 session if unexecutable and not at final date
                        if cur_date >= te_end:
                            exit_date = cur_date
                            p_exit_a = np.nan
                            p_exit_b = np.nan
                            exit_reason = "unresolved_boundary_censored"
                            break
                        continue

            if exit_date is None:
                exit_date = te_end
                exit_reason = "unresolved_boundary_censored"

            # Register active contract positions across both legs
            active_contract_positions[key_a].append({
                'trade_id': f"TRADE_{fid}_{cid}",
                'strategy_name': strat_name,
                'entry_date': entry_date,
                'exit_date': exit_date,
                'direction': dir_a,
                'lots': lots_a,
                'signed_lots': signed_lots_a,
                'grams': grams_a
            })
            active_contract_positions[key_b].append({
                'trade_id': f"TRADE_{fid}_{cid}",
                'strategy_name': strat_name,
                'entry_date': entry_date,
                'exit_date': exit_date,
                'direction': dir_b,
                'lots': lots_b,
                'signed_lots': signed_lots_b,
                'grams': grams_b
            })

            # If trade has valid exit prices: Completed Trade
            if not np.isnan(p_exit_a) and not np.isnan(p_exit_b):
                diagnostics_counts['trades_completed'] += 1

                # Calculate Gross P&L
                if side_ent_a == "sell":  # Short Leg A, Long Leg B
                    pnl_a = (p_entry_a - p_exit_a) * u_a * lots_a
                else:                     # Long Leg A, Short Leg B
                    pnl_a = (p_exit_a - p_entry_a) * u_a * lots_a

                if side_ent_b == "buy":   # Long Leg B
                    pnl_b = (p_exit_b - p_entry_b) * u_b * lots_b
                else:                     # Short Leg B
                    pnl_b = (p_entry_b - p_exit_b) * u_b * lots_b

                gross_pnl_inr = pnl_a + pnl_b
                gross_pnl_per_g = gross_pnl_inr / matched_grams

                # Calculate Transaction Costs across each configured scenario
                for sc_name in ["base", "low", "high"]:
                    sc_cfg = cost_scenarios[sc_name]

                    # Entry costs
                    c_ent_a = calculate_single_leg_cost(p_entry_a * u_a * lots_a, side_ent_a, sc_cfg)
                    c_ent_b = calculate_single_leg_cost(p_entry_b * u_b * lots_b, side_ent_b, sc_cfg)
                    tot_entry_cost = c_ent_a['total_cost'] + c_ent_b['total_cost']

                    # Exit costs
                    c_ext_a = calculate_single_leg_cost(p_exit_a * u_a * lots_a, side_ext_a, sc_cfg)
                    c_ext_b = calculate_single_leg_cost(p_exit_b * u_b * lots_b, side_ext_b, sc_cfg)
                    tot_exit_cost = c_ext_a['total_cost'] + c_ext_b['total_cost']

                    total_modeled_cost = tot_entry_cost + tot_exit_cost
                    cost_per_g = total_modeled_cost / matched_grams

                    net_pnl_inr = gross_pnl_inr - total_modeled_cost
                    net_pnl_per_g = net_pnl_inr / matched_grams

                    trade_id = f"TRADE_{fid}_{cid}_{sc_name}"
                    all_trade_records.append({
                        'trade_id': trade_id,
                        'candidate_id': cid,
                        'candidate_type': ctype,
                        'strategy_name': strat_name,
                        'signal_date': sig_date,
                        'signal_available_at': f"{sig_date} 23:59:59",
                        'entry_date': entry_date,
                        'exit_date': exit_date,
                        'fold_id': fid,
                        'train_start_date': tr_start,
                        'train_end_date': tr_end,
                        'test_start_date': te_start,
                        'test_end_date': te_end,
                        'symbol_leg_a': sym_a,
                        'expiry_date_leg_a': cand['expiry_date_leg_a'],
                        'contract_key_leg_a': key_a,
                        'lots_leg_a': lots_a,
                        'symbol_leg_b': sym_b,
                        'expiry_date_leg_b': cand['expiry_date_leg_b'],
                        'contract_key_leg_b': key_b,
                        'lots_leg_b': lots_b,
                        'matched_exposure_grams': matched_grams,
                        'signal_metric_name': cand.get('signal_metric', 'spread'),
                        'signal_value': sig_metric_val,
                        'threshold_applied': threshold_val,
                        'signal_direction': signal_direction,
                        'entry_price_leg_a': p_entry_a,
                        'entry_price_leg_b': p_entry_b,
                        'exit_price_leg_a': p_exit_a,
                        'exit_price_leg_b': p_exit_b,
                        'execution_status_leg_a': 'FILLED',
                        'execution_status_leg_b': 'FILLED',
                        'overall_execution_status': 'FILLED',
                        'rejection_or_exclusion_reason': 'NONE',
                        'exit_trigger_reason': exit_reason,
                        'holding_period_days': holding_days,
                        'gross_pnl_inr': gross_pnl_inr,
                        'gross_pnl_per_gram': gross_pnl_per_g,
                        'entry_cost_inr': tot_entry_cost,
                        'exit_cost_inr': tot_exit_cost,
                        'total_modeled_cost_inr': total_modeled_cost,
                        'total_modeled_cost_per_gram': cost_per_g,
                        'net_pnl_inr': net_pnl_inr,
                        'net_pnl_per_gram': net_pnl_per_g,
                        'notional_exposure_inr': notional_entry,
                        'cost_scenario': sc_name,
                        'cost_model_completeness': 'COMPLETE',
                        'trade_completion_status': 'COMPLETED'
                    })
            else:
                # Unresolved Trade (Audit 4)
                diagnostics_counts['trades_unresolved'] += 1
                for sc_name in ["base", "low", "high"]:
                    trade_id = f"TRADE_{fid}_{cid}_{sc_name}"
                    all_trade_records.append({
                        'trade_id': trade_id,
                        'candidate_id': cid,
                        'candidate_type': ctype,
                        'strategy_name': strat_name,
                        'signal_date': sig_date,
                        'signal_available_at': f"{sig_date} 23:59:59",
                        'entry_date': entry_date,
                        'exit_date': exit_date,
                        'fold_id': fid,
                        'train_start_date': tr_start,
                        'train_end_date': tr_end,
                        'test_start_date': te_start,
                        'test_end_date': te_end,
                        'symbol_leg_a': sym_a,
                        'expiry_date_leg_a': cand['expiry_date_leg_a'],
                        'contract_key_leg_a': key_a,
                        'lots_leg_a': lots_a,
                        'symbol_leg_b': sym_b,
                        'expiry_date_leg_b': cand['expiry_date_leg_b'],
                        'contract_key_leg_b': key_b,
                        'lots_leg_b': lots_b,
                        'matched_exposure_grams': matched_grams,
                        'signal_metric_name': cand.get('signal_metric', 'spread'),
                        'signal_value': sig_metric_val,
                        'threshold_applied': threshold_val,
                        'signal_direction': signal_direction,
                        'entry_price_leg_a': p_entry_a,
                        'entry_price_leg_b': p_entry_b,
                        'exit_price_leg_a': np.nan,
                        'exit_price_leg_b': np.nan,
                        'execution_status_leg_a': 'FILLED',
                        'execution_status_leg_b': 'FILLED',
                        'overall_execution_status': 'FILLED',
                        'rejection_or_exclusion_reason': 'NONE',
                        'exit_trigger_reason': exit_reason,
                        'holding_period_days': holding_days,
                        'gross_pnl_inr': np.nan,
                        'gross_pnl_per_gram': np.nan,
                        'entry_cost_inr': np.nan,
                        'exit_cost_inr': np.nan,
                        'total_modeled_cost_inr': np.nan,
                        'total_modeled_cost_per_gram': np.nan,
                        'net_pnl_inr': np.nan,
                        'net_pnl_per_gram': np.nan,
                        'notional_exposure_inr': notional_entry,
                        'cost_scenario': sc_name,
                        'cost_model_completeness': 'INCOMPLETE_UNRESOLVED_EXIT',
                        'trade_completion_status': 'UNRESOLVED'
                    })

    # Construct Output A: mcx_gold_backtest_trades.csv
    trades_df = pd.DataFrame(all_trade_records)
    print(f"\nTotal Simulated Trade Records Generated: {len(trades_df):,}")

    # Construct Output B: mcx_gold_walk_forward_metrics.csv
    fold_metrics = []
    for (fid, sname, sc), grp in trades_df.groupby(['fold_id', 'strategy_name', 'cost_scenario']):
        comp = grp[grp['trade_completion_status'] == 'COMPLETED']
        n_comp = len(comp)
        wins = comp[comp['net_pnl_inr'] > 0]
        losses = comp[comp['net_pnl_inr'] <= 0]
        n_wins = len(wins)
        n_losses = len(losses)
        win_rate = (n_wins / n_comp * 100.0) if n_comp > 0 else 0.0

        gross_pnl = comp['gross_pnl_inr'].sum() if n_comp > 0 else 0.0
        tot_costs = comp['total_modeled_cost_inr'].sum() if n_comp > 0 else 0.0
        net_pnl = comp['net_pnl_inr'].sum() if n_comp > 0 else 0.0

        mean_pnl = comp['net_pnl_inr'].mean() if n_comp > 0 else 0.0
        median_pnl = comp['net_pnl_inr'].median() if n_comp > 0 else 0.0
        mean_pnl_g = comp['net_pnl_per_gram'].mean() if n_comp > 0 else 0.0

        tot_win_inr = wins['net_pnl_inr'].sum() if len(wins) > 0 else 0.0
        tot_loss_inr = abs(losses['net_pnl_inr'].sum()) if len(losses) > 0 else 0.0
        profit_factor = (tot_win_inr / tot_loss_inr) if tot_loss_inr > 0 else np.nan

        # Realized P&L drawdown (Audit 3)
        if n_comp > 1:
            cum_pnl = comp.sort_values('exit_date')['net_pnl_inr'].cumsum()
            running_max = cum_pnl.cummax()
            dd = running_max - cum_pnl
            max_dd = dd.max()
        else:
            max_dd = 0.0

        fold_metrics.append({
            'fold_id': fid,
            'strategy_name': sname,
            'cost_scenario': sc,
            'train_start_date': grp['train_start_date'].iloc[0],
            'train_end_date': grp['train_end_date'].iloc[0],
            'test_start_date': grp['test_start_date'].iloc[0],
            'test_end_date': grp['test_end_date'].iloc[0],
            'trade_attempts': len(grp),
            'completed_trades': n_comp,
            'rejected_trades': len(grp[grp['trade_completion_status'] == 'REJECTED']),
            'unresolved_trades': len(grp[grp['trade_completion_status'] == 'UNRESOLVED']),
            'winning_trades': n_wins,
            'losing_trades': n_losses,
            'win_rate_pct': win_rate,
            'gross_pnl_inr': gross_pnl,
            'total_costs_inr': tot_costs,
            'net_pnl_inr': net_pnl,
            'mean_net_pnl_per_trade_inr': mean_pnl,
            'median_net_pnl_per_trade_inr': median_pnl,
            'mean_net_pnl_per_gram': mean_pnl_g,
            'profit_factor': profit_factor,
            'realized_max_drawdown_inr': max_dd,
            'mean_holding_days': comp['holding_period_days'].mean() if n_comp > 0 else 0.0
        })

    metrics_df = pd.DataFrame(fold_metrics)

    # Construct Output C: mcx_gold_backtest_summary.csv
    summary_records = []
    for (sname, sc), grp in trades_df.groupby(['strategy_name', 'cost_scenario']):
        comp = grp[grp['trade_completion_status'] == 'COMPLETED']
        n_comp = len(comp)
        wins = comp[comp['net_pnl_inr'] > 0]
        losses = comp[comp['net_pnl_inr'] <= 0]
        n_wins = len(wins)
        n_losses = len(losses)
        win_rate = (n_wins / n_comp * 100.0) if n_comp > 0 else 0.0

        gross_pnl = comp['gross_pnl_inr'].sum() if n_comp > 0 else 0.0
        tot_costs = comp['total_modeled_cost_inr'].sum() if n_comp > 0 else 0.0
        net_pnl = comp['net_pnl_inr'].sum() if n_comp > 0 else 0.0

        mean_pnl = comp['net_pnl_inr'].mean() if n_comp > 0 else 0.0
        median_pnl = comp['net_pnl_inr'].median() if n_comp > 0 else 0.0
        mean_pnl_g = comp['net_pnl_per_gram'].mean() if n_comp > 0 else 0.0

        tot_win_inr = wins['net_pnl_inr'].sum() if len(wins) > 0 else 0.0
        tot_loss_inr = abs(losses['net_pnl_inr'].sum()) if len(losses) > 0 else 0.0
        profit_factor = (tot_win_inr / tot_loss_inr) if tot_loss_inr > 0 else np.nan

        if n_comp > 1:
            cum_pnl = comp.sort_values('exit_date')['net_pnl_inr'].cumsum()
            running_max = cum_pnl.cummax()
            dd = running_max - cum_pnl
            max_dd = dd.max()
        else:
            max_dd = 0.0

        summary_records.append({
            'strategy_name': sname,
            'cost_scenario': sc,
            'total_trade_attempts': len(grp),
            'completed_trades': n_comp,
            'rejected_trades': len(grp[grp['trade_completion_status'] == 'REJECTED']),
            'unresolved_trades': len(grp[grp['trade_completion_status'] == 'UNRESOLVED']),
            'completion_rate_pct': (n_comp / len(grp) * 100.0) if len(grp) > 0 else 0.0,
            'winning_trades': n_wins,
            'losing_trades': n_losses,
            'win_rate_pct': win_rate,
            'gross_pnl_inr': gross_pnl,
            'total_costs_inr': tot_costs,
            'net_pnl_inr': net_pnl,
            'mean_net_pnl_per_trade_inr': mean_pnl,
            'median_net_pnl_per_trade_inr': median_pnl,
            'mean_net_pnl_per_gram': mean_pnl_g,
            'profit_factor': profit_factor,
            'realized_max_drawdown_inr': max_dd,
            'mean_holding_days': comp['holding_period_days'].mean() if n_comp > 0 else 0.0,
            'drawdown_construction_note': 'Realized-P&L cumulative curve booked at trade exit date. Daily MTM unrealized variations unmodeled.',
            'capital_roi_note': 'ROI/Sharpe ratio uncalculated: initial margin and capital employed unobserved in bhavcopy'
        })

    summary_df = pd.DataFrame(summary_records)

    # Construct Output D: mcx_gold_execution_diagnostics.csv
    diag_rows = [
        {'diagnostic_category': 'Eligibility & Screening', 'metric_name': 'total_candidates_screened', 'count': diagnostics_counts['total_candidates_screened'], 'description': 'Total candidates evaluated in backtest'},
        {'diagnostic_category': 'Eligibility & Screening', 'metric_name': 'candidates_in_test_windows', 'count': diagnostics_counts['candidates_in_test_windows'], 'description': 'Candidates occurring within test window boundaries'},
        {'diagnostic_category': 'Signal Triggers', 'metric_name': 'signals_triggered', 'count': diagnostics_counts['signals_triggered'], 'description': 'Candidate observations exceeding training threshold'},
        {'diagnostic_category': 'Execution Feasibility', 'metric_name': 'trades_filled', 'count': diagnostics_counts['trades_filled'], 'description': 'Trade attempts successfully filled at date t+1 Open on both legs'},
        {'diagnostic_category': 'Execution Feasibility', 'metric_name': 'trades_completed', 'count': diagnostics_counts['trades_completed'], 'description': 'Trades held and exited cleanly at Open within evaluation rules'},
        {'diagnostic_category': 'Execution Feasibility', 'metric_name': 'trades_unresolved', 'count': diagnostics_counts['trades_unresolved'], 'description': 'Trades marked unresolved due to unexecutable boundary exits'},
        {'diagnostic_category': 'Execution Rejections', 'metric_name': 'rejected_existing_contract_position', 'count': diagnostics_counts['rejected_existing_contract_position'], 'description': 'Rejections because a leg contract is already in an active portfolio position'},
        {'diagnostic_category': 'Execution Rejections', 'metric_name': 'rejected_multi_strategy_contract_conflict', 'count': diagnostics_counts['rejected_multi_strategy_contract_conflict'], 'description': 'Rejections due to multi-strategy concurrent contract conflict'},
        {'diagnostic_category': 'Execution Rejections', 'metric_name': 'rejected_opposing_contract_position', 'count': diagnostics_counts['rejected_opposing_contract_position'], 'description': 'Rejections due to opposing simultaneous contract positions'},
        {'diagnostic_category': 'Execution Rejections', 'metric_name': 'rejected_gross_exposure_limit', 'count': diagnostics_counts['rejected_gross_exposure_limit'], 'description': 'Rejections due to contract gross lot exposure limit breached'},
        {'diagnostic_category': 'Execution Rejections', 'metric_name': 'rejected_net_exposure_limit', 'count': diagnostics_counts['rejected_net_exposure_limit'], 'description': 'Rejections due to contract net lot exposure limit breached'},
        {'diagnostic_category': 'Execution Rejections', 'metric_name': 'rejected_contract_gram_limit', 'count': diagnostics_counts['rejected_contract_gram_limit'], 'description': 'Rejections due to contract underlying gram exposure limit breached'},
        {'diagnostic_category': 'Execution Rejections', 'metric_name': 'rejected_existing_active_position', 'count': diagnostics_counts['rejected_existing_active_position'], 'description': 'Legacy pair-level active position rejection counter'},
        {'diagnostic_category': 'Execution Rejections', 'metric_name': 'rejected_insufficient_training_history', 'count': diagnostics_counts['rejected_insufficient_training_history'], 'description': 'Rejections because product/pair has < 20 training samples in fold training window'},
        {'diagnostic_category': 'Execution Rejections', 'metric_name': 'rejected_missing_next_session', 'count': diagnostics_counts['rejected_missing_next_session'], 'description': 'Rejections due to missing next-session market record'},
        {'diagnostic_category': 'Execution Rejections', 'metric_name': 'rejected_missing_next_open_leg_a', 'count': diagnostics_counts['rejected_missing_next_open_leg_a'], 'description': 'Rejections due to missing next-session Open price on Leg A'},
        {'diagnostic_category': 'Execution Rejections', 'metric_name': 'rejected_missing_next_open_leg_b', 'count': diagnostics_counts['rejected_missing_next_open_leg_b'], 'description': 'Rejections due to missing next-session Open price on Leg B'},
        {'diagnostic_category': 'Execution Rejections', 'metric_name': 'rejected_zero_volume_next_session_leg_a', 'count': diagnostics_counts['rejected_zero_volume_next_session_leg_a'], 'description': 'Rejections due to zero traded volume on Leg A next session'},
        {'diagnostic_category': 'Execution Rejections', 'metric_name': 'rejected_zero_volume_next_session_leg_b', 'count': diagnostics_counts['rejected_zero_volume_next_session_leg_b'], 'description': 'Rejections due to zero traded volume on Leg B next session'},
        {'diagnostic_category': 'Execution Rejections', 'metric_name': 'rejected_tender_window_at_entry', 'count': diagnostics_counts['rejected_tender_window_at_entry'], 'description': 'Rejections because contract already within 5-day tender window'},
        {'diagnostic_category': 'Execution Rejections', 'metric_name': 'rejected_fold_boundary_censored', 'count': diagnostics_counts['rejected_fold_boundary_censored'], 'description': 'Rejections because planned entry falls on or after test window end'},
        {'diagnostic_category': 'Exit Mechanics', 'metric_name': 'exits_due_to_max_holding', 'count': diagnostics_counts['exits_due_to_max_holding'], 'description': 'Exits triggered by reaching maximum 10-day holding period'},
        {'diagnostic_category': 'Exit Mechanics', 'metric_name': 'exits_due_to_tender_safety', 'count': diagnostics_counts['exits_due_to_tender_safety'], 'description': 'Exits triggered to avoid delivery tender notice period (DTE <= 5)'},
        {'diagnostic_category': 'Exit Mechanics', 'metric_name': 'exits_due_to_fold_boundary', 'count': diagnostics_counts['exits_due_to_fold_boundary'], 'description': 'Exits triggered by test window fold boundary termination'}
    ]
    diag_df = pd.DataFrame(diag_rows)

    return trades_df, metrics_df, summary_df, diag_df

def save_outputs(trades_df: pd.DataFrame, metrics_df: pd.DataFrame, summary_df: pd.DataFrame, diag_df: pd.DataFrame, data_dir: str = DATA_DIR):
    """Save all four Phase 6 production datasets."""
    p_a = os.path.join(data_dir, "mcx_gold_backtest_trades.csv")
    p_b = os.path.join(data_dir, "mcx_gold_walk_forward_metrics.csv")
    p_c = os.path.join(data_dir, "mcx_gold_backtest_summary.csv")
    p_d = os.path.join(data_dir, "mcx_gold_execution_diagnostics.csv")

    trades_df.to_csv(p_a, index=False)
    metrics_df.to_csv(p_b, index=False)
    summary_df.to_csv(p_c, index=False)
    diag_df.to_csv(p_d, index=False)

    print(f"\n--- Phase 6 Outputs Successfully Saved ---")
    print(f"Output A (Trades Ledger):       {p_a} ({len(trades_df):,} rows)")
    print(f"Output B (Walk-Forward Metrics): {p_b} ({len(metrics_df):,} rows)")
    print(f"Output C (Strategy Summary):     {p_c} ({len(summary_df):,} rows)")
    print(f"Output D (Diagnostics):          {p_d} ({len(diag_df):,} rows)")

if __name__ == '__main__':
    t_df, m_df, s_df, d_df = run_backtest_simulation()
    save_outputs(t_df, m_df, s_df, d_df)
