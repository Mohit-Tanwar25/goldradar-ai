"""
Gold Contract Radar — FastAPI Endpoint Test Suite
Validates all endpoints, responses, schemas, and parameter filters.
"""

import unittest
from fastapi.testclient import TestClient
from api.main import app


class TestFastAPIEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_health_check(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("GOLDM", data["active_universe"])

    def test_02_overview_endpoint(self):
        res = self.client.get("/api/overview")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("metadata", data)
        self.assertIn("kpis", data)
        self.assertIn("active_contracts", data)
        self.assertEqual(len(data["active_contracts"]), 4)
        self.assertGreater(data["kpis"]["normalized_gold_price"], 1000)
        self.assertIn("price_history", data)
        self.assertGreater(len(data["price_history"]), 0)

    def test_03_compare_contracts_endpoint(self):
        res = self.client.get("/api/contracts/compare?symbol_a=GOLDM&symbol_b=GOLDTEN")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["symbol_a"], "GOLDM")
        self.assertEqual(data["symbol_b"], "GOLDTEN")
        self.assertGreater(data["statistics"]["total_observations"], 0)
        self.assertIn("timeseries", data)

    def test_04_compare_contracts_identical_symbols_rejection(self):
        res = self.client.get("/api/contracts/compare?symbol_a=GOLDM&symbol_b=GOLDM")
        self.assertEqual(res.status_code, 400)

    def test_05_futures_curve_endpoint(self):
        res = self.client.get("/api/futures/curve")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("market_structure", data)
        self.assertIn("curve_points", data)
        self.assertGreater(len(data["curve_points"]), 0)

    def test_06_opportunities_endpoint(self):
        res = self.client.get("/api/opportunities?cost_scenario=base")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("funnel", data)
        self.assertIn("opportunities", data)
        self.assertEqual(data["scenario"], "base")
        self.assertGreater(len(data["opportunities"]), 0)

    def test_07_backtest_performance_endpoint(self):
        res = self.client.get("/api/backtest?cost_scenario=base")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("kpis", data)
        self.assertIn("equity_curve", data)
        self.assertIn("strategies", data)
        self.assertIn("trade_ledger", data)
        self.assertTrue(data["kpis"]["pnl_reconciled"])

    def test_08_methodology_endpoint(self):
        res = self.client.get("/api/methodology")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("active_universe", data)
        self.assertIn("normalization_formula", data)
        self.assertIn("datasets", data)
        self.assertEqual(len(data["datasets"]), 12)


if __name__ == "__main__":
    unittest.main()
