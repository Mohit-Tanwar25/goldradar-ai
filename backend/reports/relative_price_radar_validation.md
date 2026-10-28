# Gold Contract Radar — MCX Commodity Derivatives Intelligence
## Phase 4: Relative Price Radar & Term Structure Engine Validation Report (Verified & Gap-Closed)

**Date of Validation:** October 24, 2026  
**Implementation Agent:** Antigravity IDE  
**Planning & Review Assistant:** ChatGPT  
**Target Event:** Hack in Hills '26  
**Pipeline Module:** `src/build_relative_price_radar.py`  
**Automated Test Suite:** `tests/test_relative_price_radar.py` (18 tests)  
**Regression Test Suite:** `tests/test_normalization.py` (8 tests)  
**Total Automated Tests:** 26 passed, 0 failed (100% success rate)

---

## 1. Executive Summary & Review Scope

This report documents the final verification and gap closure for **Phase 4: Relative Price Radar & Term Structure Modeling**.

The pipeline ingests the normalized dataset (`data/processed/mcx_gold_normalized.csv`, 16,195 rows, 42 columns) and generates three deterministic, validated derivative intelligence datasets:
1. **Output A (`data/processed/mcx_gold_relative_price_radar.csv`):** 9,059 rows of pure, same-expiry cross-product relative price comparisons.
2. **Output B (`data/processed/mcx_gold_term_structure.csv`):** 34,086 rows of same-symbol calendar spreads across all chronologically ordered expiry combinations.
3. **Output C (`data/processed/mcx_gold_term_structure_snapshots.csv`):** 16,195 rows of contract snapshots with calendar days to maturity.

### Key Methodological Clarifications & Corrections:
1. **Definition of `is_both_executable`:**
   - **Eligibility Only:** The flag `is_both_executable == True` indicates that on that observation date, both contracts met the project's data-eligibility criteria: positive traded volume (`volume_lots > 0`) and complete session OHLC prices.
   - **No Fill or Profitability Guarantee:** This flag **does NOT prove simultaneous fills, available market depth, acceptable slippage, or trading profitability**. Closing prices represent exchange reference points and do not guarantee execution feasibility.
2. **Correction on Term Structure Regimes (Contango vs Backwardation):**
   - The term structure is **NOT universally in contango**.
   - While contango is the predominant regime (~97.3% of pairs), **925 calendar spread pairs (2.71%) exhibit backwardation (`calendar_spread < 0`)**, including **396 pairs where both contracts were actively traded**.
   - Backwardation occurs during physical market tightness, prompt delivery tender squeezes, or abrupt price surges.
3. **Removal of "Arbitrage Parity" Claims:**
   - The observed proximity between standard 1 kg `GOLD` and 100g `GOLDM` (mean fine relative difference of **-0.042%**) is characterized strictly as **close-price alignment / empirical proximity**.
   - It is not claimed as executable arbitrage parity, because exchange transaction fees, clearing fees, bid-ask spread friction, delivery margins, and execution timing risks remain unmodeled.
4. **Data Integrity & Immutability:**
   - Zero source prices were fabricated, forward-filled, or interpolated.
   - All Phase 1, Phase 2, and Phase 3 files remain 100% byte-for-byte identical.

---

## 2. Input Dataset Profile

| Parameter | Observed Value | Validation Status |
| :--- | :--- | :---: |
| **Input File Path** | `data/processed/mcx_gold_normalized.csv` | **VERIFIED** |
| **Input Shape** | 16,195 rows $\times$ 42 columns | **VERIFIED** |
| **Trading Date Range** | `2024-01-01` to `2026-10-22` (724 trading days) | **VERIFIED** |
| **Covered Symbols** | `GOLD` (4,227), `GOLDGUINEA` (3,454), `GOLDPETAL` (3,454), `GOLDM` (3,012), `GOLDTEN` (2,048) | **VERIFIED** |
| **Primary Key Uniqueness** | `(date, symbol, expiry_date)`: 0 duplicate keys | **VERIFIED** |
| **Executable Observations** | 14,210 rows (`is_executable_traded == True`) | **VERIFIED** |
| **Non-Executable Observations**| 1,985 rows (`is_executable_traded == False`, zero-volume/carried close) | **VERIFIED** |

---

## 3. Output Datasets & Rigorous Verification

### Output A: Relative Price Radar (`data/processed/mcx_gold_relative_price_radar.csv`)
- **Row Count:** **9,059 rows**
- **Column Count:** **20 columns**
- **Primary Key:** `(date, symbol_a, expiry_a, symbol_b, expiry_b)` (0 duplicate keys).
- **Pair Invariants:** Deterministic ordering `symbol_a < symbol_b` strictly enforced (0 reversed duplicates, 0 self-pairs).
- **Comparison Basis:** 100% `same_expiry_cross_product` with `expiry_a == expiry_b`.

