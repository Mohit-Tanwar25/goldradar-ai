# Gold Contract Radar — MCX Commodity Derivatives Intelligence
## Phase 7: Interactive Streamlit Dashboard Validation Report

**Date of Audit & Validation:** October 25, 2026  
**Implementation Agent:** Antigravity IDE  
**Planning & Review Assistant:** ChatGPT  
**Target Event:** Hack in Hills '26  
**Active Phase:** Phase 7 — Interactive Streamlit Dashboard  
**Status:** **FULLY IMPLEMENTED, TESTED, AUDITED & VALIDATED**

---

## 1. Executive Summary

This report documents the design, architecture, validation, financial accounting, and test coverage for **Phase 7: Interactive Streamlit Dashboard** of the **Gold Contract Radar** project.

The dashboard provides an institutional-grade, interactive financial research interface powered entirely by the project's actual, verified datasets from Phases 1 through 6. It strictly visualizes historical market data, cross-product relative pricing, term structure curves, liquidity filters, walk-forward backtest results, and portfolio execution diagnostics without fabricating data, synthetic metrics, or unrealistic execution claims.

### Phase 7 Scorecard & Integrity Verification:
- **Application Architecture:** Modular design (`app.py`, `src/dashboard/data_loader.py`, `src/dashboard/metrics.py`, `src/dashboard/charts.py`, `src/dashboard/components.py`, `src/dashboard/views.py`).
- **Dashboard Pages:** 8 comprehensive pages implemented (Pages A through H).
- **Production Datasets Displayed:** 12 verified datasets (8 canonical Phase 1–5 datasets + 4 Phase 6 production backtest outputs).
- **Scenario Isolation:** Strict single-scenario trade filtering (`base`, `low`, `high`) prevents artificial cross-scenario trade multiplication.
- **Financial Accounting Reconciliation:** Every completed trade satisfies $|\text{Gross P\&L} - \text{Total Modeled Costs} - \text{Net Realized P\&L}| < 10^{-4}$.
- **Upstream Dataset Immutability:** All 8 canonical Phase 1–5 datasets match their canonical SHA-256 integrity hashes 100% byte-for-byte.
- **Phase 6 Trading Logic & Outputs:** 100% untouched and preserved.
- **Dashboard Test Suite (`tests/test_dashboard.py`):** 18/18 unit tests passed in 8.24s.
- **Full Repository Test Suite (`python -m unittest discover tests`):** 102/102 unit tests passed in 234.03s (Phases 3 through 7).
- **Local Application Launch:** Successfully launched locally on `http://localhost:8501` returning HTTP 200 OK.

---

## 2. Implemented Pages and UI Architecture

The application adopts a dark institutional theme inspired by Bloomberg Terminal and FactSet, featuring clean typography (Inter and JetBrains Mono), responsive CSS layouts, interactive Plotly charts, and prominent quantitative research disclaimers.

```
                              ┌──────────────────────────────────────────────┐
                              │     app.py (Streamlit Navigation Hub)        │
                              └──────────────────────┬───────────────────────┘
                                                     │
         ┌───────────────────┬───────────────────────┼───────────────────────┬───────────────────┐
         ▼                   ▼                       ▼                       ▼                   ▼
   ┌───────────┐       ┌───────────┐           ┌───────────┐           ┌───────────┐       ┌───────────┐
   │  Page A   │       │  Page B   │           │  Page C   │           │  Page D   │       │  Page E   │
   │ Executive │       │  Market   │           │ Relative  │           │   Term    │       │Liquidity &│
   │ Overview  │       │ Explorer  │           │Price Radar│           │ Structure │       │   Costs   │
   └───────────┘       └───────────┘           └───────────┘           └───────────┘       └───────────┘
         │                   │                       │                       │                   │
         └───────────────────┴───────────────────────┼───────────────────────┴───────────────────┘
                                                     │
                                 ┌───────────────────┴───────────────────┐
                                 ▼                                       ▼
                           ┌───────────┐                           ┌───────────┐
                           │  Page F   │                           │  Page G   │
                           │ Backtest  │                           │ Execution │
                           │Performance│                           │Diagnostics│
                           └─────┬─────┘                           └─────┬─────┘
                                 │                                       │
                                 └───────────────────┬───────────────────┘
                                                     ▼
                                               ┌───────────┐
                                               │  Page H   │
                                               │  Data &   │
                                               │Methodology│
                                               └───────────┘
```

