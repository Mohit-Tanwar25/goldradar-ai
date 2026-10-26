# Gold Contract Radar — Phase 7 Dashboard Data & Schema Audit Report

**Project:** Gold Contract Radar — MCX Commodity Derivatives Intelligence  
**Phase:** Phase 7 — Interactive Streamlit Dashboard  
**Date:** 2026-10-25  
**Auditor / Agent:** Antigravity IDE  

---

## 1. Executive Summary

This data audit establishes the empirical source-of-truth baseline for the **Gold Contract Radar** interactive Streamlit dashboard. All 12 production datasets spanning Phases 1 through 6 were audited for existence, file integrity, row counts, column schemas, temporal boundaries, missing value distributions, and functional mapping to the 8 dashboard pages.

### Audit Summary:
- **Files Found:** 12 / 12 (100% complete; zero missing production datasets).
- **Configuration Files Found:** 4 / 4 (`contract_specs.json`, `liquidity_filters.json`, `transaction_costs.json`, `backtest_config.json`).
- **Data Coverage:** 2024-01-01 to 2026-10-22 (701 distinct trading sessions, 5 MCX gold products).
- **Backtesting Scope:** 10 chronological rolling walk-forward folds (July 2024 to October 2026 test windows).
- **Execution Reality:** 31,437 simulated trade attempts in Output A (across `base`, `low`, and `high` cost scenarios), yielding 267 completed trades and 1 unresolved boundary exit. Exactly 0 shared-contract overlaps remain across all 114 distinct traded contracts.

---

## 2. Dataset Inventory & Schema Audit

| # | Dataset Filename | Phase | Rows | Cols | File Size | Primary Key / Granularity | Date Coverage |
| :-: | :--- | :-: | :-: | :-: | :-: | :--- | :---: |
| 1 | `mcx_gold_master.csv` | Phase 2 | 16,195 | 28 | 4.83 MB | `(contract_key, date)` | 2024-01-01 to 2026-10-22 |
| 2 | `mcx_gold_normalized.csv` | Phase 3 | 16,195 | 42 | 7.13 MB | `(contract_key, date)` | 2024-01-01 to 2026-10-22 |
| 3 | `mcx_gold_relative_price_radar.csv` | Phase 4 | 9,059 | 20 | 3.72 MB | `(pair_key, date, expiry)` | 2024-01-01 to 2026-10-22 |
| 4 | `mcx_gold_term_structure.csv` | Phase 4 | 34,086 | 19 | 12.84 MB | `(symbol, date, expiry_near, expiry_far)` | 2024-01-01 to 2026-10-22 |
| 5 | `mcx_gold_term_structure_snapshots.csv` | Phase 4 | 16,195 | 10 | 2.65 MB | `(contract_key, date)` | 2024-01-01 to 2026-10-22 |
| 6 | `mcx_gold_liquidity_filtered_candidates.csv` | Phase 5 | 43,145 | 48 | 28.71 MB | `(candidate_id)` | 2024-01-01 to 2026-10-22 |
| 7 | `mcx_gold_transaction_cost_scenarios.csv` | Phase 5 | 129,435 | 31 | 35.85 MB | `(candidate_id, scenario_name)` | 2024-01-01 to 2026-10-22 |
| 8 | `mcx_gold_eligible_candidates.csv` | Phase 5 | 29,726 | 48 | 19.03 MB | `(candidate_id)` | 2024-01-01 to 2026-10-22 |
| 9 | `mcx_gold_backtest_trades.csv` | Phase 6 | 31,437 | 48 | 16.83 MB | `(trade_id)` | 2024-07-01 to 2026-10-20 |
| 10 | `mcx_gold_walk_forward_metrics.csv` | Phase 6 | 54 | 23 | 13.6 KB | `(fold_id, strategy_name, cost_scenario)` | FOLD_01 to FOLD_10 |
| 11 | `mcx_gold_backtest_summary.csv` | Phase 6 | 6 | 21 | 3.05 KB | `(strategy_name, cost_scenario)` | Full Period Summary |
| 12 | `mcx_gold_execution_diagnostics.csv` | Phase 6 | 24 | 4 | 2.80 KB | `(metric_name)` | Overall Simulation |

---

## 3. Schema & Null-Value Analysis

### 3.1 Market Data (`mcx_gold_normalized.csv`)
- **Key Columns:** `date`, `symbol`, `expiry_date`, `contract_key`, `open`, `high`, `low`, `close`, `volume_lots`, `open_interest_lots`, `open_per_gram`, `close_per_gram`, `open_fine_per_gram`, `close_fine_per_gram`, `is_executable_traded`, `flag_zero_volume`, `flag_missing_ohlc`.
- **Null Value Inspection:** 0 nulls across price, date, and contract fields.
- **Data Freshness / Coverage:** Covers all 5 MCX products:
  - `GOLD` (1 kg / 1,000 g): 1,602 rows
  - `GOLDM` (100 g): 3,091 rows
  - `GOLDTEN` (10 g): 1,387 rows (listed starting 2025-03-31)
  - `GOLDGUINEA` (8 g): 4,891 rows
  - `GOLDPETAL` (1 g): 5,224 rows

### 3.2 Relative Price Radar (`mcx_gold_relative_price_radar.csv`)
- **Key Columns:** `candidate_id`, `candidate_type`, `date`, `symbol_leg_a`, `symbol_leg_b`, `expiry_date`, `quoted_price_spread_per_gram`, `quoted_relative_spread_pct`, `fine_price_spread_per_gram`, `fine_relative_spread_pct`, `is_both_executable_traded`.
- **Null Value Inspection:** Nulls in `fine_annualized_spread_pct` (all 9,059 rows) because this dataset represents cross-product same-expiry spreads where annualization across expiries is mathematically non-applicable.

