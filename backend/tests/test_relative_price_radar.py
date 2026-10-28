"""
Automated Test Suite for Phase 4: Relative Price Radar & Term Structure Engine
Tests formulas, synthetic edge cases, hand-calculated examples, and production dataset invariants.
Covers all required test categories from the Phase 4 specification.
"""

import unittest
import os
import sys
from datetime import datetime
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from build_relative_price_radar import (
    safe_relative_difference,
    safe_annualized_spread,
    load_and_validate_input,
    build_relative_price_radar,
    build_term_structure_spreads,
    build_term_structure_snapshots,
    run_pipeline
)

RADAR_CSV = os.path.join(PROJECT_ROOT, "data", "processed", "mcx_gold_relative_price_radar.csv")
TERM_CSV = os.path.join(PROJECT_ROOT, "data", "processed", "mcx_gold_term_structure.csv")
SNAPSHOT_CSV = os.path.join(PROJECT_ROOT, "data", "processed", "mcx_gold_term_structure_snapshots.csv")
NORMALIZED_CSV = os.path.join(PROJECT_ROOT, "data", "processed", "mcx_gold_normalized.csv")

class TestSyntheticFormulasAndEdgeCases(unittest.TestCase):
    """Synthetic unit tests with hand-calculated expected values and boundary conditions."""
    
    def test_quoted_price_difference_formula(self):
        """Test quoted price difference: diff = price_a - price_b."""
        diff, _ = safe_relative_difference(14200.0, 14000.0)
        self.assertAlmostEqual(diff, 200.0, places=6)
        
        diff_neg, _ = safe_relative_difference(13800.0, 14000.0)
        self.assertAlmostEqual(diff_neg, -200.0, places=6)

    def test_fine_price_difference_formula(self):
        """Test fine-gold equivalent price difference."""
        # e.g. leg A fine = 14250.0, leg B fine = 14200.0
        diff, rel_pct = safe_relative_difference(14250.0, 14200.0)
        self.assertAlmostEqual(diff, 50.0, places=6)
        self.assertAlmostEqual(rel_pct, 100.0 * 50.0 / 14200.0, places=6)

    def test_relative_difference_and_invalid_denominators(self):
        """Relative difference must return NaN if denominator is missing, zero, or negative."""
        # Valid calculation
        diff, rel_pct = safe_relative_difference(105.0, 100.0)
        self.assertAlmostEqual(rel_pct, 5.0, places=6)
        
        # Denominator == 0
        diff, rel_pct = safe_relative_difference(100.0, 0.0)
        self.assertTrue(np.isnan(diff) and np.isnan(rel_pct))
        
        # Denominator < 0
        diff, rel_pct = safe_relative_difference(100.0, -50.0)
        self.assertTrue(np.isnan(diff) and np.isnan(rel_pct))
        
        # Denominator is NaN
        diff, rel_pct = safe_relative_difference(100.0, np.nan)
        self.assertTrue(np.isnan(diff) and np.isnan(rel_pct))
        
        # Numerator is NaN
        diff, rel_pct = safe_relative_difference(np.nan, 100.0)
        self.assertTrue(np.isnan(diff) and np.isnan(rel_pct))

    def test_same_date_matching_invariant(self):
        """Verify cross-product pairs only match observations from the exact same observation date."""
        mock_data = pd.DataFrame([
            {'date': '2024-01-01', 'expiry_date': '2024-02-05', 'symbol': 'GOLD', 'close_per_gram': 6200.0, 'close_fine_per_gram': 6231.155779, 'is_executable_traded': True, 'source_file': 'f1'},
            # Next day: must NEVER form a pair with 2024-01-01
            {'date': '2024-01-02', 'expiry_date': '2024-02-05', 'symbol': 'GOLDM', 'close_per_gram': 6210.0, 'close_fine_per_gram': 6241.206030, 'is_executable_traded': True, 'source_file': 'f2'},
        ])
        radar = build_relative_price_radar(mock_data)
        # Should be empty because no two symbols share the same date and expiry
        self.assertEqual(len(radar), 0)

    def test_same_expiry_cross_product_identification(self):
        """Verify cross-product primary radar only pairs matching expiry dates."""
        mock_data = pd.DataFrame([
            {'date': '2024-01-01', 'expiry_date': '2024-02-05', 'symbol': 'GOLD', 'close_per_gram': 6200.0, 'close_fine_per_gram': 6231.155779, 'is_executable_traded': True, 'source_file': 'f1'},
            {'date': '2024-01-01', 'expiry_date': '2024-04-05', 'symbol': 'GOLDM', 'close_per_gram': 6250.0, 'close_fine_per_gram': 6281.407035, 'is_executable_traded': True, 'source_file': 'f2'},
        ])
        radar = build_relative_price_radar(mock_data)
        # Different expiries on the same date should not form same-expiry pairs
        self.assertEqual(len(radar), 0)

    def test_no_self_pairs_or_reversed_duplicates(self):
        """Verify symbol_a < symbol_b ordering strictly prevents self-pairs and reversed duplicate pairs."""
        mock_data = pd.DataFrame([
            {'date': '2024-01-01', 'expiry_date': '2024-02-05', 'symbol': 'GOLD', 'close_per_gram': 6200.0, 'close_fine_per_gram': 6231.155779, 'is_executable_traded': True, 'source_file': 'f1'},
            {'date': '2024-01-01', 'expiry_date': '2024-02-05', 'symbol': 'GOLDM', 'close_per_gram': 6210.0, 'close_fine_per_gram': 6241.206030, 'is_executable_traded': True, 'source_file': 'f2'},
        ])
        radar = build_relative_price_radar(mock_data)
        self.assertEqual(len(radar), 1)
        row = radar.iloc[0]
        self.assertEqual(row['symbol_a'], 'GOLD')
        self.assertEqual(row['symbol_b'], 'GOLDM')
        # Reversed pair GOLDM vs GOLD must NOT appear
        rev = radar[(radar['symbol_a'] == 'GOLDM') & (radar['symbol_b'] == 'GOLD')]
        self.assertEqual(len(rev), 0)
        # Self pair GOLD vs GOLD must NOT appear
        self_pair = radar[radar['symbol_a'] == radar['symbol_b']]
        self.assertEqual(len(self_pair), 0)

    def test_calendar_spread_formula_and_ordering(self):
        """Verify calendar spreads enforce strictly nearer_expiry < deferred_expiry and deferred - nearer."""
        mock_data = pd.DataFrame([
            {'date': '2024-01-01', 'symbol': 'GOLD', 'expiry_date': '2024-04-05', 'close_per_gram': 6350.0, 'close_fine_per_gram': 6381.909548, 'is_executable_traded': True, 'source_file': 'f2'},
            {'date': '2024-01-01', 'symbol': 'GOLD', 'expiry_date': '2024-02-05', 'close_per_gram': 6300.0, 'close_fine_per_gram': 6331.658291, 'is_executable_traded': True, 'source_file': 'f1'},
        ])
        term = build_term_structure_spreads(mock_data)
        self.assertEqual(len(term), 1)
        row = term.iloc[0]
        self.assertEqual(row['nearer_expiry'], '2024-02-05')
        self.assertEqual(row['deferred_expiry'], '2024-04-05')
        self.assertAlmostEqual(row['quoted_calendar_spread_per_gram'], 50.0, places=4)
        self.assertAlmostEqual(row['fine_calendar_spread_per_gram'], 6381.909548 - 6331.658291, places=4)

    def test_positive_expiry_gap_validation(self):
        """Verify calendar_days_between_expiries is strictly positive and non-positive gaps are rejected."""
        mock_data = pd.DataFrame([
            {'date': '2024-01-01', 'symbol': 'GOLD', 'expiry_date': '2024-02-05', 'close_per_gram': 6300.0, 'close_fine_per_gram': 6331.658291, 'is_executable_traded': True, 'source_file': 'f1'},
            {'date': '2024-01-01', 'symbol': 'GOLD', 'expiry_date': '2024-02-05', 'close_per_gram': 6300.0, 'close_fine_per_gram': 6331.658291, 'is_executable_traded': True, 'source_file': 'f2'},
        ])
        term = build_term_structure_spreads(mock_data)
        # Identical expiry should produce 0 rows because days_gap == 0
        self.assertEqual(len(term), 0)

    def test_annualized_spread_formula_and_invalid_inputs(self):
        """
        Hand-calculated annualized spread test:
        nearer = 10000.0, deferred = 10200.0, days = 60
        ann_pct = 100 * ((10200/10000) - 1) * (365 / 60) = 2.0 * 6.08333333 = 12.166667%
        """
        ann_pct = safe_annualized_spread(10000.0, 10200.0, 60)
        self.assertAlmostEqual(ann_pct, 12.166666666666666, places=6)
        
        # Zero days gap returns NaN
        self.assertTrue(np.isnan(safe_annualized_spread(10000.0, 10200.0, 0)))
        # Negative days gap returns NaN
        self.assertTrue(np.isnan(safe_annualized_spread(10000.0, 10200.0, -10)))
        # Zero nearer price returns NaN
        self.assertTrue(np.isnan(safe_annualized_spread(0.0, 10200.0, 60)))
        # Negative nearer price returns NaN
        self.assertTrue(np.isnan(safe_annualized_spread(-1000.0, 10200.0, 60)))
        # Missing price returns NaN
        self.assertTrue(np.isnan(safe_annualized_spread(np.nan, 10200.0, 60)))

    def test_non_executable_observations_handling(self):
        """Verify is_both_executable is False when either leg is non-executable."""
        mock_data = pd.DataFrame([
            {'date': '2024-01-01', 'expiry_date': '2024-02-05', 'symbol': 'GOLD', 'close_per_gram': 6200.0, 'close_fine_per_gram': 6231.155779, 'is_executable_traded': True, 'source_file': 'f1'},
            {'date': '2024-01-01', 'expiry_date': '2024-02-05', 'symbol': 'GOLDM', 'close_per_gram': 6210.0, 'close_fine_per_gram': 6241.206030, 'is_executable_traded': False, 'source_file': 'f2'},
        ])
        radar = build_relative_price_radar(mock_data)
        self.assertEqual(len(radar), 1)
        row = radar.iloc[0]
        self.assertTrue(row['is_executable_a'])
        self.assertFalse(row['is_executable_b'])
        self.assertFalse(row['is_both_executable'])

    def test_missing_data_preservation_as_null(self):
        """Missing price values must produce null in differences and spreads, never zero."""
        diff, rel = safe_relative_difference(np.nan, 1000.0)
        self.assertTrue(np.isnan(diff) and np.isnan(rel))
        self.assertNotEqual(diff, 0.0)
        self.assertNotEqual(rel, 0.0)

    def test_sparse_dates_and_missing_expiry_pairs(self):
        """Dates with only 1 active contract or 1 active expiry must not generate spurious pairs."""
        mock_data = pd.DataFrame([
            {'date': '2024-01-01', 'expiry_date': '2024-02-05', 'symbol': 'GOLD', 'close_per_gram': 6200.0, 'close_fine_per_gram': 6231.155779, 'is_executable_traded': True, 'source_file': 'f1'}
        ])
        radar = build_relative_price_radar(mock_data)
        term = build_term_structure_spreads(mock_data)
        self.assertEqual(len(radar), 0)
        self.assertEqual(len(term), 0)

    def test_expired_contracts_flagging_in_snapshots(self):
        """Snapshots must accurately compute days_to_expiry and identify expired contracts if days < 0."""
        mock_data = pd.DataFrame([
            {'date': '2024-02-10', 'symbol': 'GOLD', 'expiry_date': '2024-02-05', 'close_per_gram': 6200.0, 'close_fine_per_gram': 6231.155779, 'is_executable_traded': True, 'volume_lots': 10, 'open_interest_lots': 5, 'source_file': 'f1'},
            {'date': '2024-02-05', 'symbol': 'GOLD', 'expiry_date': '2024-02-05', 'close_per_gram': 6200.0, 'close_fine_per_gram': 6231.155779, 'is_executable_traded': True, 'volume_lots': 10, 'open_interest_lots': 5, 'source_file': 'f2'},
        ])
        snapshots = build_term_structure_snapshots(mock_data)
        self.assertEqual(len(snapshots), 2)
        # Check record dated after nominal expiry: days_to_expiry == -5
        expired_row = snapshots[snapshots['days_to_expiry'] < 0].iloc[0]
        self.assertEqual(expired_row['days_to_expiry'], -5)
        # Check record on expiry day: days_to_expiry == 0
        expiry_day_row = snapshots[snapshots['days_to_expiry'] == 0].iloc[0]
        self.assertEqual(expiry_day_row['days_to_expiry'], 0)

    def test_input_duplicate_detection(self):
        """load_and_validate_input must raise ValueError if input has duplicate keys."""
        temp_dup_csv = os.path.join(PROJECT_ROOT, "tests", "temp_dup.csv")
        try:
            # Create a small dataset with duplicate primary keys
            df_norm = pd.read_csv(NORMALIZED_CSV).head(10).copy()
            df_dup = pd.concat([df_norm, df_norm.iloc[[0]]], ignore_index=True)
            df_dup.to_csv(temp_dup_csv, index=False)
            with self.assertRaises(ValueError):
                load_and_validate_input(temp_dup_csv)
        finally:
            if os.path.exists(temp_dup_csv):
                os.remove(temp_dup_csv)


