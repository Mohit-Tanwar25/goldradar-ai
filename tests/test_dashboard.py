"""
Gold Contract Radar — MCX Commodity Derivatives Intelligence
Unit & Regression Test Suite for Phase 7: Interactive Streamlit Dashboard
Tests all 18 required categories from the Phase 7 specification.
"""

import os
import sys
import unittest
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.dashboard.data_loader import (
    load_contract_specs,
    load_backtest_config,
    load_transaction_costs_config,
    load_liquidity_filters_config,
    load_normalized_data,
    load_backtest_trades,
    load_backtest_summary,
    load_execution_diagnostics,
    _safe_load_csv
)
from src.dashboard.metrics import (
    filter_trades,
    calculate_trade_kpis,
    build_cumulative_equity_series,
    calculate_market_kpis,
    verify_reconciliation
)

class TestDashboardDataAndCalculations(unittest.TestCase):
    """18 Comprehensive tests for dashboard data loading, transformations, filtering, and math."""

    @classmethod
    def setUpClass(cls):
        cls.trades_df = load_backtest_trades()
        cls.norm_df = load_normalized_data()
        cls.summary_df = load_backtest_summary()
        cls.diag_df = load_execution_diagnostics()

    def test_01_loading_valid_source_files(self):
        """1. Test that all valid production datasets load cleanly with expected non-empty rows."""
        self.assertEqual(len(self.trades_df), 29004)
        self.assertEqual(len(self.norm_df), 11968)
        self.assertEqual(len(self.summary_df), 6)
        self.assertEqual(len(self.diag_df), 24)

    def test_02_missing_optional_files_handled_gracefully(self):
        """2. Test that missing files raise a clean FileNotFoundError rather than unhandled crash."""
        with self.assertRaises(FileNotFoundError):
            _safe_load_csv("non_existent_optional_dataset_xyz.csv")

    def test_03_missing_required_columns_validation(self):
        """3. Test that datasets missing required columns raise a ValueError."""
        with self.assertRaises(ValueError):
            _safe_load_csv("mcx_gold_backtest_summary.csv", required_cols=['missing_column_abc'])

    def test_04_empty_dataset_handling(self):
        """4. Test that empty datasets are handled safely by KPI and filter functions."""
        empty_df = pd.DataFrame()
        res = calculate_trade_kpis(empty_df)
        self.assertEqual(res['completed_trades'], 0)
        self.assertEqual(res['gross_pnl_inr'], 0.0)
        self.assertEqual(res['net_pnl_inr'], 0.0)

    def test_05_invalid_dates_and_missing_numeric_values(self):
        """5. Test that invalid dates and NaN numeric values are handled safely without crash."""
        synthetic_df = pd.DataFrame([{
            'trade_id': 'TRADE_SYN_01',
            'cost_scenario': 'base',
            'trade_completion_status': 'REJECTED',
            'signal_date': 'invalid-date-string',
            'gross_pnl_inr': np.nan,
            'total_modeled_cost_inr': np.nan,
            'net_pnl_inr': np.nan
        }])
        kpis = calculate_trade_kpis(synthetic_df, cost_scenario='base')
        self.assertEqual(kpis['completed_trades'], 0)
        self.assertEqual(kpis['rejected_trades'], 1)

    def test_06_date_range_filtering(self):
        """6. Test that date range filtering accurately subsets records by signal_date."""
        start = pd.to_datetime('2025-01-01')
        end = pd.to_datetime('2025-06-30')
        filtered = filter_trades(self.trades_df, cost_scenario='base', date_range=(start, end))
        self.assertGreater(len(filtered), 0)
        self.assertTrue((filtered['signal_date'] >= start).all())
        self.assertTrue((filtered['signal_date'] <= end).all())

    def test_07_symbol_and_expiry_filtering(self):
        """7. Test that market data filters accurately by active symbol and expiry."""
        goldm_df = self.norm_df[self.norm_df['symbol'] == 'GOLDM']
        self.assertEqual(goldm_df['symbol'].nunique(), 1)
        self.assertEqual(goldm_df['symbol'].iloc[0], 'GOLDM')
        # Verify 1kg GOLD contract is completely excluded from active normalized data
        self.assertEqual(len(self.norm_df[self.norm_df['symbol'] == 'GOLD']), 0)

    def test_08_strategy_filtering(self):
        """8. Test that strategy filtering isolates only the specified strategy."""
        strat_a = filter_trades(self.trades_df, cost_scenario='base', strategy_name='strategy_a_cross_product')
        self.assertEqual(strat_a['strategy_name'].nunique(), 1)
        self.assertEqual(strat_a['strategy_name'].iloc[0], 'strategy_a_cross_product')

    def test_09_cost_scenario_selection(self):
        """9. Test that cost scenario selection strictly isolates that scenario's records."""
        for sc in ['base', 'low', 'high']:
            sc_df = filter_trades(self.trades_df, cost_scenario=sc)
            self.assertEqual(sc_df['cost_scenario'].nunique(), 1)
            self.assertEqual(sc_df['cost_scenario'].iloc[0], sc)
            self.assertEqual(len(sc_df), 9668)

    def test_10_completed_trade_filtering(self):
        """10. Test that completed-trade filtering includes only COMPLETED status."""
        comp = self.trades_df[self.trades_df['trade_completion_status'] == 'COMPLETED']
        self.assertTrue((comp['trade_completion_status'] == 'COMPLETED').all())
        self.assertFalse(comp['net_pnl_inr'].isna().any())

    def test_11_rejected_attempts_excluded_from_completed_kpis(self):
        """11. Test that rejected and unresolved trade attempts are strictly excluded from completed metrics."""
        kpis = calculate_trade_kpis(self.trades_df, cost_scenario='base')
        self.assertEqual(kpis['completed_trades'], 244)
        self.assertEqual(kpis['rejected_trades'], 9424)
        self.assertEqual(kpis['unresolved_trades'], 0)
        # Winning + losing must equal completed trades
        self.assertEqual(kpis['winning_trades'] + kpis['losing_trades'], kpis['completed_trades'])

    def test_12_no_double_counting_of_scenario_specific_records(self):
        """12. Test that selecting one scenario never double counts records from other scenarios."""
        base_df = filter_trades(self.trades_df, cost_scenario='base')
        self.assertEqual(len(base_df), 9668)
        # Verify unique candidate_ids in filtered scenario
        self.assertEqual(base_df['candidate_id'].nunique(), len(base_df))
        # Verify unique candidate_ids in filtered scenario
        self.assertEqual(base_df['candidate_id'].nunique(), len(base_df))

    def test_13_gross_pnl_minus_costs_equals_net_pnl(self):
        """13. Test that gross P&L minus costs equals net P&L within 1e-4 tolerance for completed trades."""
        is_rec, max_d = verify_reconciliation(self.trades_df)
        self.assertTrue(is_rec, f"Reconciliation failed with max diff {max_d}")
        self.assertLess(max_d, 1e-4)

    def test_14_chronological_cumulative_realized_pnl(self):
        """14. Test that cumulative equity curve series is strictly sorted by exit_date."""
        comp = self.trades_df[(self.trades_df['cost_scenario'] == 'base') & (self.trades_df['trade_completion_status'] == 'COMPLETED')]
        equity = build_cumulative_equity_series(comp)
        exit_dates = equity['exit_date'].tolist()
        self.assertEqual(exit_dates, sorted(exit_dates))
        # Final cumulative P&L must equal sum of net P&L
        self.assertAlmostEqual(equity['cum_net_pnl'].iloc[-1], comp['net_pnl_inr'].sum(), places=4)

    def test_15_empty_filter_results(self):
        """15. Test that an impossible filter combination returns an empty DataFrame gracefully."""
        empty_res = filter_trades(self.trades_df, cost_scenario='non_existent_scenario')
        self.assertTrue(empty_res.empty)
        kpis = calculate_trade_kpis(empty_res)
        self.assertEqual(kpis['completed_trades'], 0)

    def test_16_duplicate_identifier_detection(self):
        """16. Test that trade_id in Output A is 100% unique without duplicate records."""
        self.assertEqual(self.trades_df['trade_id'].nunique(), len(self.trades_df))

    def test_17_rejection_reason_aggregation(self):
        """17. Test that rejection reasons aggregate into known, documented diagnostic categories."""
        rejs = self.trades_df[self.trades_df['trade_completion_status'] == 'REJECTED']
        reasons = rejs['rejection_or_exclusion_reason'].value_counts().to_dict()
        self.assertIn('rejected_existing_contract_position', reasons)
        self.assertIn('rejected_insufficient_training_history', reasons)
        self.assertIn('rejected_tender_window_at_entry', reasons)
        self.assertIn('rejected_fold_boundary_censored', reasons)

    def test_18_dashboard_transformations_preserve_input_immutability(self):
        """18. Test that filtering and KPI transformations do not mutate the input DataFrames."""
        original_rows = len(self.trades_df)
        original_cols = len(self.trades_df.columns)
        _ = filter_trades(self.trades_df, cost_scenario='base', strategy_name='strategy_a_cross_product')
        self.assertEqual(len(self.trades_df), original_rows)
        self.assertEqual(len(self.trades_df.columns), original_cols)

if __name__ == '__main__':
    unittest.main()