### Detailed Page Breakdown:

| Page | Title & Focus | Key Components & Visualizations | Primary Source Datasets |
| :--- | :--- | :--- | :--- |
| **Page A** | **Executive Overview** | Macro research KPIs, prompt price trajectory by contract, strategy comparison summary, upstream data validation status, research disclaimer. | `mcx_gold_master.csv`, `mcx_gold_backtest_summary.csv`, `mcx_gold_backtest_trades.csv` |
| **Page B** | **Market Explorer** | Contract discontinuity alert, contract specifications reference, interactive OHLC candlestick with volume, volume and open interest trends, daily returns distribution, filterable session table. | `mcx_gold_master.csv`, `mcx_gold_normalized.csv`, `contract_specs.json` |
| **Page C** | **Relative Price Radar** | Fine price normalization formula note, cross-product annualized spread time series, spread distribution histogram, sortable candidate inspector. | `mcx_gold_relative_price_radar.csv` |
| **Page D** | **Term Structure** | Forward curves across all historical sessions, annualized contango/backwardation roll yield time series, forward curve snapshot inspector table. | `mcx_gold_term_structure_snapshots.csv`, `mcx_gold_term_structure.csv` |
| **Page E** | **Liquidity & Transaction Costs** | Candidate screening funnel (43,145 screened $\rightarrow$ 29,726 eligible), rejection reason breakdown, statutory cost comparison across scenarios (`base`, `low`, `high`), candidate cost inspector. | `mcx_gold_liquidity_filtered_candidates.csv`, `mcx_gold_transaction_cost_scenarios.csv`, `mcx_gold_eligible_candidates.csv` |
| **Page F** | **Backtest Performance** | Cost scenario selector (`base`, `low`, `high`), Strategy A vs B summary KPIs, cumulative realized P&L equity curve with realized drawdown, trade-level P&L distribution, walk-forward fold metrics, filterable trade ledger. | `mcx_gold_backtest_summary.csv`, `mcx_gold_backtest_trades.csv`, `mcx_gold_walk_forward_metrics.csv` |
| **Page G** | **Execution Diagnostics** | Accepted vs rejected execution attempts, rejection reasons distribution, shared-contract overlap validation (0 verified across 114 contracts), exit trigger distribution (`target_converged`, `max_holding_period`, `boundary_open_exit`, `unresolved_boundary_exit`). | `mcx_gold_execution_diagnostics.csv`, `mcx_gold_backtest_trades.csv`, `phase6_shared_exposure_audit.md` |
| **Page H** | **Data & Methodology** | 5 MCX gold contract specification table, fine-gold normalization equations, statutory fee schedules, walk-forward backtesting rules, portfolio exposure controls, data limitations, institutional disclaimer. | `contract_specs.json`, `backtest_config.json`, project documentation |

---

## 3. Data Transformations & Accounting Integrity

### 3.1 Strict Scenario Isolation
The trade ledger `mcx_gold_backtest_trades.csv` contains 31,437 rows because each triggered signal is evaluated across three alternative transaction cost scenarios (`base`, `low`, `high`):
- `base`: 10,479 rows (267 completed trades)
- `low`: 10,479 rows (267 completed trades)
- `high`: 10,479 rows (267 completed trades)

**Enforced Rule:** The dashboard filters by a single user-selected scenario before computing any performance metric or rendering any chart. Cross-scenario summing is strictly prevented.

### 3.2 Completed Trades Filtering
Execution attempts are classified into distinct statuses:
- `COMPLETED`: Both entry and exit orders executed successfully (267 trades in `base` scenario).
- `REJECTED`: Signal rejected by portfolio exposure limits, insufficient training history, or tender window (10,211 attempts in `base` scenario).
- `UNRESOLVED`: Trade entered but fold boundary prevented executable exit (1 trade in `base` scenario).

**Enforced Rule:** All performance metrics (gross P&L, net P&L, win rate, profit factor, mean P&L per trade, holding period) are calculated exclusively from `COMPLETED` trades. Rejected attempts and unresolved trades are strictly segregated and analyzed in Page G (Execution Diagnostics).

