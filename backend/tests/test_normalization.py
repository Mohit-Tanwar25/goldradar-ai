"""
Automated Unit Tests for Price Normalization Formulas and Edge Cases
Tests quotation divisors, fine gold factor adjustments, missing value preservation,
and contract specifications.
"""

import unittest
import os
import json
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "contract_specs.json")
NORMALIZED_CSV = os.path.join(PROJECT_ROOT, "data", "processed", "mcx_gold_normalized.csv")
MASTER_CSV = os.path.join(PROJECT_ROOT, "data", "processed", "mcx_gold_master.csv")

class TestNormalizationFormulas(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            cls.config = json.load(f)
        cls.contracts = cls.config["contracts"]
        cls.df_norm = pd.read_csv(NORMALIZED_CSV)
        cls.df_master = pd.read_csv(MASTER_CSV)

    def test_quotation_divisors(self):
        """Verify verified quotation divisors in configuration."""
        self.assertEqual(self.contracts["GOLD"]["quotation_divisor_grams"], 10.0)
        self.assertEqual(self.contracts["GOLDM"]["quotation_divisor_grams"], 10.0)
        self.assertEqual(self.contracts["GOLDTEN"]["quotation_divisor_grams"], 10.0)
        self.assertEqual(self.contracts["GOLDGUINEA"]["quotation_divisor_grams"], 8.0)
        self.assertEqual(self.contracts["GOLDPETAL"]["quotation_divisor_grams"], 1.0)

    def test_fine_gold_factors(self):
        """Verify purity fineness and fine gold equivalent factors (including GOLDGUINEA 999)."""
        # 995 fineness standard bullion bar contracts
        self.assertEqual(self.contracts["GOLD"]["fine_gold_factor"], 0.995)
        self.assertEqual(self.contracts["GOLD"]["underlying_purity_fineness"], 995)
        self.assertEqual(self.contracts["GOLDM"]["fine_gold_factor"], 0.995)
        self.assertEqual(self.contracts["GOLDM"]["underlying_purity_fineness"], 995)
        
        # 999 fineness coin / small denomination contracts
        self.assertEqual(self.contracts["GOLDTEN"]["fine_gold_factor"], 0.999)
        self.assertEqual(self.contracts["GOLDTEN"]["underlying_purity_fineness"], 999)
        self.assertEqual(self.contracts["GOLDGUINEA"]["fine_gold_factor"], 0.999)
        self.assertEqual(self.contracts["GOLDGUINEA"]["underlying_purity_fineness"], 999)
        self.assertEqual(self.contracts["GOLDPETAL"]["fine_gold_factor"], 0.999)
        self.assertEqual(self.contracts["GOLDPETAL"]["underlying_purity_fineness"], 999)

    def test_row_count_and_columns_preserved(self):
        """Verify total rows match master dataset exactly."""
        self.assertEqual(len(self.df_norm), 11968)
        self.assertEqual(len(self.df_norm), len(self.df_master))
        # Ensure original master columns exist unchanged
        for col in self.df_master.columns:
            self.assertIn(col, self.df_norm.columns)
            pd.testing.assert_series_equal(self.df_master[col], self.df_norm[col], check_names=False)

    def test_price_per_gram_math(self):
        """Verify close_per_gram == close / quotation_divisor_grams."""
        expected_close_per_gram = self.df_norm['close'] / self.df_norm['quotation_divisor_grams']
        np.testing.assert_allclose(self.df_norm['close_per_gram'], expected_close_per_gram, rtol=1e-6)

    def test_fine_gold_price_per_gram_math(self):
        """Verify close_fine_per_gram == close_per_gram / fine_gold_factor."""
        expected_fine = self.df_norm['close_per_gram'] / self.df_norm['fine_gold_factor']
        np.testing.assert_allclose(self.df_norm['close_fine_per_gram'], expected_fine, rtol=1e-6)

    def test_missing_ohlc_preservation(self):
        """Verify missing open/high/low remain exactly missing and are not zeroed."""
        zero_vol = self.df_norm[self.df_norm['flag_zero_volume']]
        self.assertEqual(len(zero_vol), 146)
        self.assertEqual(zero_vol['open_per_gram'].isna().sum(), 146)
        self.assertEqual(zero_vol['high_per_gram'].isna().sum(), 146)
        self.assertEqual(zero_vol['low_per_gram'].isna().sum(), 146)
        self.assertEqual(zero_vol['open_fine_per_gram'].isna().sum(), 146)
        self.assertEqual(zero_vol['high_fine_per_gram'].isna().sum(), 146)
        self.assertEqual(zero_vol['low_fine_per_gram'].isna().sum(), 146)
        # Ensure close_per_gram is available even on zero volume days
        self.assertEqual(zero_vol['close_per_gram'].isna().sum(), 0)

    def test_no_duplicate_keys(self):
        """Verify no duplicate (date, symbol, expiry_date) keys exist."""
        self.assertEqual(self.df_norm.duplicated(subset=['date', 'symbol', 'expiry_date']).sum(), 0)

    def test_goldten_start_date(self):
        """Verify GOLDTEN start date is preserved without pre-launch records."""
        goldten_df = self.df_norm[self.df_norm['symbol'] == 'GOLDTEN']
        self.assertEqual(goldten_df['date'].min(), '2025-03-31')
        self.assertEqual(len(goldten_df), 2048)

    def test_active_universe_four_products_only(self):
        """Verify active normalized dataset contains exactly the four retained products."""
        active_syms = set(self.df_norm['symbol'].unique())
        expected_syms = {'GOLDM', 'GOLDTEN', 'GOLDGUINEA', 'GOLDPETAL'}
        self.assertEqual(active_syms, expected_syms)
        self.assertNotIn('GOLD', active_syms)

if __name__ == '__main__':
    unittest.main()