### 3.3 Term Structure (`mcx_gold_term_structure.csv` & `snapshots.csv`)
- **Key Columns:** `candidate_id`, `date`, `symbol`, `expiry_date_near`, `expiry_date_far`, `calendar_days_between_expiries`, `quoted_price_spread_per_gram`, `fine_annualized_spread_pct`, `term_structure_slope`, `slope_regime`.
- **Null Value Inspection:** 0 nulls in annualized spread or slope fields.

### 3.4 Liquidity & Costs (`mcx_gold_liquidity_filtered_candidates.csv`, `cost_scenarios.csv`, `eligible_candidates.csv`)
- **Key Columns:** `candidate_id`, `passes_liquidity_filter`, `is_all_filters_eligible`, `exclusion_reasons`, `scenario_name`, `total_round_trip_cost_inr`, `modeled_round_trip_cost_per_gram`, `gross_spread_per_gram`, `modeled_net_spread_per_gram`.
- **Null Value Inspection:** For candidates marked `quantity_matching_status == "UNAVAILABLE"`, costs and notional fields are `NaN` by design (23,865 rows out of 129,435 in cost scenarios).

### 3.5 Backtest Ledger & Metrics (`mcx_gold_backtest_trades.csv`, `walk_forward_metrics.csv`, `summary.csv`, `diagnostics.csv`)
- **Key Columns:** `trade_id`, `candidate_id`, `strategy_name`, `cost_scenario`, `fold_id`, `signal_date`, `entry_date`, `exit_date`, `symbol_leg_a`, `symbol_leg_b`, `matched_exposure_grams`, `signal_direction`, `gross_pnl_inr`, `total_modeled_cost_inr`, `net_pnl_inr`, `trade_completion_status`, `rejection_or_exclusion_reason`, `exit_trigger_reason`, `holding_period_days`.
- **Null Value Inspection:** In `mcx_gold_backtest_trades.csv`, P&L, entry price, and exit price columns are `NaN` for rejected attempts (30,633 rows) and unresolved trades (3 rows across scenarios). Completed trades have 0 nulls in P&L or cost fields.
- **Accounting Rule:** All performance calculations (win rate, profit factor, drawdown, mean P&L) **must strictly filter on `trade_completion_status == "COMPLETED"` and a single `cost_scenario`** to avoid double counting.

---

## 4. Mapping Datasets to Dashboard Pages

| Dashboard Page | Primary Data Source | Secondary Data Source | Filter Capabilities |
| :--- | :--- | :--- | :--- |
| **Page A: Executive Overview** | `mcx_gold_backtest_summary.csv`, `mcx_gold_execution_diagnostics.csv` | `mcx_gold_normalized.csv`, `mcx_gold_eligible_candidates.csv` | Cost scenario selector (`base`, `low`, `high`) |
| **Page B: Market Explorer** | `mcx_gold_normalized.csv` | `config/contract_specs.json` | Date range, Symbol, Expiry, Traded status |
| **Page C: Relative Price Radar** | `mcx_gold_relative_price_radar.csv` | `config/contract_specs.json` | Date range, Pair selection, Executability |
| **Page D: Term Structure** | `mcx_gold_term_structure_snapshots.csv`, `mcx_gold_term_structure.csv` | `config/contract_specs.json` | Snapshot date, Symbol, Expiry pairs |
| **Page E: Liquidity & Costs** | `mcx_gold_liquidity_filtered_candidates.csv`, `mcx_gold_transaction_cost_scenarios.csv` | `mcx_gold_eligible_candidates.csv` | Candidate type, Scenario name, Eligibility status |
| **Page F: Backtest Performance** | `mcx_gold_backtest_trades.csv`, `mcx_gold_walk_forward_metrics.csv`, `mcx_gold_backtest_summary.csv` | `config/backtest_config.json` | Cost scenario, Strategy, Fold ID, Date range |
| **Page G: Execution Diagnostics** | `mcx_gold_execution_diagnostics.csv`, `mcx_gold_backtest_trades.csv` | `reports/phase6_shared_exposure_audit.md` | Rejection category, Exit trigger reason |
| **Page H: Data & Methodology** | `config/contract_specs.json`, `config/backtest_config.json`, `config/transaction_costs.json` | Project documentation and audit logs | Reference viewer & documentation links |

---

## 5. Unavailable Metrics & Explicit Data Limitations

The following metrics **cannot be calculated or displayed** from the historical bhavcopy dataset, and will be accompanied by explicit user-facing disclaimers:
1. **Intraday Mark-to-Market (MTM) Unrealized Drawdown:** MCX bhavcopy files record only end-of-session settlement prices. Unrealized tick-by-tick or intraday variations inside the 10-session holding window are unobserved. All drawdowns are computed strictly on realized cumulative P&L at trade exit dates.
2. **Return on Investment (ROI) & Sharpe / Sortino Ratios:** Initial margin, maintenance margin, and member capital requirements are broker-specific and unrecorded in exchange bhavcopy data. Calculating percentage ROI without observed margin denominators is ungrounded.
3. **Continuous Price Series across Expiries:** Physical futures contracts expire periodically. Connecting different expiries into a continuous synthetic line creates artificial rollover gaps; the Market Explorer displays distinct contract expiries.
4. **Order Book Depth & Slippage:** Daily OHLCV data lacks order book bids and asks. Round-trip costs reflect statutory fees and discount broker models, not market impact or spread crossing.

---

## 6. Audit Conclusion

All 12 required datasets are verified, structurally complete, and mathematically reconciled. Phase 7 dashboard construction can proceed with 100% confidence in the underlying data foundation.
