# Gold Contract Radar — MCX Commodity Derivatives Intelligence
## Phase 5: Liquidity & Transaction Cost Filters Validation Report

**Date of Validation:** October 24, 2026  
**Implementation Agent:** Antigravity IDE  
**Planning & Review Assistant:** ChatGPT  
**Target Event:** Hack in Hills '26  
**Pipeline Module:** `src/apply_liquidity_cost_filters.py`  
**Configuration Files:** `config/liquidity_filters.json` (v1.0.0), `config/transaction_costs.json` (v1.0.0), `config/contract_specs.json`  
**Automated Test Suite:** `tests/test_liquidity_cost_filters.py` (20 unit tests)  
**Total Automated Tests:** 46 passed across Phase 3 (8), Phase 4 (18), and Phase 5 (20) (100% pass rate)

---

## 1. Executive Summary & Review Scope

This validation report documents the complete implementation, screening results, cost modeling, and quality audits for **Phase 5: Liquidity & Transaction Cost Filters**.

The pipeline ingests the validated derivative intelligence outputs from Phase 4 and normalized market records from Phase 3, keeping both candidate types strictly segregated:
1. **Strategy A (Cross-Product Same-Expiry Comparisons):** 9,059 candidate pairs from `data/processed/mcx_gold_relative_price_radar.csv`.
2. **Strategy B (Same-Symbol Calendar Spreads):** 34,086 candidate pairs from `data/processed/mcx_gold_term_structure.csv`.

Across the combined **43,145 candidates**, Phase 5 implements a transparent 5-tier classification framework:
- **Level 1 (Observed Historical Relationship):** All 43,145 raw pairs.
- **Level 2 (Data-Eligible Candidates):** 35,190 pairs (81.56%) meeting positive traded volume, complete session OHLC, and valid price flags.
- **Level 3 (Filtered Active Candidates):** 29,726 pairs (68.90%) satisfying data eligibility, contract maturity ($DTE \ge 5$), and configurable liquidity (volume & open interest) thresholds.
- **Level 4 (Modeled Cost Feasibility):** 35,190 pairs whose round-trip transaction costs can be modeled across `base`, `low`, and `high` broker/exchange schedules.
- **Level 5 (Positive Modeled Net Spread):** 28,239 eligible pairs (95.0% of Level 3) where the modeled gross spread exceeds modeled base round-trip transaction costs.

> [!IMPORTANT]
> **Executability and Profitability Disclaimer:**  
> Passing the configurable liquidity and transaction cost filters indicates statistical eligibility under the project's historical rules only. It does **NOT** prove that a trade was executable in real time, that simultaneous fills were achievable, that order-book depth was sufficient to absorb the order without market impact, or that the trade yielded net profits. All prices are daily closing reference marks, not synchronized tick quotes.

---

## 2. Input Dataset Audit

All input datasets were consumed directly without modification:

| Input File | Source Phase | Row Count | Column Count | Integrity Hash (SHA-256 Prefix) | Validation Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `data/processed/mcx_gold_normalized.csv` | Phase 3 | 16,195 | 42 | `26c57ce9ad54f271` | **VERIFIED (Unchanged)** |
| `data/processed/mcx_gold_relative_price_radar.csv` | Phase 4 | 9,059 | 20 | `38f13aeddb2454f9` | **VERIFIED (Unchanged)** |
| `data/processed/mcx_gold_term_structure.csv` | Phase 4 | 34,086 | 19 | `d81102755b7f1b85` | **VERIFIED (Unchanged)** |
| `data/processed/mcx_gold_term_structure_snapshots.csv`| Phase 4 | 16,195 | 10 | `f064bf4e75ff6791` | **VERIFIED (Unchanged)** |
| `config/contract_specs.json` | Phase 3/4 | — | — | `5461 bytes` | **VERIFIED (Unchanged)** |

---

## 3. Screening & Filter Results

### 3.1 Overall Pipeline Funnel

| Stage / Filter | Total Candidates | Same-Expiry Cross-Product (Radar) | Same-Symbol Calendar Spreads | Overall Pass Rate |
| :--- | :---: | :---: | :---: | :---: |
| **Total Candidates Screened** | **43,145** | 9,059 | 34,086 | **100.00%** |
| **1. Data Eligibility** (`is_both_data_eligible`) | **35,190** | 8,903 (98.28%) | 26,287 (77.12%) | **81.56%** |
| **2. Expiry & Tender Filter** (`passes_expiry_filter`)| **40,784** | 8,720 (96.26%) | 32,064 (94.07%) | **94.53%** |
| **3. Volume Threshold** (`passes_volume_filter`) | **32,356** | 8,548 (94.36%) | 23,808 (69.85%) | **74.99%** |
| **4. Open Interest Threshold** (`passes_open_interest_filter`) | **32,293** | 8,513 (93.97%) | 23,780 (69.76%) | **74.85%** |
| **Combined Liquidity Filter** (`passes_liquidity_filter`) | **31,659** | 8,419 (92.94%) | 23,240 (68.18%) | **73.38%** |
| **All Filters Eligible** (`is_all_filters_eligible`) | **29,726** | **8,136 (89.81%)** | **21,590 (63.34%)** | **68.90%** |

