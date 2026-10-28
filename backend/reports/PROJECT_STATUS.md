# Gold Contract Radar — MCX Commodity Derivatives Intelligence
## Project Status Tracking

**Last Updated:** October 25, 2026  
**Implementation Agent:** Antigravity IDE  
**Planning & Review Assistant:** ChatGPT  
**Target Event:** Hack in Hills '26  

---

## 1. Current Phase
**Four-Contract Universe Transition** — **AUDITED, FULLY REGENERATED & APPROVED**
- Restricts active analysis universe strictly to 4 retail/mini contracts: `GOLDM`, `GOLDTEN`, `GOLDGUINEA`, `GOLDPETAL`.
- Completely excludes standard 1kg wholesale contract (`GOLD`) from all active calculations.
- Original 5-product baseline preserved byte-for-byte in `data/processed/archive_5product/`.
- All 104 repository unit and regression tests pass in under 36 seconds.

---

## 2. Phase-by-Phase Roadmap & Status

| Phase | Description | Status | Sign-off / Deliverables |
| :---: | :--- | :---: | :--- |
| **Phase 1** | Raw Data Quality & Coverage Audit | **APPROVED** | `reports/data_audit.md`, `reports/file_inventory.csv`, `reports/duplicate_candidates.csv` |
| **Phase 2** | Master Dataset Preparation & Standardization | **APPROVED** | `src/prepare_master_dataset.py`, `data/processed/mcx_gold_master.csv`, `reports/master_dataset_validation.md` |
| **Phase 3** | Contract Specifications & Price Normalization | **APPROVED** | `config/contract_specs.json`, `src/normalize_prices.py`, `data/processed/mcx_gold_normalized.csv`, `tests/test_normalization.py`, `reports/contract_specifications.md`, `reports/normalization_validation.md` |
| **Phase 4** | Relative Price Radar & Term Structure Modeling | **APPROVED** | `src/build_relative_price_radar.py`, `data/processed/mcx_gold_relative_price_radar.csv`, `data/processed/mcx_gold_term_structure.csv`, `data/processed/mcx_gold_term_structure_snapshots.csv`, `tests/test_relative_price_radar.py`, `reports/relative_price_radar_validation.md` |
| **Phase 5** | Liquidity & Transaction Cost Filters | **APPROVED** | `config/liquidity_filters.json`, `config/transaction_costs.json`, `src/apply_liquidity_cost_filters.py`, `data/processed/mcx_gold_liquidity_filtered_candidates.csv`, `data/processed/mcx_gold_transaction_cost_scenarios.csv`, `data/processed/mcx_gold_eligible_candidates.csv`, `tests/test_liquidity_cost_filters.py`, `reports/liquidity_cost_filter_validation.md`, `reports/phase5_final_audit.md` |
| **Phase 6** | Walk-Forward Backtesting & Execution Feasibility Analysis | **APPROVED** | `config/backtest_config.json`, `src/run_walk_forward_backtest.py`, `data/processed/mcx_gold_backtest_trades.csv`, `data/processed/mcx_gold_walk_forward_metrics.csv`, `data/processed/mcx_gold_backtest_summary.csv`, `data/processed/mcx_gold_execution_diagnostics.csv`, `tests/test_walk_forward_backtest.py`, `reports/walk_forward_backtest_validation.md`, `reports/phase6_final_audit.md`, `reports/phase6_shared_exposure_audit.md` |
| **Phase 7** | Interactive Radar Dashboard & Visualizations | **APPROVED** | `app.py`, `src/dashboard/`, `tests/test_dashboard.py`, `reports/phase7_dashboard_data_audit.md`, `reports/phase7_dashboard_validation.md` |
| **4-Contract Transition** | Authoritative 4-Contract Universe Restriction & Pipeline Audit | **APPROVED** | `reports/four_contract_universe_audit.md`, `data/processed/archive_5product/`, `config/contract_specs.json`, full pipeline regeneration |
| **Phase 8** | Final Project Packaging & Hackathon Submission | *Not Started* | Complete system packaging & deployment |

---

## 3. Work Completed in Phase 6 & Final Logic Audit
1. **Configurable Walk-Forward & Execution Architecture:**
   - Authored `config/backtest_config.json` defining strict next-session Open execution, two-leg execution policy, tender window avoidance ($DTE \le 5$), 10-session maximum holding period, contract-level non-overlapping position enforcement, portfolio exposure controls, minimum 20 training observations rule, and 10 rolling walk-forward folds (6m train / 3m test / 3m step).
2. **Backtesting Pipeline (`src/run_walk_forward_backtest.py`):**
   - Ingested 29,726 trade-eligible candidates from Phase 5 and normalized market data from Phase 3.
   - Evaluated Strategy A (Cross-Product Convergence) and Strategy B (Calendar Spread Roll) independently.
   - Enforced zero look-ahead bias: date $t$ Close signal -> date $t+1$ Open fill. Both legs checked for positive traded volume and complete OHLC.
   - Resolved shared-contract overlap defect: contract-level occupancy tracking and deterministic prioritization eliminated all 95 contract collision instances, 2,728 opposing position instances, and 2,462 multi-strategy conflicts, ensuring strictly 0 contract collisions across all 114 traded contracts.
   - Enforced fold-boundary Open execution: unexecutable boundary exits are marked `UNRESOLVED` with `NaN` P&L (1 trade) rather than assuming closing marks.
   - Quarantined newly listed products (`GOLDTEN`) in Folds 1–4 with `rejected_insufficient_training_history` (61 rejections) until $\ge 20$ training samples accumulated.
   - Dynamically recalculated turnover, brokerage, CTT (0.01% on sell), Stamp Duty (0.002% on buy), Exchange fee, SEBI charge, and GST (18%) from simulated fill prices across `base`, `low`, and `high` scenarios.