### 3.3 Financial Accounting Reconciliation Check
For every completed trade, the dashboard programmatically validates:
$$|\text{gross\_pnl} - \text{total\_modeled\_costs} - \text{net\_pnl}| < 10^{-4}$$
If any trade violates this identity, the dashboard flags a reconciliation error. In the audited datasets, **100% of completed trades reconcile perfectly**.

### 3.4 Chronological Cumulative Realized Equity
To avoid lookahead bias and artificial equity curves:
1. Only completed trades are included.
2. Trades are sorted strictly chronologically by `exit_date` ASC (the date when cash P&L is realized).
3. Running cumulative net P&L is computed: $E_k = \sum_{i=1}^k \text{net\_pnl}_i$.
4. Running peak equity is tracked: $M_k = \max_{j \le k} E_j$.
5. Realized drawdown is calculated: $DD_k = E_k - M_k \le 0$.
6. A clear disclaimer explains that this represents **realized closed-trade equity**, not continuous mark-to-market portfolio equity.

---

## 4. Upstream Dataset SHA-256 Immutability Check

All 8 canonical datasets produced in Phases 1 through 5 were audited using SHA-256 hashing to confirm byte-for-byte immutability during Phase 7 implementation:

| Dataset File Path | Originating Phase | Row Count | File Size (Bytes) | Canonical SHA-256 Hash | Integrity Result |
| :--- | :---: | :---: | :---: | :--- | :---: |
| `data/processed/mcx_gold_master.csv` | Phase 2 | 16,195 | 4,828,791 | `ac57299101fef7092ae956dc35fa9e9f15d9e8a195a340621ddd245f3f510088` | **IMMUTABLE** |
| `data/processed/mcx_gold_normalized.csv` | Phase 3 | 16,195 | 7,127,915 | `26c57ce9ad54f271875e816ce865ef0121adadbe517136289494a8bae48c2020` | **IMMUTABLE** |
| `data/processed/mcx_gold_relative_price_radar.csv` | Phase 4 | 9,059 | 3,724,677 | `38f13aeddb2454f928ae5a043319b525c01d198283be0e050f292d8efa2386c4` | **IMMUTABLE** |
| `data/processed/mcx_gold_term_structure.csv` | Phase 4 | 34,086 | 12,837,972 | `d81102755b7f1b85766ea699a99dc1c6f998eaf50b034c2924d1bf133fac6201` | **IMMUTABLE** |
| `data/processed/mcx_gold_term_structure_snapshots.csv` | Phase 4 | 16,195 | 2,647,180 | `f064bf4e75ff6791b1839f4b8152cabf51d99478ecf310b6696a0aefb3120037` | **IMMUTABLE** |
| `data/processed/mcx_gold_liquidity_filtered_candidates.csv` | Phase 5 | 43,145 | 28,713,069 | `b2385ab75c9f0a2d6a65f6da580725b8979f6834e433042df5f9c51d4efac135` | **IMMUTABLE** |
| `data/processed/mcx_gold_transaction_cost_scenarios.csv` | Phase 5 | 129,435 | 35,850,688 | `1f58b74593db05e5a521f289870ac0368a06f14963e0676ed20d90f4e5c9158a` | **IMMUTABLE** |
| `data/processed/mcx_gold_eligible_candidates.csv` | Phase 5 | 29,726 | 19,027,212 | `774b872b9aae45d06129c970f70f852e2efdb0f1ba6358381af19cb34b6fa22f` | **IMMUTABLE** |

**Confirmation:** Zero modifications, overwrites, or regenerations occurred on any canonical Phase 1–5 dataset.

---

## 5. Automated Test Suite Results

### 5.1 Dashboard Test Suite (`tests/test_dashboard.py`)
A dedicated automated test suite was developed to test all 18 mandatory verification items specified for Phase 7:
```bash
python -m unittest tests/test_dashboard.py
```
**Output:**
```text
Ran 18 tests in 8.238s

OK
```

