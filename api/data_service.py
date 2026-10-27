"""
Gold Contract Radar — FastAPI Data Service
Loads and caches canonical datasets and runs authoritative calculations for the API.
"""

import os
import json
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")

from src.dashboard.data_loader import (
    load_contract_specs,
    load_backtest_config,
    load_transaction_costs_config,
    load_liquidity_filters_config,
    load_normalized_data,
    load_relative_price_radar,
    load_term_structure,
    load_term_structure_snapshots,
    load_liquidity_filtered_candidates,
    load_transaction_cost_scenarios,
    load_eligible_candidates,
    load_backtest_trades,
    load_walk_forward_metrics,
    load_backtest_summary,
    load_execution_diagnostics,
    get_dataset_inventory
)
from src.dashboard.metrics import (
    filter_trades,
    calculate_trade_kpis,
    build_cumulative_equity_series,
    calculate_market_kpis,
    verify_reconciliation
)


class DataService:
    _instance = None

    def __init__(self):
        self._cache: Dict[str, Any] = {}

    @classmethod
    def get_instance(cls) -> "DataService":
        if cls._instance is None:
            cls._instance = DataService()
        return cls._instance

    def get_contract_specs(self) -> Dict[str, Any]:
        if "contract_specs" not in self._cache:
            self._cache["contract_specs"] = load_contract_specs()
        return self._cache["contract_specs"]

    def get_backtest_config(self) -> Dict[str, Any]:
        if "backtest_config" not in self._cache:
            self._cache["backtest_config"] = load_backtest_config()
        return self._cache["backtest_config"]

    def get_transaction_costs_config(self) -> Dict[str, Any]:
        if "transaction_costs_config" not in self._cache:
            self._cache["transaction_costs_config"] = load_transaction_costs_config()
        return self._cache["transaction_costs_config"]

    def get_liquidity_filters_config(self) -> Dict[str, Any]:
        if "liquidity_filters_config" not in self._cache:
            self._cache["liquidity_filters_config"] = load_liquidity_filters_config()
        return self._cache["liquidity_filters_config"]

    def get_normalized_data(self) -> pd.DataFrame:
        if "normalized_data" not in self._cache:
            self._cache["normalized_data"] = load_normalized_data()
        return self._cache["normalized_data"]

    def get_relative_price_radar(self) -> pd.DataFrame:
        if "relative_price_radar" not in self._cache:
            self._cache["relative_price_radar"] = load_relative_price_radar()
        return self._cache["relative_price_radar"]

    def get_term_structure(self) -> pd.DataFrame:
        if "term_structure" not in self._cache:
            self._cache["term_structure"] = load_term_structure()
        return self._cache["term_structure"]

    def get_term_structure_snapshots(self) -> pd.DataFrame:
        if "term_structure_snapshots" not in self._cache:
            self._cache["term_structure_snapshots"] = load_term_structure_snapshots()
        return self._cache["term_structure_snapshots"]

    def get_liquidity_filtered_candidates(self) -> pd.DataFrame:
        if "liquidity_filtered_candidates" not in self._cache:
            self._cache["liquidity_filtered_candidates"] = load_liquidity_filtered_candidates()
        return self._cache["liquidity_filtered_candidates"]

    def get_transaction_cost_scenarios(self) -> pd.DataFrame:
        if "transaction_cost_scenarios" not in self._cache:
            self._cache["transaction_cost_scenarios"] = load_transaction_cost_scenarios()
        return self._cache["transaction_cost_scenarios"]

    def get_eligible_candidates(self) -> pd.DataFrame:
        if "eligible_candidates" not in self._cache:
            self._cache["eligible_candidates"] = load_eligible_candidates()
        return self._cache["eligible_candidates"]

    def get_backtest_trades(self) -> pd.DataFrame:
        if "backtest_trades" not in self._cache:
            self._cache["backtest_trades"] = load_backtest_trades()
        return self._cache["backtest_trades"]

    def get_walk_forward_metrics(self) -> pd.DataFrame:
        if "walk_forward_metrics" not in self._cache:
            self._cache["walk_forward_metrics"] = load_walk_forward_metrics()
        return self._cache["walk_forward_metrics"]

    def get_backtest_summary(self) -> pd.DataFrame:
        if "backtest_summary" not in self._cache:
            self._cache["backtest_summary"] = load_backtest_summary()
        return self._cache["backtest_summary"]

    def get_execution_diagnostics(self) -> pd.DataFrame:
        if "execution_diagnostics" not in self._cache:
            self._cache["execution_diagnostics"] = load_execution_diagnostics()
        return self._cache["execution_diagnostics"]

    def get_dataset_inventory(self) -> List[Dict[str, Any]]:
        return get_dataset_inventory()


data_service = DataService.get_instance()