#### Breakdown by Product Pair:
| Symbol A | Symbol B | Total Pairs | Both Executable | Descriptive Only | Mean Quoted Diff (₹/g) | Mean Fine Diff (₹/g) | Mean Fine Rel Diff (%) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`GOLD`** | **`GOLDM`** | 1,387 | 1,372 | 15 | -₹2.88 | -₹2.90 | **-0.042%** |
| **`GOLDGUINEA`**| **`GOLDPETAL`** | 3,454 | 3,439 | 15 | ₹72.19 | ₹72.27 | **+0.574%** |
| **`GOLDGUINEA`**| **`GOLDTEN`** | 2,048 | 2,040 | 8 | ₹106.66 | ₹106.76 | **+0.872%** |
| **`GOLDPETAL`** | **`GOLDTEN`** | 2,048 | 2,040 | 8 | ₹116.89 | ₹117.01 | **+0.947%** |
| **`GOLDGUINEA`**| **`GOLDM`** | 61 | 6 | 55 | ₹97.23 | ₹127.28 | **+0.719%** |
| **`GOLDM`** | **`GOLDPETAL`** | 61 | 6 | 55 | -₹233.97 | -₹203.88 | **+1.686%** |
| **Total** | — | **9,059** | **8,903** | **156** | — | — | — |

---

### Output B: Same-Product Calendar Spreads (`data/processed/mcx_gold_term_structure.csv`)
- **Row Count:** **34,086 rows**
- **Column Count:** **19 columns**
- **Primary Key:** `(date, symbol, nearer_expiry, deferred_expiry)` (0 duplicate keys).
- **Ordering Constraint:** `nearer_expiry < deferred_expiry` strictly enforced (0 reversed pairs).
- **Maturity Gap:** $27 \le \text{calendar\_days\_between\_expiries} \le 309$ days (100% strictly $> 0$).

#### Per-Symbol Spread Distribution & Contango/Backwardation Analysis:
| Symbol | Total Pairs | Contango Pairs ($>0$) | Backwardation Pairs ($<0$) | Flat ($=0$) | Executable Total | Executable Contango | Executable Backwardation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`GOLD`** | 10,275 | 9,779 (95.17%) | **496 (4.83%)** | 0 | 2,936 | 2,894 (98.57%) | **42 (1.43%)** |
| **`GOLDGUINEA`** | 6,856 | 6,628 (96.67%) | **226 (3.30%)** | 2 | 6,480 | 6,305 (97.30%) | **173 (2.67%)** |
| **`GOLDM`** | 5,535 | 5,429 (98.08%) | **106 (1.92%)** | 0 | 5,486 | 5,396 (98.36%) | **90 (1.64%)** |
| **`GOLDPETAL`** | 6,856 | 6,783 (98.94%) | **71 (1.04%)** | 2 | 6,829 | 6,759 (98.97%) | **68 (1.00%)** |
| **`GOLDTEN`** | 4,564 | 4,537 (99.41%) | **26 (0.57%)** | 1 | 4,556 | 4,532 (99.47%) | **23 (0.50%)** |
| **Total** | **34,086** | **33,156 (97.27%)** | **925 (2.71%)** | **5** | **26,287** | **25,886 (98.47%)** | **396 (1.51%)** |