#### Test Case Breakdown:
1. `test_01_load_valid_source_files`: Loads and validates real and synthetic production CSVs.
2. `test_02_missing_optional_files`: Gracefully handles missing files without crashing.
3. `test_03_missing_required_columns`: Detects schema defects and raises actionable errors.
4. `test_04_empty_datasets`: Safely processes 0-row datasets.
5. `test_05_invalid_dates_and_missing_numerics`: Safely coerces corrupted dates and numbers.
6. `test_06_date_range_filtering`: Verifies inclusive boundary filtering on timestamps.
7. `test_07_symbol_and_expiry_filtering`: Confirms exact matching on symbol and expiry.
8. `test_08_strategy_filtering`: Verifies clean isolation between Strategy A and Strategy B.
9. `test_09_cost_scenario_selection`: Confirms strict scenario isolation (`base`, `low`, `high`).
10. `test_10_completed_trade_filtering`: Extracts only `COMPLETED` trade records.
11. `test_11_rejected_attempts_excluded_from_completed`: Confirms 0 rejected records enter performance KPIs.
12. `test_12_no_double_counting_scenario_specific_trades`: Verifies row count isolation per scenario.
13. `test_13_gross_minus_costs_equals_net_pnl_tolerance`: Validates $|\text{Gross} - \text{Costs} - \text{Net}| < 10^{-4}$.
14. `test_14_chronological_cumulative_realized_pnl`: Confirms exit-date sorting and running equity math.
15. `test_15_empty_filter_results`: Verifies safe fallback on empty filter results.
16. `test_16_duplicate_identifier_detection`: Detects duplicate `trade_id` records in inputs.
17. `test_17_rejection_reason_aggregation`: Confirms exact rejection count distributions.
18. `test_18_transformations_preserve_input_immutability`: Confirms original DataFrames are never mutated.

### 5.2 Full Repository Regression Test Suite
```bash
python -m unittest discover tests
```
**Output:**
```text
Ran 102 tests in 234.032s

OK
```
**Test Breakdown Across Phases:**
- `tests/test_normalization.py` (Phase 3): 8 tests passing.
- `tests/test_relative_price_radar.py` (Phase 4): 18 tests passing.
- `tests/test_liquidity_cost_filters.py` (Phase 5): 20 tests passing.
- `tests/test_walk_forward_backtest.py` (Phase 6): 38 tests passing.
- `tests/test_dashboard.py` (Phase 7): 18 tests passing.
- **Total Passing Tests:** **102 / 102 (100% success)**. Zero regressions introduced.

---

## 6. Local Launch Instructions

### Prerequisites
Ensure Python 3.10+ is installed with the required dependencies in `requirements.txt`:
```bash
pip install -r requirements.txt
```

### Launching the Dashboard
Execute the standard Streamlit launch command from the repository root:
```powershell
streamlit run app.py
```

### Operational Behavior:
- **Port:** Default is `http://localhost:8501`.
- **Headless Mode (Optional):** `streamlit run app.py --server.headless true --server.port 8501`
- **Caching:** Production datasets are loaded once using `@st.cache_data`. Use the sidebar **"Clear Cache & Reload"** button to force a cold reload.

---

## 7. Known Data & Quantitative Limitations

1. **Daily Settlement vs Intraday Order Matching:**
   Simulated executions execute at Date $t+1$ Open. Daily bhavcopy data cannot replicate intraday order book dynamics, quote queue positions, or execution slippage during opening volatility.
2. **Unobserved Bid-Ask Spread:**
   While statutory taxes (CTT, Stamp Duty, GST, Exchange charges) and broker commissions are modeled across 3 scenarios, empirical market-maker bid-ask spreads (₹10–₹25/g on smaller contracts like `GOLDGUINEA` and `GOLDPETAL`) are unrecorded in bhavcopy files and would further erode net returns.
3. **Absence of Intraday Mark-to-Market Margin Requirements:**
   Bhavcopy data does not report broker-specific initial or maintenance margin requirements. Consequently, cash drawdown cannot be translated into a validated return on invested capital (ROIC) or Sharpe ratio without ungrounded assumptions.
4. **Physical Delivery Basis Risk:**
   Cross-product contracts represent distinct deliverable commodities (1 kg 995 bars, 100g 995 bars, 8g 999 coins, 1g 999 coins). Observed spreads reflect structural physical delivery basis risk and are not risk-free arbitrage.
5. **No Investment Advice Disclaimer:**
   This application is a historical research and simulation tool. Its outputs are not investment advice or guaranteed trading returns. Historical results may not predict future performance.

---

## 8. Conclusion and Sign-Off

Phase 7 implementation is complete, thoroughly audited, verified by automated tests, and validated locally.

- **Phase 7 Status:** **APPROVED / COMPLETE**
- **Phase 8 Packaging & Deployment:** **STRICTLY NOT STARTED**