*Note: Filters are evaluated independently and jointly. A candidate may fail multiple filters simultaneously.*

---

### 3.2 Breakdown by Product & Pair Type

#### A. Calendar Spreads by Symbol:
| Symbol | Total Candidates | Data Eligible | Expiry Filter Pass | Liquidity Filter Pass | All Filters Eligible | Rejection Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`GOLD`** (1 kg) | 10,275 | 2,936 (28.57%) | 9,945 (96.79%) | 1,796 (17.48%) | **1,665 (16.20%)** | 83.80% |
| **`GOLDGUINEA`** (8g) | 6,856 | 6,480 (94.52%) | 6,369 (92.90%) | 5,577 (81.34%) | **5,167 (75.36%)** | 24.64% |
| **`GOLDM`** (100g) | 5,535 | 5,486 (99.11%) | 5,107 (92.27%) | 4,967 (89.74%) | **4,551 (82.22%)** | 17.78% |
| **`GOLDPETAL`** (1g) | 6,856 | 6,829 (99.61%) | 6,369 (92.90%) | 6,562 (95.71%) | **6,138 (89.53%)** | 10.47% |
| **`GOLDTEN`** (10g) | 4,564 | 4,556 (99.82%) | 4,274 (93.65%) | 4,338 (95.05%) | **4,069 (89.15%)** | 10.85% |
| **Total** | **34,086** | **26,287 (77.12%)** | **32,064 (94.07%)** | **23,240 (68.18%)** | **21,590 (63.34%)** | **36.66%** |

*Key Empirical Finding:* Standard `GOLD` has multiple far-deferred expiries extending up to 12 months forward where open interest and trading volume are dormant (zero volume in 43.5% of records). As a result, 83.8% of theoretical calendar spread combinations in `GOLD` are properly quarantined as inactive. Retail contracts (`GOLDM`, `GOLDPETAL`, `GOLDTEN`) exhibit high active participation across prompt contracts (82%–90% pass rates).

#### B. Same-Expiry Cross-Product Pairs:
| Leg A Symbol | Leg B Symbol | Total Pairs | Data Eligible | Expiry Pass | Liquidity Pass | All Filters Eligible | Pass Rate (%) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`GOLD`** | **`GOLDM`** | 1,387 | 1,369 | 1,325 | 1,291 | **1,239** | **89.33%** |
| **`GOLDGUINEA`** | **`GOLDM`** | 61 | 61 | 57 | 60 | **56** | **91.80%** |
| **`GOLDGUINEA`** | **`GOLDPETAL`** | 3,454 | 3,331 | 3,325 | 3,052 | **2,954** | **85.52%** |
| **`GOLDGUINEA`** | **`GOLDTEN`** | 2,048 | 2,037 | 1,978 | 1,960 | **1,897** | **92.63%** |
| **`GOLDM`** | **`GOLDPETAL`** | 61 | 61 | 57 | 60 | **56** | **91.80%** |
| **`GOLDPETAL`** | **`GOLDTEN`** | 2,048 | 2,044 | 1,978 | 1,996 | **1,934** | **94.43%** |
| **Total** | — | **9,059** | **8,903** | **8,720** | **8,419** | **8,136** | **89.81%** |

---

### 3.3 Independent Machine-Readable Exclusion Reasons

Every screened candidate is assigned explicit machine-readable exclusion reasons. Candidates passing all criteria receive `'NONE'`.