3. **Generated Production Datasets:**
   - **Output A (`mcx_gold_backtest_trades.csv`):** 31,437 simulated trade attempts and fills with complete execution metadata.
   - **Output B (`mcx_gold_walk_forward_metrics.csv`):** 54 walk-forward fold metric records across 10 folds, 2 strategies, and 3 scenarios.
   - **Output C (`mcx_gold_backtest_summary.csv`):** 6 comprehensive strategy summary records.
   - **Output D (`mcx_gold_execution_diagnostics.csv`):** 24 execution diagnostic tracking metrics.
4. **Automated Unit Testing (`tests/test_walk_forward_backtest.py`):**
   - Built 38 comprehensive unit and regression tests covering chronological sorting, train/test window isolation, two-leg execution enforcement, integer-lot exposure matching, dynamic cost recalculation, tender exits, fold-boundary censoring, primary key uniqueness, upstream dataset immutability, insufficient training history quarantine, contract non-overlap enforcement, opposing positions, gross/net limits, deterministic prioritization, and session-by-session occupancy.
   - Executed full test suite across all phases: **84/84 tests passed in 111.75s**.
5. **Auditing & Validation Reporting:**
   - Authored `reports/walk_forward_backtest_validation.md` detailing data audits, fold ranges, empirical performance, execution diagnostics, and quantitative limitations.
   - Authored `reports/phase6_final_audit.md` and `reports/phase6_shared_exposure_audit.md` presenting the complete audit scorecard, independently recalculated representative trades across all symbols (including GOLDTEN), and full SHA-256 immutability proof.

---

## 4. Phase 6 Validation & Audit Scorecard

| Validation Metric | Target Value | Observed Value | Result |
| :--- | :---: | :---: | :---: |
| **Audit 1: P&L & Contract Units** | Reconciled within $< 10^{-4}$ | Gross - Costs == Net reconciled for 100% of trades | **PASS** |
| **Audit 2: Shared-Contract & Overlap** | 0 overlapping contracts across portfolio | 0 overlaps across all 114 distinct contracts | **PASS** |
| **Audit 3: Equity Curve & Drawdown** | Realized-P&L exit-date series | Fully verified and disclaimers applied | **PASS** |
| **Audit 4: Fold-Boundary Exit Execution** | Strict Open fills / UNRESOLVED | 1 trade marked UNRESOLVED with NaN P&L | **PASS** |
| **Audit 5: Training Data Sufficiency** | Min 20 observations rule | GOLDTEN quarantined in Folds 1-4; 61 rejections | **PASS** |
| **Audit 6: Regression & Immutability** | 100% test pass & byte-identical | 84/84 tests pass; Phase 1-5 SHA-256 byte-identical | **PASS** |
| **Output A Trade Ledger Rows** | > 30,000 rows | 31,437 rows | **PASS** |
| **Output A Trade ID Uniqueness** | 0 duplicates | 0 duplicates (100% unique) | **PASS** |
| **Output B Walk-Forward Metric Rows** | 10 folds $\times$ strategies $\times$ scenarios | 54 rows | **PASS** |
| **Output B Primary Key Uniqueness** | `(fold_id, strategy_name, cost_scenario)` | 0 duplicates (100% unique) | **PASS** |
| **Output C Strategy Summary Rows** | 2 strategies $\times$ 3 scenarios | 6 rows | **PASS** |
| **Output D Execution Diagnostic Rows** | Comprehensive tracking | 24 rows | **PASS** |
| **Phase 6 Automated Tests** | 38 / 38 passed | 38 / 38 passed (100% in 10.8s) | **PASS** |
| **Total Automated Test Suite** | 104 / 104 passed | 104 / 104 passed (100% in 35.47s) | **PASS** |
| **Upstream Datasets Immutability** | Byte-identical | Byte-identical (Verified via SHA-256 for active & archive) | **PASS** |

---

## 5. Execution Commands

### To Regenerate Data Pipeline (4-Contract Universe):
```powershell
python src/prepare_master_dataset.py
python src/normalize_prices.py
python src/build_relative_price_radar.py
python src/apply_liquidity_cost_filters.py
python src/run_walk_forward_backtest.py
```

### To Launch the Streamlit Dashboard:
```powershell
streamlit run app.py
```

### To Run Full Repository Test Suite (104 Tests across all phases):
```powershell
python -m unittest discover tests
```

---

## 6. Next Proposed Phase
**Phase 8: Final Project Packaging & Hackathon Submission** — *NOT STARTED*
- Final containerization, submission artifacts, documentation packaging, and deployment prep.
- Strict scope boundary: Phase 8 must NOT be started until explicit approval is granted.

---
*Four-contract universe transition complete, audited, and approved. 104/104 tests passing. Awaiting instructions before proceeding to Phase 8.*