class TestProductionOutputs(unittest.TestCase):
    """Validation tests against the generated production datasets."""
    
    @classmethod
    def setUpClass(cls):
        cls.radar = pd.read_csv(RADAR_CSV)
        cls.term = pd.read_csv(TERM_CSV)
        cls.snapshots = pd.read_csv(SNAPSHOT_CSV)
        cls.normalized = pd.read_csv(NORMALIZED_CSV)

    def test_output_a_integrity(self):
        """Test Output A schema, uniqueness, and constraints."""
        self.assertEqual(len(self.radar), 7672)
        expected_cols = [
            'date', 'pair_type', 'symbol_a', 'expiry_a', 'symbol_b', 'expiry_b',
            'close_per_gram_a', 'close_per_gram_b', 'quoted_price_difference_per_gram',
            'quoted_relative_difference_pct', 'close_fine_per_gram_a', 'close_fine_per_gram_b',
            'fine_price_difference_per_gram', 'fine_relative_difference_pct',
            'is_executable_a', 'is_executable_b', 'is_both_executable',
            'comparison_basis', 'source_file_a', 'source_file_b'
        ]
        self.assertEqual(list(self.radar.columns), expected_cols)
        # No reversed duplicates or self-pairs
        self.assertEqual((self.radar['symbol_a'] == self.radar['symbol_b']).sum(), 0)
        self.assertEqual(self.radar.duplicated(subset=['date', 'symbol_a', 'expiry_a', 'symbol_b', 'expiry_b']).sum(), 0)
        # All are same_expiry
        self.assertEqual((self.radar['expiry_a'] != self.radar['expiry_b']).sum(), 0)
        self.assertEqual((self.radar['pair_type'] != 'same_expiry_cross_product').sum(), 0)
        self.assertEqual((self.radar['comparison_basis'] != 'same_expiry').sum(), 0)
        # Active 4-contract universe check: GOLD must not appear in symbol_a or symbol_b
        active_syms = {'GOLDM', 'GOLDTEN', 'GOLDGUINEA', 'GOLDPETAL'}
        self.assertTrue(set(self.radar['symbol_a'].unique()).issubset(active_syms))
        self.assertTrue(set(self.radar['symbol_b'].unique()).issubset(active_syms))
        self.assertNotIn('GOLD', self.radar['symbol_a'].unique())
        self.assertNotIn('GOLD', self.radar['symbol_b'].unique())

    def test_output_b_integrity(self):
        """Test Output B schema, uniqueness, and ordering constraints."""
        self.assertEqual(len(self.term), 23811)
        expected_cols = [
            'date', 'symbol', 'nearer_expiry', 'deferred_expiry',
            'nearer_close_per_gram', 'deferred_close_per_gram',
            'quoted_calendar_spread_per_gram', 'quoted_relative_calendar_spread_pct',
            'nearer_close_fine_per_gram', 'deferred_close_fine_per_gram',
            'fine_calendar_spread_per_gram', 'fine_relative_calendar_spread_pct',
            'calendar_days_between_expiries', 'fine_annualized_spread_pct',
            'nearer_is_executable', 'deferred_is_executable', 'is_both_executable',
            'source_file_nearer', 'source_file_deferred'
        ]
        self.assertEqual(list(self.term.columns), expected_cols)
        # Chronological ordering strictly enforced
        dt_near = pd.to_datetime(self.term['nearer_expiry'])
        dt_def = pd.to_datetime(self.term['deferred_expiry'])
        self.assertTrue((dt_near < dt_def).all())
        self.assertTrue((self.term['calendar_days_between_expiries'] > 0).all())
        # No duplicate pairs
        self.assertEqual(self.term.duplicated(subset=['date', 'symbol', 'nearer_expiry', 'deferred_expiry']).sum(), 0)
        # Active 4-contract universe check: GOLD must not appear in term structure
        active_syms = {'GOLDM', 'GOLDTEN', 'GOLDGUINEA', 'GOLDPETAL'}
        self.assertTrue(set(self.term['symbol'].unique()).issubset(active_syms))
        self.assertNotIn('GOLD', self.term['symbol'].unique())

    def test_output_c_integrity(self):
        """Test Output C row parity, zero expired contracts, and days_to_expiry calculation."""
        self.assertEqual(len(self.snapshots), len(self.normalized))
        self.assertEqual(len(self.snapshots), 11968)
        expected_cols = [
            'date', 'symbol', 'expiry_date', 'days_to_expiry',
            'close_per_gram', 'close_fine_per_gram', 'is_executable_traded',
            'volume_lots', 'open_interest_lots', 'source_file'
        ]
        self.assertEqual(list(self.snapshots.columns), expected_cols)
        # Days to expiry must be >= 0 (no records after nominal expiry)
        self.assertEqual((self.snapshots['days_to_expiry'] < 0).sum(), 0)
        # Active 4-contract universe check: GOLD must not appear in snapshots
        active_syms = {'GOLDM', 'GOLDTEN', 'GOLDGUINEA', 'GOLDPETAL'}
        self.assertTrue(set(self.snapshots['symbol'].unique()).issubset(active_syms))
        self.assertNotIn('GOLD', self.snapshots['symbol'].unique())
        
        # Spot check days_to_expiry = expiry_date - date
        sample = self.snapshots.sample(n=30, random_state=42)
        for _, row in sample.iterrows():
            d_trade = datetime.strptime(row['date'], '%Y-%m-%d')
            d_exp = datetime.strptime(row['expiry_date'], '%Y-%m-%d')
            self.assertEqual(row['days_to_expiry'], (d_exp - d_trade).days)

    def test_deterministic_outputs_on_repeated_runs(self):
        """Verify pipeline execution is 100% deterministic."""
        radar_df = build_relative_price_radar(self.normalized)
        pd.testing.assert_frame_equal(self.radar, radar_df, check_like=False)

if __name__ == '__main__':
    unittest.main()