| Exclusion Reason Code | Description / Condition | Observed Occurrences | % of Total Candidates |
| :--- | :--- | :---: | :---: |
| **`NONE`** | Candidate passed all data, expiry, and liquidity filters | **29,726** | **68.90%** |
| **`open_interest_below_threshold_leg_b`** | Leg B open interest < configured threshold | 10,417 | 24.14% |
| **`volume_below_threshold_leg_b`** | Leg B volume < configured threshold | 10,395 | 24.09% |
| **`incomplete_ohlc_leg_b`** | Leg B session OHLC incomplete / missing | 7,804 | 18.09% |
| **`zero_volume_leg_b`** | Leg B has zero volume / carried reference mark | 7,804 | 18.09% |
| **`volume_below_threshold_leg_a`** | Leg A volume < configured threshold | 3,006 | 6.97% |
| **`open_interest_below_threshold_leg_a`** | Leg A open interest < configured threshold | 2,883 | 6.68% |
| **`insufficient_days_to_expiry`** | Contract maturity $0 < DTE < 5$ days (tender notice window) | 1,784 | 4.13% |
| **`incomplete_ohlc_leg_a`** | Leg A session OHLC incomplete / missing | 1,779 | 4.12% |
| **`zero_volume_leg_a`** | Leg A has zero volume / carried reference mark | 1,779 | 4.12% |
| **`expired_or_expiry_day`** | Observation date on or after expiry day ($DTE \le 0$) | 577 | 1.34% |

---

## 4. Transaction Cost Modeling & Analysis

### 4.1 Statutory Charges & Verified Fee Schedule

All statutory charges and regulatory levies are documented with source citations:

| Cost Component | Applicable Rate | Charge Basis | Applicable Side | Statutory / Regulatory Source | Verification Status |
| :--- | :---: | :---: | :---: | :--- | :---: |
| **Commodity Transaction Tax (CTT)** | **0.01%** (₹1,000/Cr) | Sell Turnover | Sell side only | Finance Act 2013 (Chapter VII, Section 116) | **VERIFIED** |
| **Stamp Duty** | **0.002%** (₹200/Cr) | Buy Turnover | Buy side only | Indian Stamp Act, 1899 (Finance Act 2019 amendment, eff. July 1, 2020) | **VERIFIED** |
| **SEBI Turnover Charge** | **0.0001%** (₹10/Cr) | Total Turnover | Both (Buy & Sell) | SEBI (Stock Brokers) (Amendment) Regulations | **VERIFIED** |
| **MCX Exchange Turnover Fee** | **0.0021%** (₹210/Cr) | Total Turnover | Both (Buy & Sell) | MCX Circular MCX/TRD/057/2023 (Non-agri futures base slab) | **VERIFIED** |
| **Goods & Services Tax (GST)** | **18.0%** | Service Fees | Both | CGST Act, 2017 (Levied on Brokerage + Exch Fee + SEBI Fee; CTT & Stamp exempt) | **VERIFIED** |

---

### 4.2 Configured Brokerage & Fee Scenarios

To assess execution feasibility under varying market participant profiles, 3 scenarios are evaluated:

| Parameter | Base Scenario (Discount Broker) | Low Scenario (Institutional / HFT) | High Scenario (Full-Service Retail) |
| :--- | :---: | :---: | :---: |
| **Participant Profile** | Standard retail / active trader | Prop desk / HFT rebate tier | Traditional retail client |
| **Brokerage Model** | $\min(₹20, 0.03\%\text{ turnover})$ | $\min(₹10, 0.01\%\text{ turnover})$ | $0.02\%\text{ of turnover}$ (2 bps) |
| **Exchange Turnover Fee** | 0.0021% (₹210 / Cr) | 0.0015% (₹150 / Cr volume rebate) | 0.0026% (₹260 / Cr top slab) |
| **SEBI Turnover Charge** | 0.0001% (₹10 / Cr) | 0.0001% (₹10 / Cr) | 0.0001% (₹10 / Cr) |
| **Stamp Duty Rate** | 0.0020% (Buy side) | 0.0020% (Buy side) | 0.0020% (Buy side) |
| **CTT Rate** | 0.0100% (Sell side) | 0.0100% (Sell side) | 0.0100% (Sell side) |
| **GST Rate** | 18.0% on service charges | 18.0% on service charges | 18.0% on service charges |
| **Status Classification** | `ASSUMPTION_BASED_WITH_VERIFIED_STATUTORY_RATES` | `ASSUMPTION_BASED_WITH_VERIFIED_STATUTORY_RATES` | `ASSUMPTION_BASED_WITH_VERIFIED_STATUTORY_RATES` |

---

### 4.3 Quantity Matching & Notional Calculation

1. **Exchange Notional vs Purity Factor:**
   - Contract trading notional is computed strictly from the **quoted close per gram** multiplied by the **contract trading unit in grams**:
     $$\text{Notional per lot} = \text{Close}_{\text{quoted, per gram}} \times U_{\text{trading unit grams}}$$
   - In accordance with MCX trading rules, **no fineness/purity adjustments are applied to turnover**. Purity adjustments apply only to physical delivery DDR calculations.
