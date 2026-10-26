"""
Gold Contract Radar — MCX Commodity Derivatives Intelligence
Independent Correctness & Backtest Reconciliation Test Suite
Authoritative tests verifying exact portfolio figures, gold beta independence, and dataset hashes.
"""

import os
import sys
import hashlib
from pathlib import Path
import unittest
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.dashboard.data_loader import (
    load_contract_specs,
    load_normalized_data,
    load_backtest_trades,
    load_backtest_summary
)
from src.dashboard.metrics import (
    calculate_trade_kpis,
    verify_reconciliation
)

class TestIndependentAuditReconciliation(unittest.TestCase):
    """Rigorous independent test suite verifying backtest ledger reconciliation, gold beta, and dataset integrity."""

    @classmethod
    def setUpClass(cls):
        cls.trades_df = load_backtest_trades()
        cls.summary_df = load_backtest_summary()
        cls.norm_df = load_normalized_data()
        cls.specs_cfg = load_contract_specs()

    def test_01_canonical_dataset_sha256_hashes(self):
        """1. Verify that all 12 active datasets match their canonical SHA-256 hashes exactly."""
        expected_hashes = {
            'mcx_gold_master.csv': '0efb75ed225bf6515c77d66015a92e629651515acd54e8bb9611b71c751a55e4',
            'mcx_gold_normalized.csv': '8eb15f5353e8df883758d28b46f0d63cb68066ebd95d93303dd6cbb4d3b5ffb2',
            'mcx_gold_relative_price_radar.csv': 'bf746998b24560a9e926d18fdf12cabbda70ce68dada0c98afd8be88463770f7',
            'mcx_gold_term_structure.csv': '9d78f67db6120f3e62ae53d7f0209d32cc0f561c6eb7bce5c09c14b67281bc45',
            'mcx_gold_term_structure_snapshots.csv': '775c4bbafa2410c6f7dd5659f74a27fa32e1dfd534b26e3c1fc87a467f759c9f',
            'mcx_gold_liquidity_filtered_candidates.csv': '39432f3bbcd45898e8627459955e945aa04d21867db6d9a6846677e3089a0210',
            'mcx_gold_transaction_cost_scenarios.csv': '7c852bf0ea361495fea9d3ca26625a3899944699d0cf47760b6c238a945803e1',
            'mcx_gold_eligible_candidates.csv': '0e8299fb816c8c851d99564c62a53a1ab19fedd85191926d71860c5248f767bc',
            'mcx_gold_backtest_trades.csv': '4743ea47d188909f3bce5d87c5691f4a5adc80dfbd940c46c1c44e0e8485b59a',
            'mcx_gold_walk_forward_metrics.csv': 'f5c37580a80e0196a42423906a50bc4bdd0453c2b938d334e8f5847c5a22ed9c',
            'mcx_gold_backtest_summary.csv': '55fba227ce03c8cf127c7e74a88429253a747cb7bc82c4272c880ac74aed46ac',
            'mcx_gold_execution_diagnostics.csv': 'cd4f7df6f0a4ed6c014fdd71bea1cb6b69fb8993b28e9255af1e1bd94f43fa35',
        }
        for name, exp_h in expected_hashes.items():
            p = Path(DATA_DIR) / name
            calc_h = hashlib.sha256(p.read_bytes()).hexdigest()
            self.assertEqual(calc_h, exp_h, f"Dataset hash mismatch for {name}")

    def test_02_reconciled_base_portfolio_metrics(self):
        """2. Verify exact reconciled base portfolio totals directly from trade ledger."""
        comp = self.trades_df[
            (self.trades_df['cost_scenario'] == 'base') & 
            (self.trades_df['trade_completion_status'] == 'COMPLETED')
        ]
        self.assertEqual(len(comp), 244)
        
        gross_pnl = comp['gross_pnl_inr'].sum()
        total_costs = comp['total_modeled_cost_inr'].sum()
        net_pnl = comp['net_pnl_inr'].sum()
        
        self.assertAlmostEqual(gross_pnl, 59812.00, places=2)
        self.assertAlmostEqual(total_costs, 52516.15, places=2)
        self.assertAlmostEqual(net_pnl, 7295.85, places=2)
        
        # Exact trade-by-trade cashflow reconciliation
        rec_diff = abs(gross_pnl - total_costs - net_pnl)
        self.assertLess(rec_diff, 1e-4)

    def test_03_reconciled_strategy_a_metrics(self):
        """3. Verify Strategy A (Cross-Product Convergence) individual metrics."""
        strat_a = self.trades_df[
            (self.trades_df['cost_scenario'] == 'base') & 
            (self.trades_df['strategy_name'] == 'strategy_a_cross_product') & 
            (self.trades_df['trade_completion_status'] == 'COMPLETED')
        ]
        self.assertEqual(len(strat_a), 82)
        self.assertAlmostEqual(strat_a['gross_pnl_inr'].sum(), 74506.00, places=2)
        self.assertAlmostEqual(strat_a['total_modeled_cost_inr'].sum(), 17537.17, places=2)
        self.assertAlmostEqual(strat_a['net_pnl_inr'].sum(), 56968.83, places=2)
        
        wins = (strat_a['net_pnl_inr'] > 0).sum()
        losses = (strat_a['net_pnl_inr'] <= 0).sum()
        self.assertEqual(wins, 41)
        self.assertEqual(losses, 41)

    def test_04_reconciled_strategy_b_metrics(self):
        """4. Verify Strategy B (Calendar Spread Roll) individual metrics."""
        strat_b = self.trades_df[
            (self.trades_df['cost_scenario'] == 'base') & 
            (self.trades_df['strategy_name'] == 'strategy_b_calendar_spread') & 
            (self.trades_df['trade_completion_status'] == 'COMPLETED')
        ]
        self.assertEqual(len(strat_b), 162)
        self.assertAlmostEqual(strat_b['gross_pnl_inr'].sum(), -14694.00, places=2)
        self.assertAlmostEqual(strat_b['total_modeled_cost_inr'].sum(), 34978.98, places=2)
        self.assertAlmostEqual(strat_b['net_pnl_inr'].sum(), -49672.98, places=2)
        
        wins = (strat_b['net_pnl_inr'] > 0).sum()
        losses = (strat_b['net_pnl_inr'] <= 0).sum()
        self.assertEqual(wins, 58)
        self.assertEqual(losses, 104)

    def test_05_realized_maximum_drawdown_calculation(self):
        """5. Verify the realized maximum drawdown calculation across chronological exits."""
        kpis = calculate_trade_kpis(self.trades_df, cost_scenario='base')
        self.assertAlmostEqual(kpis['realized_max_drawdown_inr'], 186188.75, places=2)

    def test_06_gold_beta_independence(self):
        """6. Verify that strategy returns are market-neutral and uncorrelated with directional gold movement."""
        comp = self.trades_df[
            (self.trades_df['cost_scenario'] == 'base') & 
            (self.trades_df['trade_completion_status'] == 'COMPLETED')
        ].copy()
        norm = self.norm_df.copy()
        
        norm['date'] = pd.to_datetime(norm['date'])
        daily_gold = norm[norm['symbol'] == 'GOLDM'].groupby('date')['close'].first().sort_index()
        gold_ret = daily_gold.pct_change().dropna()
        
        comp['exit_date'] = pd.to_datetime(comp['exit_date'])
        daily_strat = comp.groupby('exit_date')['net_pnl_inr'].sum()
        
        aligned = pd.DataFrame({'strat_pnl': daily_strat, 'gold_ret': gold_ret}).dropna()
        self.assertGreater(len(aligned), 10)
        corr = aligned['strat_pnl'].corr(aligned['gold_ret'])
        
        # Absolute correlation must be below 0.15 confirming market neutrality
        self.assertLess(abs(corr), 0.15, f"Strategy correlation with gold price ({corr:.4f}) exceeds threshold")

    def test_07_four_contract_specifications_exactness(self):
        """7. Verify exact quotation divisors and purity factors for active universe."""
        contracts = self.specs_cfg.get('contracts', {})
        self.assertEqual(contracts['GOLDM']['trading_unit_grams'], 100)
        self.assertEqual(contracts['GOLDM']['quotation_divisor_grams'], 10)
        self.assertEqual(contracts['GOLDM']['fine_gold_factor'], 0.995)
        
        self.assertEqual(contracts['GOLDTEN']['trading_unit_grams'], 10)
        self.assertEqual(contracts['GOLDTEN']['quotation_divisor_grams'], 10)
        self.assertEqual(contracts['GOLDTEN']['fine_gold_factor'], 0.999)
        
        self.assertEqual(contracts['GOLDGUINEA']['trading_unit_grams'], 8)
        self.assertEqual(contracts['GOLDGUINEA']['quotation_divisor_grams'], 8)
        self.assertEqual(contracts['GOLDGUINEA']['fine_gold_factor'], 0.999)
        
        self.assertEqual(contracts['GOLDPETAL']['trading_unit_grams'], 1)
        self.assertEqual(contracts['GOLDPETAL']['quotation_divisor_grams'], 1)
        self.assertEqual(contracts['GOLDPETAL']['fine_gold_factor'], 0.999)
        
        # Standard 1kg GOLD contract must be marked inactive
        self.assertFalse(contracts['GOLD'].get('is_active', True))

if __name__ == '__main__':
    unittest.main()