#### Annualized Spread Percentiles (`fine_annualized_spread_pct`):
| Symbol | P01 (1%) | P05 (5%) | P25 (25%) | Median (50%) | P75 (75%) | P95 (95%) | P99 (99%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`GOLD`** | -5.01% | +0.05% | +3.50% | **+5.38%** | +8.97% | +16.97% | +28.30% |
| **`GOLDGUINEA`** | -4.39% | +1.50% | +6.29% | **+9.78%** | +14.05% | +21.48% | +39.51% |
| **`GOLDM`** | -3.01% | +2.83% | +6.37% | **+9.55%** | +14.00% | +19.23% | +33.36% |
| **`GOLDPETAL`** | -0.16% | +3.35% | +6.97% | **+9.39%** | +13.74% | +20.31% | +37.32% |
| **`GOLDTEN`** | +1.58% | +5.26% | +8.36% | **+11.79%** | +15.18% | +21.24% | +38.82% |

*Key Takeaway:* While contango represents ~97.3% of observations, backwardation is a verified market phenomenon in MCX gold futures, occurring across all five symbols.

---

### Output C: Term-Structure Snapshots (`data/processed/mcx_gold_term_structure_snapshots.csv`)
- **Row Count:** **16,195 rows** (Exact parity with input dataset).
- **Column Count:** **10 columns**.
- **Days to Expiry Range:** **0 to 356 calendar days** (Median: 84.0 days).
- **Records Dated After Expiry (`days_to_expiry < 0`):** **0 records**.
- **Expiry Day Observations (`days_to_expiry == 0`):** **129 records**.

---

## 4. Hand-Calculated Formula Verification

### Example 1: Same-Expiry Cross-Product Comparison
- **Inputs:**
  - Date: `2024-01-01`, Expiry: `2024-02-05`
  - Leg A (`GOLD`): Quoted Close = ₹63,320.00 / 10g $\rightarrow$ `close_per_gram_a` = **₹6,332.000/g**
    - Purity: 995 $\rightarrow$ `close_fine_per_gram_a` = $6332.0 / 0.995$ = **₹6,363.819095/g**
  - Leg B (`GOLDM`): Quoted Close = ₹63,297.00 / 10g $\rightarrow$ `close_per_gram_b` = **₹6,329.700/g**
    - Purity: 995 $\rightarrow$ `close_fine_per_gram_b` = $6329.7 / 0.995$ = **₹6,361.507538/g**
- **Hand Calculations:**
  - $\text{quoted\_diff} = 6332.000 - 6329.700 = \mathbf{+₹2.300/g}$
  - $\text{quoted\_rel\_diff\_pct} = 100 \times \frac{2.300}{6329.700} = \mathbf{+0.036337\%}$
  - $\text{fine\_diff} = 6363.819095 - 6361.507538 = \mathbf{+₹2.311557/g}$
  - $\text{fine\_rel\_diff\_pct} = 100 \times \frac{2.311557}{6361.507538} = \mathbf{+0.036337\%}$
- **Pipeline Match:** Row 0 in `mcx_gold_relative_price_radar.csv` matches to 6 decimal places.

### Example 2: Same-Symbol Calendar Spread
- **Inputs:**
  - Date: `2024-01-01`, Symbol: `GOLD`
  - Nearer Expiry: `2024-02-05`, Nearer Close = ₹6,332.000/g (Fine: ₹6,363.819095/g)
  - Deferred Expiry: `2024-04-05`, Deferred Close = ₹6,362.900/g (Fine: ₹6,394.874372/g)
  - $\text{calendar\_days} = \text{2024-04-05} - \text{2024-02-05} = \mathbf{60\text{ days}}$
- **Hand Calculations:**
  - $\text{quoted\_spread} = 6362.900 - 6332.000 = \mathbf{+₹30.900/g}$
  - $\text{fine\_spread} = 6394.874372 - 6363.819095 = \mathbf{+₹31.055277/g}$
  - $\text{fine\_rel\_spread\_pct} = 100 \times \frac{31.055277}{6363.819095} = \mathbf{+0.487998\%}$
  - $\text{fine\_annualized\_pct} = 0.487998 \times \frac{365}{60} = \mathbf{+2.968654\%}$
- **Pipeline Match:** Row 0 in `mcx_gold_term_structure.csv` matches to 6 decimal places.

---

## 5. Automated Test Suite Results

Test execution command:
```bash
python -m unittest discover tests
```

Execution output:
```text
Ran 26 tests in 37.741s

OK
```

### Complete Test Catalog:
1. **`tests/test_relative_price_radar.py` (18 tests):**
   - `test_quoted_price_difference_formula` — **PASS**
   - `test_fine_price_difference_formula` — **PASS**
   - `test_relative_difference_and_invalid_denominators` (handles zero, negative, NaN denominators) — **PASS**
   - `test_same_date_matching_invariant` (prevents cross-date pairing) — **PASS**
   - `test_same_expiry_cross_product_identification` (pairs matching expiries only) — **PASS**
   - `test_no_self_pairs_or_reversed_duplicates` (enforces $symbol_a < symbol_b$) — **PASS**
   - `test_calendar_spread_formula_and_ordering` (strictly $nearer < deferred$) — **PASS**
   - `test_positive_expiry_gap_validation` (rejects zero/negative day gaps) — **PASS**
   - `test_annualized_spread_formula_and_invalid_inputs` (validates days, prices, and NaNs) — **PASS**
   - `test_non_executable_observations_handling` (requires both legs active for `is_both_executable`) — **PASS**
   - `test_missing_data_preservation_as_null` (no zero-coercion) — **PASS**
   - `test_sparse_dates_and_missing_expiry_pairs` (no spurious pairs on sparse dates) — **PASS**
   - `test_expired_contracts_flagging_in_snapshots` (flags records dated after nominal expiry) — **PASS**
   - `test_input_duplicate_detection` (rejects corrupted input with duplicate keys) — **PASS**
   - `test_deterministic_outputs_on_repeated_runs` (verifies rerun byte-level determinism) — **PASS**
   - `test_output_a_integrity` (validates Output A schema and constraints) — **PASS**
   - `test_output_b_integrity` (validates Output B schema and constraints) — **PASS**
   - `test_output_c_integrity` (validates Output C schema and constraints) — **PASS**
2. **`tests/test_normalization.py` (8 Phase 3 regression tests):**
   - `test_quotation_divisors` — **PASS**
   - `test_fine_gold_factors` (including verified 999 GOLDGUINEA) — **PASS**
   - `test_row_count_and_columns_preserved` — **PASS**
   - `test_price_per_gram_math` — **PASS**
   - `test_fine_gold_price_per_gram_math` — **PASS**
   - `test_missing_ohlc_preservation` — **PASS**
   - `test_no_duplicate_keys` — **PASS**
   - `test_goldten_start_date` — **PASS**

---

## 6. Fixes Implemented During Verification

1. **Empty DataFrame Handling in Pipeline Functions:**
   - Updated `build_relative_price_radar` and `build_term_structure_spreads` in `src/build_relative_price_radar.py` to define explicit `RADAR_COLUMNS` and `TERM_COLUMNS`. If no pairs are generated (e.g. for a synthetic single-observation test slice), the functions cleanly return an empty DataFrame with proper schema instead of encountering a sorting `KeyError`.
2. **Console Encoding Safeguard:**
   - Replaced Unicode checkmarks in pipeline logging with ASCII `[PASS]` tags to eliminate potential `cp1252` encoding issues on standard Windows shell environments.
3. **Comprehensive Test Coverage:**
   - Expanded unit tests from 8 to 18 tests, adding explicit coverage for invalid denominators, sparse dates, input duplicates, negative days to expiry, and rerun determinism.

---

## 7. Assumptions, Limitations & Non-Executable Exclusions

1. **Executability vs Tradability:**
   - 156 radar pairs (1.7%) and 7,799 calendar spread pairs (22.9%) contain at least one non-traded leg (`is_executable_traded == False`).
   - These are included for descriptive term structure tracking, but marked `is_both_executable == False`.
   - In Phase 5 and Phase 6, trading signals and backtests must strictly restrict order simulation to `is_both_executable == True` records.
2. **Execution Friction Unmodeled:**
   - Relative price differences and calendar spreads are close-to-close metrics. They do not account for bid-ask spreads, market depth, execution slippage, clearing/exchange fees, GST, or delivery margins.
3. **Linear Annualization Convention:**
   - Annualized spreads use simple linear scaling ($\text{rel\_spread} \times 365 / \text{days}$) for descriptive comparability. They do not represent compound financing rates.

---

## 8. Acceptance Criteria Scorecard

| Acceptance Criterion | Status | Evidence & Verification |
| :--- | :---: | :--- |
| **All three output CSVs generated** | **PASS** | `mcx_gold_relative_price_radar.csv`, `mcx_gold_term_structure.csv`, `mcx_gold_term_structure_snapshots.csv` verified on disk. |
| **Every pair compares observations from same date** | **PASS** | 100% of 9,059 radar pairs and 34,086 term structure pairs share identical observation dates. |
| **Calendar spreads use same symbol and ordered expiries** | **PASS** | 100% of 34,086 calendar spreads strictly satisfy `nearer_expiry < deferred_expiry` and `days_gap > 0`. |
| **No continuous-contract stitching** | **PASS** | Every contract retains its individual `(symbol, expiry_date)` identity. |
| **No missing prices fabricated or forward-filled** | **PASS** | Missing prices remain strictly `NaN`. Zero prices fabricated. |
| **Non-executable observations explicitly flagged** | **PASS** | `is_both_executable` column explicitly classifies all pairs. |
| **Outputs unique and deterministically sorted** | **PASS** | Zero duplicate keys across all three outputs. Deterministic ordering verified. |
| **Formulas pass hand-calculated synthetic tests** | **PASS** | Synthetic unit tests passed with exact matching ($rtol \le 10^{-6}$). |
| **Existing Phase 3 tests still pass** | **PASS** | All 8 Phase 3 normalization regression tests passed. |
| **Validation report reflects actual execution** | **PASS** | All counts, tables, and statistics derived directly from generated outputs. |
| **All unresolved issues disclosed** | **PASS** | Non-executable exclusions, backwardation episodes, and execution friction caveats fully documented. |

---
*Phase 4 Final Verification and Gap Closure is complete. Ready for ChatGPT review.*