2. **Calendar Spreads:**
   - The nearer and deferred legs have the same symbol and identical trading units ($U_a = U_b$).
   - Modeled position: strictly **1 lot nearer and 1 lot deferred** (`exact_1_to_1_lot`), matching physical exposure exactly.
3. **Cross-Product Comparisons (Integer-Lot LCM Matching):**
   - Different gold contracts trade in different lot sizes (1g to 1,000g). A 1-lot to 1-lot comparison represents mismatched financial exposure.
   - For every cross-product candidate pair, the engine computes the Least Common Multiple (LCM) of the trading units in grams ($G_{\text{matched}} = \text{LCM}(U_a, U_b)$):
     - `GOLD` (1,000g) vs `GOLDM` (100g): 1 lot GOLD = 10 lots GOLDM (1,000g matched).
     - `GOLDGUINEA` (8g) vs `GOLDPETAL` (1g): 1 lot GOLDGUINEA = 8 lots GOLDPETAL (8g matched).
     - `GOLDGUINEA` (8g) vs `GOLDTEN` (10g): 5 lots GOLDGUINEA = 4 lots GOLDTEN (40g matched).
     - `GOLDPETAL` (1g) vs `GOLDTEN` (10g): 10 lots GOLDPETAL = 1 lot GOLDTEN (10g matched).
     - `GOLDGUINEA` (8g) vs `GOLDM` (100g): 25 lots GOLDGUINEA = 2 lots GOLDM (200g matched).
     - `GOLDM` (100g) vs `GOLDPETAL` (1g): 1 lot GOLDM = 100 lots GOLDPETAL (100g matched).
   - Modeled round-trip transaction costs are computed for this matched integer-lot bundle and normalized by $G_{\text{matched}}$ to yield **cost per gram**.
   - *Crucial Caveat:* While mathematically balanced in physical grams, this does **not** constitute an economic arbitrage hedge due to physical delivery differences (bars vs coins, 995 vs 999 fineness, delivery tender logic).

---

### 4.4 Scenario Sensitivity Analysis

#### Across Eligible Candidates Only (29,726 rows in Output C):
| Cost Scenario | Mean Round-Trip Cost (₹ per candidate) | Mean Round-Trip Cost (₹ per gram) | Candidates Where Gross Spread > Modeled Cost | % of Eligible Subset |
| :--- | :---: | :---: | :---: | :---: |
| **Low** (Institutional) | ₹477.30 | ₹7.83 / g | 28,661 | **96.42%** |
| **Base** (Discount Broker) | ₹557.68 | ₹13.49 / g | 28,239 | **94.99%** |
| **High** (Full-Service) | ₹1,829.77 | ₹16.98 / g | 27,611 | **92.89%** |

*Takeaway:* For active, liquid calendar spreads and cross-product differences, the typical gross spread (₹30 to ₹80/g) comfortably exceeds modeled baseline execution costs (~₹2.50/g for 1kg GOLD, ~₹13.49/g average across all denominations). However, for prompt expiries with tight spreads ($< ₹2.50$/g), gross spreads fail to cover round-trip friction.

---

## 5. Output Datasets & Quality Checks

The Phase 5 pipeline generated three reproducible datasets in `data/processed/`:

### 5.1 Output Files Summary
| Output File | Description | Row Count | Primary Key | Key Uniqueness |
| :--- | :--- | :---: | :---: | :---: |
| **Output A** (`mcx_gold_liquidity_filtered_candidates.csv`)| Complete screened candidate inventory | **43,145** | `candidate_id` | **0 duplicates (100% unique)** |
| **Output B** (`mcx_gold_transaction_cost_scenarios.csv`)| Scenario cost calculations (`base`, `low`, `high`)| **129,435** | `(candidate_id, scenario_name)` | **0 duplicates (100% unique)** |
| **Output C** (`mcx_gold_eligible_candidates.csv`)| Filtered trade-eligible candidates subset | **29,726** | `candidate_id` | **0 duplicates (100% unique)** |

---

### 5.2 Quality Assurance Checklist

- **No Data Fabrication:** Zero prices or volumes were fabricated, forward-filled, or interpolated.
- **Unavailable Cost Quarantine:** For all 7,955 data-ineligible candidates, modeled costs and net spreads are strictly preserved as `NaN` (never coerced to zero).
- **Date Matching Invariant:** 100% of candidate pairs share the exact same observation date.
- **Expiry Order Invariant:** 100% of calendar spreads satisfy `nearer_expiry < deferred_expiry` and `calendar_days_between_expiries > 0`.
- **Reproducibility:** Pipeline rerun produces 100% identical row counts, flags, and floating-point cost calculations.
- **Upstream Immutability:** SHA-256 prefixes of all Phase 1–4 outputs verified identical before and after Phase 5 execution.

