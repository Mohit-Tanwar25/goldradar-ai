# Four-Contract Universe Transition & Data Integrity Audit Report

**Project:** Gold Contract Radar — MCX Commodity Derivatives Intelligence  
**Target Event:** Hack in Hills ’26  
**Audit Date:** October 25, 2026  
**Status:** COMPLETE & VERIFIED — 104/104 Tests Passing  

---

## Executive Summary

The **Gold Contract Radar** research framework has been successfully updated to restrict the active MCX contract universe to **exactly four retail/mini products**, completely excluding the standard 1 kg wholesale contract (`GOLD`) from all active upstream calculations, pipelines, candidate screens, walk-forward backtests, and dashboard interfaces.

The active four-product universe is:
1. **`GOLDM`** (MCX Gold Mini — 100g, 995 fineness)
2. **`GOLDTEN`** (MCX Gold Ten — 10g, 999 fineness)
3. **`GOLDGUINEA`** (MCX Gold Guinea — 8g, 999 fineness)
4. **`GOLDPETAL`** (MCX Gold Petal — 1g, 999 fineness)

### Scope & Preservation Highlights
- **100% Non-Destructive Archival:** All 12 original five-product canonical datasets have been preserved byte-for-byte in [`data/processed/archive_5product/`](file:///d:/Akshitakumawat/hackkk/data/processed/archive_5product) with SHA-256 hashes verified against baseline records.
- **Upstream Filtering, Not Surface Clipping:** Rather than merely filtering `GOLD` at the UI layer, the pipeline was rebuilt from the ingestion phase down through backtest execution.
- **Mathematical Integrity:** Reconciled entry and exit physical notionals, contract multipliers, purity adjustments, next-session Open execution assumptions, and portfolio-level contract exposure controls across 10 walk-forward folds.
- **Full Test Suite Success:** All 104 unit, regression, and data integrity tests in `tests/` pass cleanly in under 36 seconds.

---

## 1. Rationale for Excluding the Standard 1 kg Contract (`GOLD`)

The standard MCX `GOLD` contract has a trading lot unit of **1,000 grams (1 kg)** with a notional value exceeding **₹8.5 to ₹9.0 crore per lot**. In contrast, the remaining contracts represent smaller physical denominations tailored to retail, jeweller, and non-institutional trading:
- `GOLDM`: 100 grams (~₹85–90 Lakh notional)
- `GOLDTEN`: 10 grams (~₹8.5–9 Lakh notional)
- `GOLDGUINEA`: 8 grams (~₹6.8–7.2 Lakh notional)
- `GOLDPETAL`: 1 gram (~₹8,500–9,000 notional)

### Core Motivations for Exclusion:
1. **Exposure Sizing Disparity:** Pairing 1 kg `GOLD` against 1g `GOLDPETAL` required an integer lot ratio of 1:1,000. In cross-product spreads, this created severe execution friction and slippage risk on illiquid legs.
2. **Nominal Drawdown Distortion:** In calendar spreads (Strategy B), the 1,000g trading unit of `GOLD` overwhelmed all other contract types in nominal INR drawdown (-₹3.29 Lakh in the 5-product baseline was overwhelmingly dominated by 1kg calendar positions).
3. **Target Scope Alignment:** For the Hack in Hills '26 derivatives research scope, focusing on mini and micro contracts (`GOLDM`, `GOLDTEN`, `GOLDGUINEA`, `GOLDPETAL`) provides an economically realistic and executable universe without institutional 1kg balance-sheet requirements.
4. **Preservation of Methodology:** The contract specifications, purity factors, and historical bhavcopy records of `GOLD` remain intact in [`config/contract_specs.json`](file:///d:/Akshitakumawat/hackkk/config/contract_specs.json) and [`data/raw/`](file:///d:/Akshitakumawat/hackkk/data/raw) for full scientific reproducibility and cross-reference.

---

## 2. Authoritative Active Contract Universe Configuration

The single authoritative definition for the active universe is maintained in [`config/contract_specs.json`](file:///d:/Akshitakumawat/hackkk/config/contract_specs.json):

```json
{
  "active_contracts": [
    "GOLDM",
    "GOLDTEN",
    "GOLDGUINEA",
    "GOLDPETAL"
  ],
  "excluded_contracts": [
    "GOLD"
  ],
  "contracts": {
    "GOLD": {
      "trading_unit_grams": 1000,
      "quotation_unit": "10 grams",
      "purity_factor": 0.995,
      "is_active": false,
      "exclusion_note": "Standard 1kg contract excluded from active trading universe; retained for historical reference."
    },
    "GOLDM": {
      "trading_unit_grams": 100,
      "quotation_unit": "10 grams",
      "purity_factor": 0.995,
      "is_active": true
    },
    "GOLDTEN": {
      "trading_unit_grams": 10,
      "quotation_unit": "10 grams",
      "purity_factor": 0.999,
      "is_active": true
    },
    "GOLDGUINEA": {
      "trading_unit_grams": 8,
      "quotation_unit": "8 grams",
      "purity_factor": 0.999,
      "is_active": true
    },
    "GOLDPETAL": {
      "trading_unit_grams": 1,
      "quotation_unit": "1 gram",
      "purity_factor": 0.999,
      "is_active": true
    }
  }
}
```

### Protection Against Loose Substring Matching:
All pipeline scripts and filtering logic enforce exact equality (`symbol in active_contracts` or `clean_symbol in active_contracts`). Removing `"GOLD"` does **not** inadvertently filter out `"GOLDM"`, `"GOLDTEN"`, `"GOLDGUINEA"`, or `"GOLDPETAL"`. Whitespace trimming and uppercase normalization are strictly applied before checking membership.

---

## 3. Pipeline Regeneration & Row Count Comparison

All datasets in `data/processed/` were regenerated in strict dependency order:
1. `prepare_master_dataset.py` $\rightarrow$ `mcx_gold_master.csv`
2. `normalize_prices.py` $\rightarrow$ `mcx_gold_normalized.csv`
3. `build_relative_price_radar.py` $\rightarrow$ `mcx_gold_relative_price_radar.csv`, `mcx_gold_term_structure.csv`, `mcx_gold_term_structure_snapshots.csv`
4. `apply_liquidity_cost_filters.py` $\rightarrow$ `mcx_gold_liquidity_filtered_candidates.csv`, `mcx_gold_transaction_cost_scenarios.csv`, `mcx_gold_eligible_candidates.csv`
5. `run_walk_forward_backtest.py` $\rightarrow$ `mcx_gold_backtest_trades.csv`, `mcx_gold_walk_forward_metrics.csv`, `mcx_gold_backtest_summary.csv`, `mcx_gold_execution_diagnostics.csv`

### Detailed Dataset Comparison

| Dataset Filename | 5-Product Baseline (Archived) | 4-Product Active Universe | Delta (Rows) | Operational Meaning of Delta |
| :--- | :---: | :---: | :---: | :--- |
| `mcx_gold_master.csv` | 16,195 | **11,968** | -4,227 | Exact removal of 4,227 `GOLD` bhavcopy records |
| `mcx_gold_normalized.csv` | 16,195 | **11,968** | -4,227 | 100% 1-to-1 parity with cleaned master dataset |
| Zero-Volume Records | 1,985 | **146** | -1,839 | 1kg `GOLD` had 1,839 zero-volume deferred expiry rows |
| `mcx_gold_relative_price_radar.csv` | 9,059 | **7,672** | -1,387 | All pairs involving `GOLD` eliminated (e.g. GOLD-GOLDM) |
| `mcx_gold_term_structure.csv` | 34,086 | **23,811** | -10,275 | Removal of 10,275 `GOLD` calendar spread pairs |
| `mcx_gold_term_structure_snapshots.csv` | 16,195 | **11,968** | -4,227 | Exact removal of `GOLD` curve snapshot records |
| `mcx_gold_liquidity_filtered_candidates.csv` | 43,145 | **31,483** | -11,662 | Screened candidate pool ($7,672 + 23,811 = 31,483$) |
| `mcx_gold_transaction_cost_scenarios.csv` | 129,435 | **94,449** | -34,986 | Exactly $31,483 \times 3$ scenarios (Low, Base, High) |
| `mcx_gold_eligible_candidates.csv` | 29,726 | **26,822** | -2,904 | Fully eligible candidate entries after all filters |
| `mcx_gold_backtest_trades.csv` | 31,437 | **29,004** | -2,433 | $9,668 \text{ attempts} \times 3 \text{ scenarios} = 29,004$ rows |
| Strategy A Completed Trades (Base) | 87 | **82** | -5 | 5 completed trades involving `GOLD` legs eliminated |
| Strategy B Completed Trades (Base) | 180 | **162** | -18 | 18 completed `GOLD` calendar spreads eliminated |
| Total Completed Trades (Base) | 267 | **244** | -23 | 82 Strategy A + 162 Strategy B completed trades |

---

## 4. Backtest Performance Metrics: 5-Product vs 4-Product

Below is an honest, mathematically verified comparison across both strategies and the combined portfolio under the **Base Cost Scenario**.

### Strategy A: Relative Price Cross-Product Spreads (Base Scenario)

| Metric | 5-Product Baseline (Archived) | 4-Product Active Universe | Directional Impact & Notes |
| :--- | :---: | :---: | :--- |
| Trade Attempts | 2,238 | **1,957** | -281 attempts (pairs involving `GOLD` excluded) |
| Completed Trades | 87 | **82** | -5 completed trades |
| Win Rate (%) | 49.43% | **50.00%** | 41 wins, 41 losses |
| Gross Realized P&L | +₹59,850.00 | **+₹70,612.00** | Retained pairs captured higher relative basis deviation |
| Modeled Costs | ₹19,955.40 | **₹13,643.17** | Lower turnover statutory charges on mini/micro lots |
| **Net Realized P&L** | **+₹39,894.60** | **+₹56,968.83** | +₹17,074.23 net improvement |
| Mean Net P&L / Trade | +₹458.56 | **+₹694.74** | +51.5% improvement in per-trade edge |
| Profit Factor | 1.37 | **1.61** | Gross profit / gross loss improved |
| Realized Max Drawdown | ₹10,488.00 | **₹10,488.00** | Identical peak-to-trough path on remaining pairs |
| Mean Holding Days | 8.87 days | **8.76 days** | Exit timing remains deterministic |

### Strategy B: Calendar Roll Yield Spreads (Base Scenario)

| Metric | 5-Product Baseline (Archived) | 4-Product Active Universe | Directional Impact & Notes |
| :--- | :---: | :---: | :--- |
| Trade Attempts | 8,241 | **7,711** | -530 attempts |
| Completed Trades | 180 | **162** | -18 completed trades |
| Win Rate (%) | 34.44% | **35.80%** | 58 wins, 104 losses |
| Gross Realized P&L | -₹36,420.00 | **-₹10,800.00** | Curtailed outsized gross roll losses |
| Modeled Costs | ₹292,978.50 | **₹38,872.98** | Massive friction reduction: 1kg lot turnover eliminated |
| **Net Realized P&L** | **-₹329,398.50** | **-₹49,672.98** | **₹279,725.52 loss reduction** |
| Mean Net P&L / Trade | -₹1,829.99 | **-₹306.62** | Per-trade drag reduced by 83.2% |
| Profit Factor | 0.35 | **0.69** | Remains sub-1.0; calendar roll drag persists |
| Realized Max Drawdown | ₹371,446.50 | **₹91,018.84** | **₹280,427.66 drawdown compression** |
| Mean Holding Days | 8.23 days | **8.22 days** | Identical holding distribution |

### Combined Portfolio (Base Scenario)

| Metric | 5-Product Baseline (Archived) | 4-Product Active Universe | Directional Impact & Notes |
| :--- | :---: | :---: | :--- |
| Total Trade Attempts | 10,479 | **9,668** | -811 attempts |
| Completed Trades | 267 | **244** | -23 trades |
| Portfolio Win Rate (%) | 39.33% | **40.57%** | 99 wins, 145 losses |
| Gross Realized P&L | +₹23,430.00 | **+₹59,812.00** | +₹36,382.00 |
| Total Modeled Costs | ₹312,933.90 | **₹52,516.15** | ₹260,417.75 savings in modeled friction |
| **Portfolio Net P&L** | **-₹289,503.90** | **+₹7,295.85** | **Shift from deeply negative to marginal positive** |
| Mean Net P&L / Trade | -₹1,084.28 | **+₹29.90** | Marginal net edge after statutory costs |
| Portfolio Profit Factor | 0.54 | **1.02** | Strategy A gains offset Strategy B drag |
| Realized Max Drawdown | ₹371,446.50 | **₹186,188.75** | Peak-to-trough exposure reduced by 50.0% |
| P&L Reconciliation Diff | $< 10^{-11}$ | **$7.28 \times 10^{-12}$** | **Exact mathematical reconciliation** |
| Shared-Contract Collisions | 0 | **0** | Strict contract exclusivity maintained |

> [!WARNING]
> **Research Reality & No-Profitability Disclaimer:**
> Although the four-product active universe displays an overall net positive result (+₹7,295.85) under the Base Cost Scenario, Strategy B (Calendar Spreads) remains unprofitable on a standalone basis (Win Rate: 35.80%, Net P&L: -₹49,672.98, Profit Factor: 0.69). The net positive portfolio result is driven entirely by Strategy A (Cross-Product Spreads) combined with the elimination of the 1 kg wholesale contract's disproportionate transaction costs. Historical backtest results do not guarantee future profitability or real-world fill execution.

---

## 5. SHA-256 Hash Verification & Reproducibility Matrix

### A. Archived Five-Product Historical Baseline (Verified Unaltered)
Location: [`data/processed/archive_5product/`](file:///d:/Akshitakumawat/hackkk/data/processed/archive_5product)

| Dataset | Canonical SHA-256 (First 16 chars) | Full SHA-256 Hash | Integrity Status |
| :--- | :---: | :---: | :---: |
| `mcx_gold_master.csv` | `ac57299101fef709` | `ac57299101fef709c95977baec7b99c855a15998f5a544b677a285d033a388f8` | **VERIFIED UNCHANGED** |
| `mcx_gold_normalized.csv` | `26c57ce9ad54f271` | `26c57ce9ad54f271d44111fa6ca01f016d9a04a11b22e1b1d1e406322b7d2f97` | **VERIFIED UNCHANGED** |
| `mcx_gold_relative_price_radar.csv` | `38f13aeddb2454f9` | `38f13aeddb2454f981030e46b0e8c89c4d9cbba99be0be24fc0b0744923e512d` | **VERIFIED UNCHANGED** |
| `mcx_gold_term_structure.csv` | `d81102755b7f1b85` | `d81102755b7f1b855e378bbca2871081da22e176eb2bb43f054ba9f4937fc5a0` | **VERIFIED UNCHANGED** |
| `mcx_gold_term_structure_snapshots.csv` | `f064bf4e75ff6791` | `f064bf4e75ff6791937ff221efc91c3d18386b6a22c54ca4febe73d74542566c` | **VERIFIED UNCHANGED** |
| `mcx_gold_liquidity_filtered_candidates.csv`| `b2385ab75c9f0a2d` | `b2385ab75c9f0a2d04a796e62111d4d7e98bf62d596ee24300e84b8d6d84fbb8` | **VERIFIED UNCHANGED** |
| `mcx_gold_transaction_cost_scenarios.csv` | `1f58b74593db05e5` | `1f58b74593db05e5f5f4b5f928e4e9ae8cfc3b01a61c37d40dd560e98031d24c` | **VERIFIED UNCHANGED** |
| `mcx_gold_eligible_candidates.csv` | `774b872b9aae45d0` | `774b872b9aae45d0234cf78b02220d5885c4bfefcf5c2a11b65cb33a6950ee0b` | **VERIFIED UNCHANGED** |
| `mcx_gold_backtest_trades.csv` | `ee27bfb6040285a1` | `ee27bfb6040285a1a1f0a0bbad21bfa3c6dfd94d3ae22e1262d2949ffdc64817` | **VERIFIED UNCHANGED** |
| `mcx_gold_walk_forward_metrics.csv` | `69ef13e1d79a25f9` | `69ef13e1d79a25f95f4c4a5c531d279cf441e8c07c6f05a5a1f6a1e38933b93f` | **VERIFIED UNCHANGED** |
| `mcx_gold_backtest_summary.csv` | `5b2b0c75b3f10e3b` | `5b2b0c75b3f10e3b97ba119c48858e763133ae3e29c0a3791a2bb469ce38290e` | **VERIFIED UNCHANGED** |
| `mcx_gold_execution_diagnostics.csv` | `a6a4efdb304c6fb7` | `a6a4efdb304c6fb78ce89656b23b32e09ca1e32716386da678f14896d859b00e` | **VERIFIED UNCHANGED** |

### B. Active Four-Product Production Outputs (Current Production)
Location: [`data/processed/`](file:///d:/Akshitakumawat/hackkk/data/processed)

| Dataset | Rows | Columns | Canonical SHA-256 (First 16 chars) | Full SHA-256 Hash |
| :--- | :---: | :---: | :---: | :---: |
| `mcx_gold_master.csv` | 11,968 | 29 | `0efb75ed225bf651` | `0efb75ed225bf6515c77d66015a92e629651515acd54e8bb9611b71c751a55e4` |
| `mcx_gold_normalized.csv` | 11,968 | 42 | `8eb15f5353e8df88` | `8eb15f5353e8df883758d28b46f0d63cb68066ebd95d93303dd6cbb4d3b5ffb2` |
| `mcx_gold_relative_price_radar.csv` | 7,672 | 20 | `bf746998b24560a9` | `bf746998b24560a9e926d18fdf12cabbda70ce68dada0c98afd8be88463770f7` |
| `mcx_gold_term_structure.csv` | 23,811 | 19 | `9d78f67db6120f3e` | `9d78f67db6120f3e62ae53d7f0209d32cc0f561c6eb7bce5c09c14b67281bc45` |
| `mcx_gold_term_structure_snapshots.csv` | 11,968 | 10 | `775c4bbafa2410c6` | `775c4bbafa2410c6f7dd5659f74a27fa32e1dfd534b26e3c1fc87a467f759c9f` |
| `mcx_gold_liquidity_filtered_candidates.csv`| 31,483 | 48 | `39432f3bbcd45898` | `39432f3bbcd45898e8627459955e945aa04d21867db6d9a6846677e3089a0210` |
| `mcx_gold_transaction_cost_scenarios.csv` | 94,449 | 31 | `7c852bf0ea361495` | `7c852bf0ea361495fea9d3ca26625a3899944699d0cf47760b6c238a945803e1` |
| `mcx_gold_eligible_candidates.csv` | 26,822 | 48 | `0e8299fb816c8c85` | `0e8299fb816c8c851d99564c62a53a1ab19fedd85191926d71860c5248f767bc` |
| `mcx_gold_backtest_trades.csv` | 29,004 | 48 | `4743ea47d188909f` | `4743ea47d188909f3bce5d87c5691f4a5adc80dfbd940c46c1c44e0e8485b59a` |
| `mcx_gold_walk_forward_metrics.csv` | 54 | 23 | `f5c37580a80e0196` | `f5c37580a80e0196a42423906a50bc4bdd0453c2b938d334e8f5847c5a22ed9c` |
| `mcx_gold_backtest_summary.csv` | 6 | 21 | `55fba227ce03c8cf` | `55fba227ce03c8cf127c7e74a88429253a747cb7bc82c4272c880ac74aed46ac` |
| `mcx_gold_execution_diagnostics.csv` | 24 | 4 | `cd4f7df6f0a4ed6c` | `cd4f7df6f0a4ed6c014fdd71bea1cb6b69fb8993b28e9255af1e1bd94f43fa35` |

---

## 6. Bugs Investigated & Code Enhancements Implemented

During the transition audit, the following items were identified and addressed:

1. **Dashboard Data Loader Schema Aliasing:**
   - **Root Cause:** `src/dashboard/data_loader.py` functions `load_relative_price_radar()` and `load_term_structure()` checked for candidate-level column names (`candidate_id`, `symbol_leg_a`, `symbol_leg_b`) rather than Phase 4 canonical output names (`symbol_a`, `symbol_b`, `quoted_price_difference_per_gram`).
   - **Fix:** Updated `required_cols` in `data_loader.py` to match Phase 4 output specifications and automatically generated alias columns (`symbol_leg_a`, `symbol_leg_b`, `quoted_price_spread_per_gram`, `fine_price_spread_per_gram`, `is_both_executable_traded`) for smooth backwards-compatibility.
2. **Dynamic Active Universe Injection:**
   - **Root Cause:** Hardcoded row counts and lists in test assertions and pipeline assertions.
   - **Fix:** Sourced `active_contracts` directly from `config/contract_specs.json` across `src/prepare_master_dataset.py`, `src/normalize_prices.py`, `src/build_relative_price_radar.py`, and `src/dashboard/views.py`.
3. **Execution Diagnostics Consistency:**
   - **Observation:** `mcx_gold_execution_diagnostics.csv` confirms **zero shared-contract collisions**, **zero multi-strategy conflicts**, and **zero opposing positions** across all 10 folds in the four-product universe.

---

## 7. Test Suite Verification & Execution Results

All 104 automated tests across five test suites pass with zero failures and zero errors:

```bash
python -m unittest discover tests
```

### Breakdown of Test Results:
1. [`tests/test_normalization.py`](file:///d:/Akshitakumawat/hackkk/tests/test_normalization.py): **9/9 PASS**
   - Verified 11,968 normalized rows, 146 zero-volume rows, exact quotation divisors, purity adjustments, and absence of `GOLD`.
2. [`tests/test_relative_price_radar.py`](file:///d:/Akshitakumawat/hackkk/tests/test_relative_price_radar.py): **18/18 PASS**
   - Verified 7,672 radar rows, 23,811 term structure rows, 11,968 snapshot rows, chronological expiry ordering, and exclusion of `GOLD`.
3. [`tests/test_liquidity_cost_filters.py`](file:///d:/Akshitakumawat/hackkk/tests/test_liquidity_cost_filters.py): **20/20 PASS**
   - Verified 31,483 screened candidates, 94,449 scenario evaluations, 26,822 eligible candidates, cross-product notional matching (`GOLDM` vs `GOLDTEN`), and active hash verification.
4. [`tests/test_walk_forward_backtest.py`](file:///d:/Akshitakumawat/hackkk/tests/test_walk_forward_backtest.py): **39/39 PASS**
   - Verified 9,668 signal attempts per scenario ($29,004$ total), 244 completed base trades, boundary censorship tracking, next-session Open execution, and immutability.
5. [`tests/test_dashboard.py`](file:///d:/Akshitakumawat/hackkk/tests/test_dashboard.py): **18/18 PASS**
   - Verified all 11 data loaders, metric calculators, scenario isolation, KPI integrity, and absence of `GOLD` from active normalized data.

**Total Tests:** **104 Passed** | **Failures:** 0 | **Errors:** 0 | **Time:** 35.47s

---

## 8. Dashboard Validation & Deployment Readiness

The interactive Streamlit application was validated locally on `http://localhost:8501`:
- All eight pages render without runtime warnings or unhandled exceptions.
- KPI cards, OHLC candlesticks, volume/OI charts, term structure forward curves, cost scenario breakdowns, cumulative equity curves, and fold diagnostic tables reflect the regenerated four-product datasets.
- Page A (Executive Overview) highlights: `Active MCX Products: 4 Contracts (GOLDM, GOLDTEN, GUINEA, PETAL)`.
- Page H (Data & Methodology) provides the complete "Active Contract Universe Policy" explaining why the 1kg contract was excluded and how historical reproducibility is preserved.

### Local Run Commands:
```powershell
# 1. Regenerate full pipeline (in dependency order)
python src/prepare_master_dataset.py
python src/normalize_prices.py
python src/build_relative_price_radar.py
python src/apply_liquidity_cost_filters.py
python src/run_walk_forward_backtest.py

# 2. Run full test suite
python -m unittest discover tests

# 3. Launch dashboard locally
streamlit run app.py
```

### Render Deployment Configuration:
The project is configured for Render deployment using the start command:
```bash
streamlit run app.py --server.address 0.0.0.0 --server.port $PORT
```
All dependencies remain specified in `requirements.txt`. No external API keys or credentials are required.
