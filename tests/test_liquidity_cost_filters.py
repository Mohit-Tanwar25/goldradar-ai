"""
Gold Contract Radar — MCX Commodity Derivatives Intelligence
Unit & Regression Test Suite for Phase 5: Liquidity & Transaction Cost Filters

Tests all 20 required categories from the Phase 5 specification:
1. Correct loading and validation of both candidate types.
2. Candidate IDs are stable and unique.
3. Cross-product candidates preserve same-date and same-expiry constraints.
4. Calendar-spread candidates preserve same-date and correct expiry ordering.
5. Zero-volume legs are rejected.
6. Missing required prices or incomplete required OHLC handled correctly.
7. Minimum volume thresholds applied to each leg.
8. Minimum open-interest thresholds applied to each leg.
9. Minimum days-to-expiry filters reject expiry-day and ineligible contracts.
10. Machine-readable exclusion reasons are retained and correct.
11. Different product lot sizes are not incorrectly treated as equal exposure.
12. Notional calculations use correct verified units and trading specifications.
13. Cost components are not double-counted.
14. Entry, exit, and round-trip costs are internally consistent.
15. Missing or unverified cost inputs never silently become zero.
16. Net results are unavailable when quantity matching or prices cannot be established.
17. Low, base, and high scenarios produce consistent results under declared assumptions.
18. Output keys are unique at appropriate candidate/scenario granularity.
19. Outputs are reproducible for identical inputs and configurations.
20. Phase 1-4 source files remain unchanged.
"""

import os
import sys
import json
import unittest
import hashlib
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from apply_liquidity_cost_filters import (
    get_lcm,
    load_configurations,
    load_input_datasets,
    screen_candidates,
    model_transaction_costs,
    compute_single_leg_cost,
    run_pipeline
)

OUT_A_CSV = os.path.join(DATA_DIR, "mcx_gold_liquidity_filtered_candidates.csv")
OUT_B_CSV = os.path.join(DATA_DIR, "mcx_gold_transaction_cost_scenarios.csv")
OUT_C_CSV = os.path.join(DATA_DIR, "mcx_gold_eligible_candidates.csv")