---

## 6. Automated Test Suite Results

Test execution command:
```bash
python -m unittest discover tests
```

Execution output:
```text
Ran 46 tests in 62.168s

OK
```

### Complete Test Catalog:
1. **`tests/test_liquidity_cost_filters.py` (20 Phase 5 tests):**
   - `test_01_hand_calculated_single_leg_cost_breakdown` — **PASS**
   - `test_02_cost_components_not_double_counted` — **PASS**
   - `test_03_missing_or_invalid_inputs_produce_nan_costs` — **PASS**
   - `test_04_integer_lot_lcm_exposure_matching` — **PASS**
   - `test_05_rejection_of_zero_volume_and_incomplete_ohlc` — **PASS**
   - `test_06_expiry_filters_and_tender_period_rejection` — **PASS**
   - `test_07_scenario_cost_ordering` — **PASS**
   - `test_08_output_a_row_count_and_candidate_types` — **PASS**
   - `test_09_candidate_id_uniqueness` — **PASS**
   - `test_10_cross_product_same_date_and_same_expiry` — **PASS**
   - `test_11_calendar_spread_nearer_deferred_ordering` — **PASS**
   - `test_12_output_b_scenario_key_uniqueness` — **PASS**
   - `test_13_output_c_eligible_candidates_integrity` — **PASS**
   - `test_14_zero_volume_rejected_consistently` — **PASS**
   - `test_15_expiry_day_observations_rejected` — **PASS**
   - `test_16_notional_math_and_exposure_units` — **PASS**
   - `test_17_cross_product_notional_purity_distinction` — **PASS**
   - `test_18_unavailable_costs_remain_nan` — **PASS**
   - `test_19_pipeline_deterministic_reruns` — **PASS**
   - `test_20_upstream_datasets_immutability` — **PASS**
2. **`tests/test_relative_price_radar.py` (18 Phase 4 regression tests):** All 18 passed.
3. **`tests/test_normalization.py` (8 Phase 3 regression tests):** All 8 passed.

---

## 7. Known Limitations & Non-Executable Boundaries

1. **Daily OHLCV Aggregation vs Intraday Order Book:**
   - Closing bhavcopy prices reflect end-of-day trade reference points. They do not prove that bid-ask quotes were continuous or that simultaneous order fills were achievable.
2. **Unmodeled Execution Slippage & Market Impact:**
   - While statutory fees, exchange charges, and brokerages are modeled, bid-ask spread crossing and order book depth impact remain unmodeled.
3. **Holding Period & Roll Mechanics:**
   - Phase 5 establishes entry eligibility and round-trip reference cost schedules. Dynamic multi-day holding periods, margin financing, and roll execution policies will be modeled in Phase 6.

---

## 8. Acceptance Criteria Scorecard

| Acceptance Criterion | Status | Evidence & Verification |
| :--- | :---: | :--- |
| **Phase 3 and Phase 4 outputs consumed without modification** | **PASS** | Hashes verified byte-identical; all 16,195 master rows preserved. |
| **Cross-product and calendar spreads strictly separated** | **PASS** | `candidate_type` field explicitly separates 9,059 radar vs 34,086 calendar pairs. |
| **All candidates retained with audit flags and exclusion reasons**| **PASS** | Output A retains all 43,145 candidates with machine-readable reasons. |
| **Zero-volume records quarantined from execution** | **PASS** | 100% of zero-volume records rejected with `zero_volume_leg` flags. |
| **Liquidity & expiry filters configurable & documented** | **PASS** | Configured in `config/liquidity_filters.json` with per-symbol overrides. |
| **Contract specifications & integer lot matching respected** | **PASS** | LCM integer-lot exposure matching enforced across all distinct products. |
| **Verified statutory rates distinguished from assumptions** | **PASS** | Documented in `config/transaction_costs.json` with statutory citations. |
| **Unknown costs never silently treated as zero** | **PASS** | Data-ineligible records yield `NaN` modeled costs and `unavailable` status. |
| **20 unit tests covering edge cases & invariants** | **PASS** | `tests/test_liquidity_cost_filters.py` passed with 20/20 test cases. |
| **Full test suite passes** | **PASS** | 46/46 tests passed across repository in 62.17s. |
| **No Phase 6–8 work started** | **PASS** | Backtesting, ML, and dashboard development strictly deferred. |

---
*Phase 5 implementation is complete. Ready for ChatGPT review.*
