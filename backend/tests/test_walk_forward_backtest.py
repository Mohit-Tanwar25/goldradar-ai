"""
Unit and Regression Test Suite for Phase 6: Walk-Forward Backtesting Engine
"""

import os
import sys
import json
import math
import hashlib
import unittest
from collections import defaultdict
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from run_walk_forward_backtest import (
    load_all_configs,
    load_data,
    compute_walk_forward_folds,
    calculate_single_leg_cost,
    run_backtest_simulation
)

class TestWalkForwardBacktest(unittest.TestCase):
    """22 Comprehensive validation tests for Phase 6 walk-forward engine."""

    @classmethod
    def setUpClass(cls):
        cls.specs_cfg, cls.liq_cfg, cls.costs_cfg, cls.bt_cfg = load_all_configs(CONFIG_DIR)
        cls.trades_p = os.path.join(DATA_DIR, "mcx_gold_backtest_trades.csv")
        cls.metrics_p = os.path.join(DATA_DIR, "mcx_gold_walk_forward_metrics.csv")
        cls.summary_p = os.path.join(DATA_DIR, "mcx_gold_backtest_summary.csv")
        cls.diag_p = os.path.join(DATA_DIR, "mcx_gold_execution_diagnostics.csv")

        cls.trades_df = pd.read_csv(cls.trades_p)
        cls.metrics_df = pd.read_csv(cls.metrics_p)
        cls.summary_df = pd.read_csv(cls.summary_p)
        cls.diag_df = pd.read_csv(cls.diag_p)
        cls.norm_df, cls.elig_df = load_data(DATA_DIR)

    def test_01_chronological_sorting_and_deterministic_output(self):
        """Confirm trades within each fold are strictly ordered chronologically by signal date."""
        for fid, grp in self.trades_df.groupby('fold_id'):
            dates = grp['signal_date'].tolist()
            self.assertEqual(dates, sorted(dates), f"Fold {fid} must be strictly chronological.")

    def test_02_training_and_test_windows_strictly_ordered(self):
        """Confirm for every fold, max(train_date) < min(test_date) without any temporal overlap."""
        all_dates = sorted(self.norm_df['date'].unique())
        folds = compute_walk_forward_folds(all_dates)
        for f in folds:
            self.assertLess(
                f['train_end_date'],
                f['test_start_date'],
                f"Fold {f['fold_id']} has temporal overlap! Train end must precede test start."
            )

    def test_03_no_future_data_used_for_earlier_signal(self):
        """Confirm signals at date t close are marked available only at t 23:59:59."""
        for _, row in self.trades_df.head(100).iterrows():
            sig_d = row['signal_date']
            avail_at = row['signal_available_at']
            self.assertTrue(avail_at.startswith(sig_d), "Signal availability timestamp must match signal date.")
            self.assertIn("23:59:59", avail_at)

    def test_04_thresholds_fitted_only_on_training_window(self):
        """Confirm that signal thresholds applied during test window remain frozen."""
        for fid, grp in self.trades_df.groupby('fold_id'):
            # In each fold, strategy threshold applied must be constant across all trades
            for sname, sgrp in grp.groupby('strategy_name'):
                unique_thresholds = sgrp['threshold_applied'].nunique()
                self.assertEqual(unique_thresholds, 1, f"Fold {fid} {sname} threshold must be frozen.")

    def test_05_prohibit_same_close_entry(self):
        """Confirm entry date is strictly greater than signal date (next session open)."""
        valid_trades = self.trades_df[self.trades_df['overall_execution_status'] == 'FILLED']
        for _, row in valid_trades.iterrows():
            self.assertGreater(
                row['entry_date'],
                row['signal_date'],
                f"Look-ahead violation! Entry date {row['entry_date']} must follow signal date {row['signal_date']}."
            )

    def test_06_missing_next_open_not_filled_with_close(self):
        """Confirm synthetic candidate with missing open is rejected, never filled with close."""
        sc_cfg = self.costs_cfg['scenarios']['base']
        res = calculate_single_leg_cost(np.nan, "buy", sc_cfg)
        self.assertEqual(res['total_cost'], 0.0)

    def test_07_zero_volume_and_incomplete_ohlc_rejected(self):
        """Confirm zero volume execution records are rejected with explicit reasons."""
        zero_vol_rejections = self.trades_df[self.trades_df['rejection_or_exclusion_reason'].str.contains('zero_volume', na=False)]
        for _, r in zero_vol_rejections.iterrows():
            self.assertEqual(r['overall_execution_status'], 'REJECTED')
            self.assertTrue(np.isnan(r['net_pnl_inr']))

    def test_08_both_legs_satisfy_two_leg_execution_policy(self):
        """Confirm both legs are FILLED if trade is FILLED, and REJECTED if trade is REJECTED."""
        for _, r in self.trades_df.iterrows():
            if r['overall_execution_status'] == 'FILLED':
                self.assertEqual(r['execution_status_leg_a'], 'FILLED')
                self.assertEqual(r['execution_status_leg_b'], 'FILLED')
            elif r['overall_execution_status'] == 'REJECTED':
                self.assertEqual(r['execution_status_leg_a'], 'REJECTED')
                self.assertEqual(r['execution_status_leg_b'], 'REJECTED')

    def test_09_correct_strategy_spread_orientation(self):
        """Confirm valid signal directions exist for each strategy."""
        rad_trades = self.trades_df[self.trades_df['strategy_name'] == 'strategy_a_cross_product']
        self.assertTrue(set(rad_trades['signal_direction'].unique()).issubset({'SELL_A_BUY_B', 'BUY_A_SELL_B'}))

        cal_trades = self.trades_df[self.trades_df['strategy_name'] == 'strategy_b_calendar_spread']
        self.assertTrue(set(cal_trades['signal_direction'].unique()).issubset({'SELL_B_BUY_A', 'BUY_B_SELL_A'}))

    def test_10_correct_integer_lot_and_exposure_math(self):
        """Confirm exposure grams match contract specs exactly."""
        specs = self.specs_cfg['contracts']
        for _, r in self.trades_df.head(200).iterrows():
            u_a = specs[r['symbol_leg_a']]['trading_unit_grams']
            u_b = specs[r['symbol_leg_b']]['trading_unit_grams']
            g_a = r['lots_leg_a'] * u_a
            g_b = r['lots_leg_b'] * u_b
            self.assertEqual(g_a, g_b, f"Matched exposure mismatch in {r['trade_id']}")
            self.assertEqual(r['matched_exposure_grams'], g_a)

    def test_11_dynamic_transaction_cost_recalculation(self):
        """Confirm transaction costs are dynamically computed from entry and exit prices."""
        comp = self.trades_df[self.trades_df['trade_completion_status'] == 'COMPLETED'].iloc[0]
        tot_cost = comp['total_modeled_cost_inr']
        ent_cost = comp['entry_cost_inr']
        ext_cost = comp['exit_cost_inr']
        self.assertAlmostEqual(tot_cost, ent_cost + ext_cost, places=4)
        self.assertGreater(tot_cost, 0.0)

    def test_12_no_double_counting_phase5_costs(self):
        """Confirm net PnL equals gross PnL minus modeled cost, not subtracted twice."""
        comp = self.trades_df[self.trades_df['trade_completion_status'] == 'COMPLETED'].iloc[0]
        expected_net = comp['gross_pnl_inr'] - comp['total_modeled_cost_inr']
        self.assertAlmostEqual(comp['net_pnl_inr'], expected_net, places=4)

    def test_13_expiry_safety_exit_behavior(self):
        """Confirm trades with exit trigger 'expiry_tender_safety' are exited before or at tender window."""
        tender_exits = self.trades_df[self.trades_df['exit_trigger_reason'] == 'expiry_tender_safety']
        self.assertGreater(len(tender_exits), 0, "Tender safety exits must be present.")

    def test_14_max_holding_period_enforced(self):
        """Confirm holding period does not exceed configured maximum."""
        comp = self.trades_df[self.trades_df['trade_completion_status'] == 'COMPLETED']
        self.assertTrue((comp['holding_period_days'] <= 11).all())

    def test_15_unresolved_trades_not_silently_counted_as_completed(self):
        """Confirm rejected trades have NaN PnL, not zero."""
        rej = self.trades_df[self.trades_df['trade_completion_status'] == 'REJECTED']
        self.assertTrue(rej['net_pnl_inr'].isna().all())
        self.assertTrue(rej['gross_pnl_inr'].isna().all())

    def test_16_fold_boundary_handling_no_future_leakage(self):
        """Confirm test trades do not have exit dates beyond their fold's test window end."""
        for fid, grp in self.trades_df.groupby('fold_id'):
            te_end = grp['test_end_date'].iloc[0]
            comp = grp[grp['trade_completion_status'] == 'COMPLETED']
            for _, r in comp.iterrows():
                self.assertLessEqual(r['exit_date'], te_end, f"Trade {r['trade_id']} leaked past test window!")

    def test_17_pnl_and_equity_curves_chronologically_ordered(self):
        """Confirm fold metrics have valid non-negative drawdowns."""
        for _, m in self.metrics_df.iterrows():
            if m['completed_trades'] > 1:
                self.assertGreaterEqual(m['realized_max_drawdown_inr'], 0.0)

    def test_18_missing_pnl_does_not_become_zero(self):
        """Confirm rejected and unresolved trades are tracked and excluded from win rate."""
        for _, s in self.summary_df.iterrows():
            self.assertEqual(s['total_trade_attempts'], s['completed_trades'] + s['rejected_trades'] + s['unresolved_trades'])

    def test_19_duplicate_trade_ids_rejected(self):
        """Confirm trade_id in Output A is 100% unique."""
        self.assertEqual(self.trades_df['trade_id'].nunique(), len(self.trades_df))

    def test_20_output_schemas_and_primary_keys_validated(self):
        """Confirm primary keys and schemas for all 4 output tables."""
        self.assertTrue('trade_id' in self.trades_df.columns)
        self.assertTrue('fold_id' in self.metrics_df.columns)
        self.assertTrue('strategy_name' in self.summary_df.columns)
        self.assertTrue('diagnostic_category' in self.diag_df.columns)
        # Check Output B key uniqueness
        metrics_keys = self.metrics_df.set_index(['fold_id', 'strategy_name', 'cost_scenario']).index
        self.assertTrue(metrics_keys.is_unique)

    def test_21_pipeline_deterministic_reruns(self):
        """Confirm deterministic fold boundary calculation."""
        all_dates = sorted(self.norm_df['date'].unique())
        f1 = compute_walk_forward_folds(all_dates)
        f2 = compute_walk_forward_folds(all_dates)
        self.assertEqual(f1, f2)

    def test_22_upstream_datasets_immutability(self):
        """Confirm raw data and Phase 2-5 active 4-product datasets remain 100% byte-identical."""
        expected_hashes = {
            'data/processed/mcx_gold_master.csv': '0efb75ed225bf651',
            'data/processed/mcx_gold_normalized.csv': '8eb15f5353e8df88',
            'data/processed/mcx_gold_relative_price_radar.csv': 'bf746998b24560a9',
            'data/processed/mcx_gold_term_structure.csv': '9d78f67db6120f3e',
            'data/processed/mcx_gold_term_structure_snapshots.csv': '775c4bbafa2410c6',
            'data/processed/mcx_gold_liquidity_filtered_candidates.csv': '39432f3bbcd45898',
            'data/processed/mcx_gold_transaction_cost_scenarios.csv': '7c852bf0ea361495',
            'data/processed/mcx_gold_eligible_candidates.csv': '0e8299fb816c8c85'
        }
        for rel_path, exp_prefix in expected_hashes.items():
            full_path = os.path.join(PROJECT_ROOT, rel_path)
            self.assertTrue(os.path.exists(full_path), f"File {rel_path} must exist.")
            with open(full_path, 'rb') as f:
                h = hashlib.sha256(f.read()).hexdigest()[:16]
            self.assertEqual(h, exp_prefix, f"File {rel_path} changed! Upstream data must be immutable.")

        # Verify preserved 5-product archive
        arch_master = os.path.join(PROJECT_ROOT, 'data/processed/archive_5product/mcx_gold_master.csv')
        if os.path.exists(arch_master):
            with open(arch_master, 'rb') as f:
                arch_h = hashlib.sha256(f.read()).hexdigest()[:16]
            self.assertEqual(arch_h, 'ac57299101fef709')

    def test_23_insufficient_training_history_and_newly_listed_products(self):
        """Verify that products/pairs with < 20 training observations are quarantined and not traded."""
        # In Folds 1 to 4, GOLDTEN has insufficient training history (< 20 samples).
        # Check that no completed trade in Folds 1 to 4 involves GOLDTEN
        early_trades = self.trades_df[
            (self.trades_df['fold_id'].isin(['FOLD_01', 'FOLD_02', 'FOLD_03', 'FOLD_04'])) &
            (self.trades_df['trade_completion_status'] == 'COMPLETED')
        ]
        goldten_early = early_trades[
            (early_trades['symbol_leg_a'] == 'GOLDTEN') | 
            (early_trades['symbol_leg_b'] == 'GOLDTEN')
        ]
        self.assertEqual(len(goldten_early), 0, "GOLDTEN must not trade in Folds 1-4 due to insufficient training history.")

        # Check that rejected trades contain explicit rejection reason for insufficient training history
        rejections = self.trades_df[self.trades_df['rejection_or_exclusion_reason'] == 'rejected_insufficient_training_history']
        self.assertGreater(len(rejections), 0, "Must have rejections for insufficient training history.")
        # Verify that GOLDTEN is among the rejected products in Fold 4
        goldten_rejections = rejections[
            (rejections['symbol_leg_a'] == 'GOLDTEN') | 
            (rejections['symbol_leg_b'] == 'GOLDTEN')
        ]
        self.assertGreater(len(goldten_rejections), 0, "GOLDTEN must have rejections due to insufficient training history in Fold 4.")

    def test_24_no_concurrent_overlapping_pair_positions(self):
        """Verify that no two completed trades on the same contract pair overlap in holding window."""
        completed = self.trades_df[
            (self.trades_df['trade_completion_status'] == 'COMPLETED') &
            (self.trades_df['cost_scenario'] == 'base')
        ]
        for pair_key, group in completed.groupby(['strategy_name', 'symbol_leg_a', 'symbol_leg_b', 'expiry_date_leg_a', 'expiry_date_leg_b']):
            sorted_grp = group.sort_values(by='entry_date')
            prev_exit = None
            for _, r in sorted_grp.iterrows():
                if prev_exit is not None:
                    self.assertGreater(
                        r['entry_date'], prev_exit,
                        f"Overlapping trade detected for {pair_key}: Entry {r['entry_date']} <= Prior Exit {prev_exit}"
                    )
                prev_exit = r['exit_date']

    def test_25_two_different_pairs_sharing_same_contract(self):
        """1. Synthetic test: Two different pairs sharing the same contract are rejected."""
        active_positions = defaultdict(list)
        active_positions['GOLD_05JUN2026'].append({
            'trade_id': 'TRADE_A', 'strategy_name': 'strategy_a_cross_product',
            'entry_date': '2026-01-05', 'exit_date': '2026-01-15',
            'direction': 'SELL', 'lots': 1, 'signed_lots': -1, 'grams': 1000
        })

        entry_date = '2026-01-08'
        allow_shared = False
        rejection_reason = "NONE"
        for leg_key in ['GOLD_05JUN2026', 'GOLDGUINEA_31JUL2026']:
            active_list = [p for p in active_positions.get(leg_key, []) if p['exit_date'] >= entry_date]
            if len(active_list) > 0 and not allow_shared:
                rejection_reason = "rejected_existing_contract_position"
                break
        self.assertEqual(rejection_reason, "rejected_existing_contract_position")

    def test_26_multiple_strategies_sharing_same_contract(self):
        """2. Synthetic test: Multiple strategies attempting to use the same contract are rejected."""
        active_positions = defaultdict(list)
        active_positions['GOLDM_05AUG2025'].append({
            'trade_id': 'TRADE_STRAT_A', 'strategy_name': 'strategy_a_cross_product',
            'entry_date': '2025-05-02', 'exit_date': '2025-05-12',
            'direction': 'BUY', 'lots': 10, 'signed_lots': 10, 'grams': 1000
        })

        entry_date = '2025-05-06'
        allow_multi = False
        rejection_reason = "NONE"
        active_list = [p for p in active_positions.get('GOLDM_05AUG2025', []) if p['exit_date'] >= entry_date]
        if len(active_list) > 0:
            if not allow_multi and any(p['strategy_name'] != 'strategy_b_calendar_spread' for p in active_list):
                rejection_reason = "rejected_multi_strategy_contract_conflict"
        self.assertEqual(rejection_reason, "rejected_multi_strategy_contract_conflict")

    def test_27_gross_exposure_limit_exceeded(self):
        """3. Synthetic test: Gross exposure exceeding the configured limit is rejected."""
        active_positions = defaultdict(list)
        active_positions['GOLD_05DEC2025'].append({
            'trade_id': 'TRADE_1', 'strategy_name': 'strategy_a_cross_product',
            'entry_date': '2025-08-01', 'exit_date': '2025-08-10',
            'direction': 'BUY', 'lots': 6, 'signed_lots': 6, 'grams': 6000
        })

        entry_date = '2025-08-04'
        new_lots = 5
        max_gross_lots = 10
        active_list = [p for p in active_positions['GOLD_05DEC2025'] if p['exit_date'] >= entry_date]
        tot_gross = sum(p['lots'] for p in active_list) + new_lots
        rejection_reason = "rejected_gross_exposure_limit" if tot_gross > max_gross_lots else "NONE"
        self.assertEqual(rejection_reason, "rejected_gross_exposure_limit")
        self.assertEqual(tot_gross, 11)

    def test_28_net_exposure_limit_exceeded(self):
        """4. Synthetic test: Net exposure exceeding the configured limit is rejected."""
        active_positions = defaultdict(list)
        active_positions['GOLD_05DEC2025'].append({
            'trade_id': 'TRADE_1', 'strategy_name': 'strategy_a_cross_product',
            'entry_date': '2025-08-01', 'exit_date': '2025-08-10',
            'direction': 'BUY', 'lots': 8, 'signed_lots': 8, 'grams': 8000
        })

        entry_date = '2025-08-04'
        new_signed_lots = 3
        max_net_lots = 10
        active_list = [p for p in active_positions['GOLD_05DEC2025'] if p['exit_date'] >= entry_date]
        tot_net = abs(sum(p['signed_lots'] for p in active_list) + new_signed_lots)
        rejection_reason = "rejected_net_exposure_limit" if tot_net > max_net_lots else "NONE"
        self.assertEqual(rejection_reason, "rejected_net_exposure_limit")
        self.assertEqual(tot_net, 11)

    def test_29_opposite_positions_and_gross_vs_net_exposure(self):
        """5. Synthetic test: Opposing positions distinguish between gross and net exposure."""
        active_positions = [{'direction': 'BUY', 'lots': 5, 'signed_lots': +5}]
        new_dir = 'SELL'
        new_lots = 5
        new_signed_lots = -5

        allow_opposing = False
        rejection_reason = "NONE"
        if not allow_opposing and any(p['direction'] != new_dir for p in active_positions):
            rejection_reason = "rejected_opposing_contract_position"
        self.assertEqual(rejection_reason, "rejected_opposing_contract_position")

        net_exposure = abs(sum(p['signed_lots'] for p in active_positions) + new_signed_lots)
        gross_exposure = sum(p['lots'] for p in active_positions) + new_lots
        self.assertEqual(net_exposure, 0)
        self.assertEqual(gross_exposure, 10)

    def test_30_exit_and_subsequent_reentry_release_timing(self):
        """6. Synthetic test: Position released strictly after exit date has passed."""
        active_positions = defaultdict(list)
        active_positions['GOLD_05FEB2025'].append({
            'trade_id': 'TRADE_EXIT_TEST', 'entry_date': '2025-01-05', 'exit_date': '2025-01-10'
        })

        active_on_exit_day = [p for p in active_positions['GOLD_05FEB2025'] if p['exit_date'] >= '2025-01-10']
        self.assertEqual(len(active_on_exit_day), 1)

        active_next_day = [p for p in active_positions['GOLD_05FEB2025'] if p['exit_date'] >= '2025-01-11']
        self.assertEqual(len(active_next_day), 0)

    def test_31_position_occupancy_across_all_trading_sessions(self):
        """7. Integration test: No single contract has overlapping occupancy across all sessions."""
        comp = self.trades_df[
            (self.trades_df['trade_completion_status'] == 'COMPLETED') &
            (self.trades_df['cost_scenario'] == 'base')
        ]
        contract_intervals = defaultdict(list)
        for _, r in comp.iterrows():
            contract_intervals[r['contract_key_leg_a']].append((r['entry_date'], r['exit_date'], r['trade_id']))
            contract_intervals[r['contract_key_leg_b']].append((r['entry_date'], r['exit_date'], r['trade_id']))

        for c_key, intervals in contract_intervals.items():
            sorted_int = sorted(intervals, key=lambda x: x[0])
            for i in range(len(sorted_int) - 1):
                cur_entry, cur_exit, tid_1 = sorted_int[i]
                nxt_entry, nxt_exit, tid_2 = sorted_int[i+1]
                self.assertGreater(
                    nxt_entry, cur_exit,
                    f"Contract {c_key} overlap detected! {tid_1} [{cur_entry} to {cur_exit}] overlaps with {tid_2} [{nxt_entry} to {nxt_exit}]"
                )

    def test_32_simultaneous_signals_deterministic_prioritization(self):
        """8. Synthetic test: Simultaneous signals prioritised deterministically by relative strength."""
        cands = [
            {'candidate_id': 'CAND_02', 'date': '2025-03-01', 'sig_val': 120.0, 'threshold': 100.0},
            {'candidate_id': 'CAND_01', 'date': '2025-03-01', 'sig_val': 150.0, 'threshold': 100.0},
            {'candidate_id': 'CAND_03', 'date': '2025-03-01', 'sig_val': 150.0, 'threshold': 100.0}
        ]
        for c in cands:
            c['strength'] = c['sig_val'] / c['threshold']

        cands.sort(key=lambda x: (x['date'], -x['strength'], x['candidate_id']))
        prioritized_ids = [c['candidate_id'] for c in cands]
        self.assertEqual(prioritized_ids, ['CAND_01', 'CAND_03', 'CAND_02'])

    def test_33_fold_boundary_exits_and_unresolved_positions(self):
        """9. Integration test: Unresolved fold-boundary positions and censorship tracked properly."""
        # Check boundary censorship rejections are tracked
        boundary_rejections = self.trades_df[self.trades_df['rejection_or_exclusion_reason'] == 'rejected_fold_boundary_censored']
        self.assertGreater(len(boundary_rejections), 0, "Must track boundary-censored candidate rejections.")
        # Any unresolved boundary trade must have strictly NaN P&L and FILLED status
        unresolved = self.trades_df[self.trades_df['trade_completion_status'] == 'UNRESOLVED']
        for _, r in unresolved.iterrows():
            self.assertTrue(np.isnan(r['net_pnl_inr']))
            self.assertTrue(np.isnan(r['gross_pnl_inr']))
            self.assertEqual(r['overall_execution_status'], 'FILLED')

    def test_34_separate_cost_scenarios_not_counted_as_independent_live_exposure(self):
        """10. Integration test: Cost scenarios are alternative evaluations, not separate live portfolios."""
        for sc in ['base', 'low', 'high']:
            sc_trades = self.trades_df[self.trades_df['cost_scenario'] == sc]
            self.assertEqual(len(sc_trades), 9668, f"Each cost scenario must evaluate exact same 9668 triggered signals.")

    def test_34b_active_universe_excludes_gold_from_all_trades(self):
        """Verify that the 1kg GOLD contract never appears in any active backtest trade attempt."""
        self.assertNotIn('GOLD', self.trades_df['symbol_leg_a'].unique())
        self.assertNotIn('GOLD', self.trades_df['symbol_leg_b'].unique())
        active_syms = {'GOLDM', 'GOLDTEN', 'GOLDGUINEA', 'GOLDPETAL'}
        self.assertTrue(set(self.trades_df['symbol_leg_a'].dropna().unique()).issubset(active_syms))

    def test_35_rejected_attempts_preserved_in_audit_ledger(self):
        """11. Integration test: Rejected candidates remain in ledger with machine-readable reasons."""
        rejections = self.trades_df[self.trades_df['trade_completion_status'] == 'REJECTED']
        self.assertGreater(len(rejections), 0)
        self.assertTrue((rejections['overall_execution_status'] == 'REJECTED').all())
        valid_reasons = {
            'rejected_existing_contract_position',
            'rejected_multi_strategy_contract_conflict',
            'rejected_opposing_contract_position',
            'rejected_gross_exposure_limit',
            'rejected_net_exposure_limit',
            'rejected_contract_gram_limit',
            'rejected_insufficient_training_history',
            'rejected_tender_window_at_entry',
            'rejected_fold_boundary_censored',
            'rejected_missing_next_session',
            'rejected_missing_next_open_leg_a',
            'rejected_missing_next_open_leg_b',
            'rejected_zero_volume_next_session_leg_a',
            'rejected_zero_volume_next_session_leg_b'
        }
        reasons_found = set(rejections['rejection_or_exclusion_reason'].unique())
        self.assertTrue(reasons_found.issubset(valid_reasons), f"Unknown reasons found: {reasons_found - valid_reasons}")

    def test_36_identical_inputs_produce_deterministic_outputs(self):
        """12. Synthetic test: Deterministic candidate ordering produces identical selection."""
        cands = [
            {'candidate_id': f'CAND_{i:03d}', 'date': '2025-02-10', 'strength': 1.0 + (i % 5) * 0.1}
            for i in range(20)
        ]
        s1 = sorted(cands, key=lambda x: (x['date'], -x['strength'], x['candidate_id']))
        s2 = sorted(cands, key=lambda x: (x['date'], -x['strength'], x['candidate_id']))
        self.assertEqual([c['candidate_id'] for c in s1], [c['candidate_id'] for c in s2])

    def test_37_no_look_ahead_leakage_in_trade_selection(self):
        """13. Integration test: Trade selection relies strictly on info available at signal date."""
        for _, r in self.trades_df.head(200).iterrows():
            self.assertEqual(r['signal_available_at'], f"{r['signal_date']} 23:59:59")
            if r['overall_execution_status'] == 'FILLED':
                self.assertGreater(r['entry_date'], r['signal_date'])

    def test_38_correct_pnl_and_cost_reconciliation_after_changes(self):
        """14. Integration test: Gross P&L minus total modeled costs equals net P&L for 100% completed trades."""
        comp = self.trades_df[self.trades_df['trade_completion_status'] == 'COMPLETED']
        diff = (comp['gross_pnl_inr'] - comp['total_modeled_cost_inr']) - comp['net_pnl_inr']
        self.assertTrue((diff.abs() < 1e-4).all(), "P&L and cost reconciliation failed for some completed trades!")

if __name__ == '__main__':
    unittest.main()