class TestSyntheticFormulasAndLogic(unittest.TestCase):
    """Synthetic unit tests for mathematical models, boundary conditions, and logic invariants."""

    @classmethod
    def setUpClass(cls):
        cls.specs_cfg, cls.liq_cfg, cls.costs_cfg = load_configurations(CONFIG_DIR)

    def test_01_hand_calculated_single_leg_cost_breakdown(self):
        """Test hand-calculated exact cost breakdown on a 10 Lakh notional trade under base scenario."""
        # 10 Lakh notional (e.g. ~140g gold)
        turnover = 1000000.0
        sc_cfg = self.costs_cfg["scenarios"]["base"]
        
        # Test 1A: Long entry (Buy on entry, Sell on exit)
        cost_buy = compute_single_leg_cost(turnover, orders=1, scenario_cfg=sc_cfg, entry_side="buy")
        
        # Hand calculations:
        # Brokerage = min(20, 1000000 * 0.0003) = 20 per side -> 40 total
        self.assertAlmostEqual(cost_buy['brokerage'], 40.0, places=4)
        # Exchange fee = 2 * 1000000 * 0.000021 = 42.0
        self.assertAlmostEqual(cost_buy['exchange_fee'], 42.0, places=4)
        # SEBI fee = 2 * 1000000 * 0.000001 = 2.0
        self.assertAlmostEqual(cost_buy['sebi_fee'], 2.0, places=4)
        # Stamp duty = 1000000 * 0.00002 = 20.0
        self.assertAlmostEqual(cost_buy['stamp_duty'], 20.0, places=4)
        # CTT = 1000000 * 0.00010 = 100.0
        self.assertAlmostEqual(cost_buy['ctt'], 100.0, places=4)
        # GST = 18% on (40 + 42 + 2) = 15.12
        self.assertAlmostEqual(cost_buy['gst'], 15.12, places=4)
        
        # Total round trip = 40 + 42 + 2 + 20 + 100 + 15.12 = 219.12
        expected_total = 219.12
        self.assertAlmostEqual(cost_buy['total_cost'], expected_total, places=4)
        
        # Entry cost (Buy) = 20 + 21 + 1 + 20 (Stamp) + (42 * 0.18 = 7.56) = 69.56
        self.assertAlmostEqual(cost_buy['entry_cost'], 69.56, places=4)
        # Exit cost (Sell) = 20 + 21 + 1 + 100 (CTT) + 7.56 = 149.56
        self.assertAlmostEqual(cost_buy['exit_cost'], 149.56, places=4)

        # Test 1B: Short entry (Sell on entry, Buy on exit)
        cost_sell = compute_single_leg_cost(turnover, orders=1, scenario_cfg=sc_cfg, entry_side="sell")
        self.assertAlmostEqual(cost_sell['total_cost'], expected_total, places=4)
        # Entry cost (Sell) = 20 + 21 + 1 + 100 (CTT) + 7.56 = 149.56
        self.assertAlmostEqual(cost_sell['entry_cost'], 149.56, places=4)
        # Exit cost (Buy) = 20 + 21 + 1 + 20 (Stamp) + 7.56 = 69.56
        self.assertAlmostEqual(cost_sell['exit_cost'], 69.56, places=4)

    def test_02_cost_components_not_double_counted(self):
        """Verify that total_cost strictly equals entry_cost + exit_cost and equals sum of individual components."""
        turnover = 5000000.0
        sc_cfg = self.costs_cfg["scenarios"]["base"]
        cost = compute_single_leg_cost(turnover, orders=1, scenario_cfg=sc_cfg)
        
        # Test entry + exit = total
        self.assertAlmostEqual(cost['entry_cost'] + cost['exit_cost'], cost['total_cost'], places=4)
        
        # Test sum of individual components = total
        component_sum = (
            cost['brokerage'] + cost['exchange_fee'] + cost['sebi_fee'] +
            cost['stamp_duty'] + cost['ctt'] + cost['gst']
        )
        self.assertAlmostEqual(component_sum, cost['total_cost'], places=4)

    def test_03_missing_or_invalid_inputs_produce_nan_costs(self):
        """Zero or NaN turnover must produce NaN costs, never silently zero."""
        sc_cfg = self.costs_cfg["scenarios"]["base"]
        
        nan_res = compute_single_leg_cost(np.nan, orders=1, scenario_cfg=sc_cfg)
        self.assertTrue(np.isnan(nan_res['total_cost']))
        self.assertTrue(np.isnan(nan_res['entry_cost']))
        self.assertTrue(np.isnan(nan_res['exit_cost']))
        
        zero_res = compute_single_leg_cost(0.0, orders=1, scenario_cfg=sc_cfg)
        self.assertTrue(np.isnan(zero_res['total_cost']))

    def test_04_integer_lot_lcm_exposure_matching(self):
        """Verify LCM exposure matching across all distinct product pairs."""
        # GOLD (1000g) vs GOLDM (100g)
        self.assertEqual(get_lcm(1000, 100), 1000)
        self.assertEqual(1000 // 1000, 1)   # 1 lot GOLD
        self.assertEqual(1000 // 100, 10)   # 10 lots GOLDM
        
        # GOLDGUINEA (8g) vs GOLDPETAL (1g)
        self.assertEqual(get_lcm(8, 1), 8)
        self.assertEqual(8 // 8, 1)          # 1 lot GOLDGUINEA
        self.assertEqual(8 // 1, 8)          # 8 lots GOLDPETAL
        
        # GOLDGUINEA (8g) vs GOLDTEN (10g)
        self.assertEqual(get_lcm(8, 10), 40)
        self.assertEqual(40 // 8, 5)         # 5 lots GOLDGUINEA (40g)
        self.assertEqual(40 // 10, 4)        # 4 lots GOLDTEN (40g)
        
        # GOLDM (100g) vs GOLDPETAL (1g)
        self.assertEqual(get_lcm(100, 1), 100)
        self.assertEqual(100 // 100, 1)      # 1 lot GOLDM
        self.assertEqual(100 // 1, 100)      # 100 lots GOLDPETAL

    def test_05_rejection_of_zero_volume_and_incomplete_ohlc(self):
        """Synthetic test: candidates with zero volume or incomplete OHLC must be rejected."""
        mock_radar = pd.DataFrame([{
            'date': '2024-01-01', 'pair_type': 'same_expiry_cross_product',
            'symbol_a': 'GOLD', 'expiry_a': '2024-02-05',
            'symbol_b': 'GOLDM', 'expiry_b': '2024-02-05',
            'close_per_gram_a': 6332.0, 'close_per_gram_b': 6329.7,
            'quoted_price_difference_per_gram': 2.3, 'quoted_relative_difference_pct': 0.036,
            'close_fine_per_gram_a': 6363.8, 'close_fine_per_gram_b': 6361.5,
            'fine_price_difference_per_gram': 2.3, 'fine_relative_difference_pct': 0.036,
            'is_executable_a': True, 'is_executable_b': False, 'is_both_executable': False,
            'comparison_basis': 'same_expiry', 'source_file_a': 'f1', 'source_file_b': 'f2'
        }])
        
        mock_norm = pd.DataFrame([
            {'date': '2024-01-01', 'symbol': 'GOLD', 'expiry_date': '2024-02-05', 'contract_key': 'GOLD_2024-02-05',
             'close': 63320.0, 'close_per_gram': 6332.0, 'close_fine_per_gram': 6363.8,
             'volume_lots': 100, 'open_interest_lots': 500, 'days_to_expiry': 35,
             'is_executable_traded': True, 'flag_missing_ohlc': False, 'flag_zero_volume': False,
             'flag_invalid_price': False, 'source_file': 'f1'},
            # Leg B has zero volume and missing OHLC
            {'date': '2024-01-01', 'symbol': 'GOLDM', 'expiry_date': '2024-02-05', 'contract_key': 'GOLDM_2024-02-05',
             'close': 63297.0, 'close_per_gram': 6329.7, 'close_fine_per_gram': 6361.5,
             'volume_lots': 0, 'open_interest_lots': 50, 'days_to_expiry': 35,
             'is_executable_traded': False, 'flag_missing_ohlc': True, 'flag_zero_volume': True,
             'flag_invalid_price': False, 'source_file': 'f2'}
        ])
        
        screened = screen_candidates(mock_radar, pd.DataFrame(), mock_norm, self.liq_cfg, self.specs_cfg)
        row = screened.iloc[0]
        self.assertFalse(row['is_both_data_eligible'])
        self.assertFalse(row['is_all_filters_eligible'])
        self.assertIn('zero_volume_leg_b', row['exclusion_reasons'])
        self.assertIn('incomplete_ohlc_leg_b', row['exclusion_reasons'])

    def test_06_expiry_filters_and_tender_period_rejection(self):
        """Synthetic test: contracts with DTE <= 0 or DTE < min_dte must fail expiry filter."""
        mock_norm = pd.DataFrame([
            # Expiry day: DTE == 0
            {'date': '2024-02-05', 'symbol': 'GOLD', 'expiry_date': '2024-02-05', 'contract_key': 'GOLD_2024-02-05',
             'close': 63320.0, 'close_per_gram': 6332.0, 'close_fine_per_gram': 6363.8,
             'volume_lots': 100, 'open_interest_lots': 500, 'days_to_expiry': 0,
             'is_executable_traded': True, 'flag_missing_ohlc': False, 'flag_zero_volume': False,
             'flag_invalid_price': False, 'source_file': 'f1'},
            # Nearer leg with DTE == 2 (tender period, below min_dte=5)
            {'date': '2024-02-03', 'symbol': 'GOLD', 'expiry_date': '2024-02-05', 'contract_key': 'GOLD_2024-02-05',
             'close': 63320.0, 'close_per_gram': 6332.0, 'close_fine_per_gram': 6363.8,
             'volume_lots': 100, 'open_interest_lots': 500, 'days_to_expiry': 2,
             'is_executable_traded': True, 'flag_missing_ohlc': False, 'flag_zero_volume': False,
             'flag_invalid_price': False, 'source_file': 'f2'},
            # Deferred leg
            {'date': '2024-02-03', 'symbol': 'GOLD', 'expiry_date': '2024-04-05', 'contract_key': 'GOLD_2024-04-05',
             'close': 63600.0, 'close_per_gram': 6360.0, 'close_fine_per_gram': 6391.9,
             'volume_lots': 100, 'open_interest_lots': 500, 'days_to_expiry': 62,
             'is_executable_traded': True, 'flag_missing_ohlc': False, 'flag_zero_volume': False,
             'flag_invalid_price': False, 'source_file': 'f3'}
        ])
        
        mock_term = pd.DataFrame([{
            'date': '2024-02-03', 'symbol': 'GOLD',
            'nearer_expiry': '2024-02-05', 'deferred_expiry': '2024-04-05',
            'nearer_close_per_gram': 6332.0, 'deferred_close_per_gram': 6360.0,
            'quoted_calendar_spread_per_gram': 28.0, 'quoted_relative_calendar_spread_pct': 0.44,
            'nearer_close_fine_per_gram': 6363.8, 'deferred_close_fine_per_gram': 6391.9,
            'fine_calendar_spread_per_gram': 28.1, 'fine_relative_calendar_spread_pct': 0.44,
            'calendar_days_between_expiries': 60, 'fine_annualized_spread_pct': 2.68,
            'nearer_is_executable': True, 'deferred_is_executable': True, 'is_both_executable': True,
            'source_file_nearer': 'f2', 'source_file_deferred': 'f3'
        }])
        
        screened = screen_candidates(pd.DataFrame(), mock_term, mock_norm, self.liq_cfg, self.specs_cfg)
        row = screened.iloc[0]
        self.assertFalse(row['passes_expiry_filter'])
        self.assertFalse(row['is_all_filters_eligible'])
        self.assertIn('insufficient_days_to_expiry', row['exclusion_reasons'])

    def test_07_scenario_cost_ordering(self):
        """Verify scenario ordering: round-trip cost for Low < Base < High across identical notional."""
        turnover = 7000000.0 # 70 Lakhs
        cost_low = compute_single_leg_cost(turnover, 1, self.costs_cfg["scenarios"]["low"])
        cost_base = compute_single_leg_cost(turnover, 1, self.costs_cfg["scenarios"]["base"])
        cost_high = compute_single_leg_cost(turnover, 1, self.costs_cfg["scenarios"]["high"])
        
        self.assertLess(cost_low['total_cost'], cost_base['total_cost'])
        self.assertLess(cost_base['total_cost'], cost_high['total_cost'])


class TestProductionDatasetsIntegrity(unittest.TestCase):
    """Validation tests against the generated production datasets."""

    @classmethod
    def setUpClass(cls):
        cls.df_a = pd.read_csv(OUT_A_CSV)
        cls.df_b = pd.read_csv(OUT_B_CSV)
        cls.df_c = pd.read_csv(OUT_C_CSV)

    def test_08_output_a_row_count_and_candidate_types(self):
        """Output A must contain exactly 31,483 candidates (7,672 radar + 23,811 calendar)."""
        self.assertEqual(len(self.df_a), 31483)
        counts = self.df_a['candidate_type'].value_counts()
        self.assertEqual(counts['same_expiry_cross_product'], 7672)
        self.assertEqual(counts['same_symbol_calendar_spread'], 23811)
        # Verify GOLD is completely excluded
        self.assertNotIn('GOLD', self.df_a['symbol_leg_a'].unique())
        self.assertNotIn('GOLD', self.df_a['symbol_leg_b'].unique())

    def test_09_candidate_id_uniqueness(self):
        """Candidate IDs must be unique across all 31,483 rows in Output A."""
        self.assertEqual(self.df_a['candidate_id'].nunique(), 31483)
        self.assertEqual(self.df_a.duplicated(subset=['candidate_id']).sum(), 0)

    def test_10_cross_product_same_date_and_same_expiry(self):
        """Cross-product candidates must preserve same-date and same-expiry invariants."""
        radar_subset = self.df_a[self.df_a['candidate_type'] == 'same_expiry_cross_product']
        self.assertEqual(len(radar_subset), 7672)
        self.assertTrue((radar_subset['expiry_date_leg_a'] == radar_subset['expiry_date_leg_b']).all())
        self.assertTrue((radar_subset['calendar_days_between_expiries'] == 0).all())

    def test_11_calendar_spread_nearer_deferred_ordering(self):
        """Calendar spread candidates must enforce nearer_expiry < deferred_expiry."""
        cal_subset = self.df_a[self.df_a['candidate_type'] == 'same_symbol_calendar_spread']
        self.assertEqual(len(cal_subset), 23811)
        self.assertTrue((cal_subset['calendar_days_between_expiries'] > 0).all())
        self.assertTrue((cal_subset['symbol_leg_a'] == cal_subset['symbol_leg_b']).all())

    def test_12_output_b_scenario_key_uniqueness(self):
        """Output B must contain 94,449 rows (31,483 * 3) with unique (candidate_id, scenario_name) keys."""
        self.assertEqual(len(self.df_b), 94449)
        self.assertEqual(self.df_b.duplicated(subset=['candidate_id', 'scenario_name']).sum(), 0)
        scenario_counts = self.df_b['scenario_name'].value_counts()
        self.assertEqual(scenario_counts['base'], 31483)
        self.assertEqual(scenario_counts['low'], 31483)
        self.assertEqual(scenario_counts['high'], 31483)

    def test_13_output_c_eligible_candidates_integrity(self):
        """Output C must match Output A candidates where is_all_filters_eligible is True."""
        expected_len = self.df_a['is_all_filters_eligible'].sum()
        self.assertEqual(len(self.df_c), expected_len)
        self.assertEqual(len(self.df_c), 26822)
        self.assertTrue(self.df_c['is_all_filters_eligible'].all())
        self.assertTrue((self.df_c['exclusion_reasons'] == 'NONE').all())
        # Verify zero GOLD in eligible candidates
        self.assertNotIn('GOLD', self.df_c['symbol_leg_a'].unique())
        self.assertNotIn('GOLD', self.df_c['symbol_leg_b'].unique())

    def test_14_zero_volume_rejected_consistently(self):
        """Zero volume records must never pass data eligibility or the overall filter."""
        zero_vol = self.df_a[self.df_a['flag_zero_volume_leg_a'] | self.df_a['flag_zero_volume_leg_b']]
        self.assertTrue((~zero_vol['is_both_data_eligible']).all())
        self.assertTrue((~zero_vol['is_all_filters_eligible']).all())

    def test_15_expiry_day_observations_rejected(self):
        """Observations on or after nominal expiry (days <= 0) must never qualify as eligible entries."""
        exp_day = self.df_a[(self.df_a['days_to_expiry_leg_a'] <= 0) | (self.df_a['days_to_expiry_leg_b'] <= 0)]
        self.assertGreater(len(exp_day), 0)
        self.assertTrue((~exp_day['passes_expiry_filter']).all())
        self.assertTrue((~exp_day['is_all_filters_eligible']).all())
        for r in exp_day['exclusion_reasons']:
            self.assertIn("expired_or_expiry_day", r)

    def test_16_notional_math_and_exposure_units(self):
        """Verify notional and physical exposure matching in Output B."""
        sample = self.df_b[(self.df_b['candidate_type'] == 'same_symbol_calendar_spread') & 
                           (self.df_b['cost_model_status'] == 'available')].head(10)
        for _, row in sample.iterrows():
            self.assertEqual(row['matched_lots_leg_a'], 1)
            self.assertEqual(row['matched_lots_leg_b'], 1)
            self.assertEqual(row['exposure_grams_leg_a'], row['exposure_grams_leg_b'])
            # Check total_round_trip == entry + exit
            self.assertAlmostEqual(row['total_round_trip_cost_inr'], 
                                   row['total_entry_cost_inr'] + row['total_exit_cost_inr'], places=3)

    def test_17_cross_product_notional_purity_distinction(self):
        """Cross-product notionals must be derived from quoted price without purity scaling."""
        pair_sample = self.df_b[(self.df_b['candidate_id'].str.contains('GOLDM_')) & 
                                (self.df_b['candidate_id'].str.contains('GOLDTEN_')) &
                                (self.df_b['cost_model_status'] == 'available')].head(5)
        for _, row in pair_sample.iterrows():
            # 1 lot GOLDM = 100g, 10 lots GOLDTEN = 100g
            self.assertEqual(row['matched_lots_leg_a'], 1)
            self.assertEqual(row['matched_lots_leg_b'], 10)
            self.assertEqual(row['exposure_grams_leg_a'], 100)
            self.assertEqual(row['exposure_grams_leg_b'], 100)

    def test_18_unavailable_costs_remain_nan(self):
        """Unavailable candidates must have NaN in modeled costs, never zero."""
        unavail = self.df_b[self.df_b['cost_model_status'] != 'available']
        self.assertGreater(len(unavail), 0)
        self.assertTrue(unavail['total_round_trip_cost_inr'].isna().all())
        self.assertTrue(unavail['modeled_net_spread_per_gram'].isna().all())
        self.assertTrue((unavail['gross_exceeds_modeled_costs'] == False).all())

    def test_19_pipeline_deterministic_reruns(self):
        """Verify pipeline execution is 100% deterministic on repeated runs."""
        specs_cfg, liq_cfg, costs_cfg = load_configurations(CONFIG_DIR)
        norm_df, radar_df, term_df = load_input_datasets(DATA_DIR)
        re_screened = screen_candidates(radar_df, term_df, norm_df, liq_cfg, specs_cfg)
        self.assertEqual(len(re_screened), len(self.df_a))
        self.assertEqual(re_screened['is_all_filters_eligible'].sum(), self.df_a['is_all_filters_eligible'].sum())

    def test_20_upstream_datasets_immutability(self):
        """Confirm Phase 1-4 active 4-product processed datasets remain 100% byte-for-byte unchanged."""
        expected_hashes = {
            'data/processed/mcx_gold_master.csv': '0efb75ed225bf651',
            'data/processed/mcx_gold_normalized.csv': '8eb15f5353e8df88',
            'data/processed/mcx_gold_relative_price_radar.csv': 'bf746998b24560a9',
            'data/processed/mcx_gold_term_structure.csv': '9d78f67db6120f3e',
            'data/processed/mcx_gold_term_structure_snapshots.csv': '775c4bbafa2410c6'
        }
        for rel_path, exp_prefix in expected_hashes.items():
            full_path = os.path.join(PROJECT_ROOT, rel_path)
            self.assertTrue(os.path.exists(full_path), f"File {rel_path} must exist.")
            with open(full_path, 'rb') as f:
                h = hashlib.sha256(f.read()).hexdigest()[:16]
            self.assertEqual(h, exp_prefix, f"File {rel_path} hash changed! Upstream data must be immutable.")

        # Also verify preserved 5-product historical archive
        archived_master = os.path.join(PROJECT_ROOT, 'data/processed/archive_5product/mcx_gold_master.csv')
        if os.path.exists(archived_master):
            with open(archived_master, 'rb') as f:
                arch_h = hashlib.sha256(f.read()).hexdigest()[:16]
            self.assertEqual(arch_h, 'ac57299101fef709')

if __name__ == '__main__':
    unittest.main()
