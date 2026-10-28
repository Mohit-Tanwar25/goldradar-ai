# Gold Contract Radar — MCX Commodity Derivatives Intelligence
## Phase 3: Price Normalization & Contract Specifications Validation Report (Updated)

**Date of Validation:** October 24, 2026  
**Implementation Agent:** Antigravity IDE  
**Planning & Review Assistant:** ChatGPT  
**Target Event:** Hack in Hills '26  
**Input Master Dataset:** `data/processed/mcx_gold_master.csv` (16,195 rows, 28 columns)  
**Output Normalized Dataset:** `data/processed/mcx_gold_normalized.csv` (16,195 rows, 42 columns)  
**Configuration File:** `config/contract_specs.json` (Includes verified GOLDGUINEA 999 purity)  
**Automated Test Suite:** `tests/test_normalization.py` (8/8 tests passed)

---

## 1. Executive Summary & Correction Overview

During Phase 3 review, official MCX contract specifications and circulars were cross-referenced to verify whether `GOLDGUINEA` purity is 995 or 999 fineness. 

### Resolution & Correction:
- **Discrepancy Source:** Informal third-party broker summaries cited 995 spot polling basis; however, official MCX contract specifications mandate **999 purity** (24-karat fineness, serially numbered coins/bars supplied with quality certicards by LBMA/MCX approved refiners).
- **Settlement Formula Confirmation:** MCX's official Due Date Rate (DDR) formula explicitly scales polled Ahmedabad 995 spot prices by $\frac{999}{995}$ to reflect the 999 contract purity:
  $$\text{DDR}_{\text{GOLDGUINEA}} = \left(\text{Spot Price}_{995} \times \frac{999}{995}\right) \times \frac{8}{10}$$
- **Pipeline Update:** `config/contract_specs.json` was updated with `underlying_purity_fineness: 999` and `fine_gold_factor: 0.999`. The normalization pipeline `src/normalize_prices.py` was rerun to regenerate `data/processed/mcx_gold_normalized.csv`.
- **Validation:** Automated unit test suite `tests/test_normalization.py` was updated and executed: **all 8 unit tests passed with 100% precision**.

---

## 2. Validation Checklist (All 10 Requirements)

| Requirement | Result | Target Metric | Observed Master Metric | Validation Evidence & Details |
| :--- | :---: | :---: | :---: | :--- |
| **1. Input/Output Row Count Parity** | **PASS** | 16,195 rows | 16,195 rows | Exact match. Zero rows dropped or added. |
| **2. Key & Lineage Retention** | **PASS** | 100% match | 100% match | All 16,195 rows retain original `date`, `symbol`, `expiry_date`, `source_file`, and `source_row`. |
| **3. Documented Divisors with Evidence** | **PASS** | 5 / 5 symbols | 5 / 5 symbols | Backed by official MCX specifications documented in `config/contract_specs.json` and `reports/contract_specifications.md`. |
| **4. Formula Compliance** | **PASS** | Exact match | Exact match | $price\_per\_gram = quoted\_price / D_s$ verified across 100% of observations ($rtol \le 10^{-6}$). |
| **5. Missing OHLC Preservation** | **PASS** | 1,985 nulls | 1,985 nulls | Missing Open, High, Low remain strictly `NaN` in both raw and normalized metrics. |
| **6. Zero-Volume Flags Intact** | **PASS** | 1,985 flags | 1,985 flags | `flag_zero_volume` and `flag_missing_ohlc` perfectly preserved. |
| **7. Duplicate Prevention** | **PASS** | 0 duplicates | 0 duplicates | Unique primary keys on `(date, symbol, expiry_date)` verified. |
| **8. No Silent Zero-Coercion** | **PASS** | 0 coerced | 0 coerced | Unpopulated prices remain `NaN`. No `NaN` converted to `0.0`. |
| **9. Deterministic Rerunnability** | **PASS** | Identical | Identical | Script produces identical hash and row order upon repeated execution. |
| **10. Historical Changes Documented** | **PASS** | Documented | Documented | `GOLDTEN` listing on March 31, 2025 and 4-vs-5 contract regimes fully documented. |

---

## 3. Updated Normalized Price Distributions by Contract

Historical price per gram distribution across all 16,195 contract records:

| Symbol | Quotation Divisor ($D_s$) | Purity Fineness | Fine Factor ($F_s$) | Min Close / g (₹) | Median Close / g (₹) | Max Close / g (₹) | Min Fine / g (₹) | Median Fine / g (₹) | Max Fine / g (₹) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`GOLD`** | 10.0 | 995 | 0.995 | ₹6,011.80 | ₹9,789.90 | ₹24,791.70 | ₹6,042.01 | ₹9,839.10 | ₹24,916.28 |
| **`GOLDM`** | 10.0 | 995 | 0.995 | ₹6,117.00 | ₹12,485.20 | ₹19,866.10 | ₹6,147.74 | ₹12,547.94 | ₹19,965.93 |
| **`GOLDTEN`** | 10.0 | 999 | 0.999 | ₹8,731.60 | ₹14,766.80 | ₹20,551.60 | ₹8,740.34 | ₹14,781.58 | ₹20,572.17 |
| **`GOLDGUINEA`** | 8.0 | **999** | **0.999** | ₹6,178.50 | ₹10,806.81 | ₹21,414.75 | **₹6,184.68** | **₹10,817.63** | **₹21,436.19** |
| **`GOLDPETAL`** | 1.0 | 999 | 0.999 | ₹6,052.00 | ₹10,809.50 | ₹21,360.00 | ₹6,058.06 | ₹10,820.32 | ₹21,381.38 |

### Cross-Contract Pricing Alignment:
With `GOLDGUINEA` correctly configured as 999 purity:
1. **Median Fine Gold Alignment:** `GOLDGUINEA` median fine price (₹10,817.63/g) and `GOLDPETAL` median fine price (₹10,820.32/g) align within **₹2.69/g (~0.02%)** over the entire multi-year period.
2. **Latest Session Alignment (October 22, 2026):** Prompt `GOLDGUINEA` (expiring 2026-10-30) closed at **₹14,299.92/g** fine equivalent, and prompt `GOLDPETAL` (expiring on the same date) closed at **₹14,301.30/g** fine equivalent — a difference of just **₹1.38/g (0.009%)**.

---

## 4. Automated Test Suite Results

Test execution summary from `tests/test_normalization.py`:
```
Ran 8 tests in 2.549s

OK
```

### Verified Test Cases:
1. `test_quotation_divisors`: Confirmed $D_{\text{GOLD}}=10, D_{\text{GOLDM}}=10, D_{\text{GOLDTEN}}=10, D_{\text{GOLDGUINEA}}=8, D_{\text{GOLDPETAL}}=1$.
2. `test_fine_gold_factors`: Confirmed purity factors $0.995$ for GOLD/GOLDM and $0.999$ for GOLDTEN/GOLDGUINEA/GOLDPETAL.
3. `test_row_count_and_columns_preserved`: Confirmed exactly 16,195 rows, and verified all 28 original master columns remain identical.
4. `test_price_per_gram_math`: Confirmed `close_per_gram == close / quotation_divisor_grams` with $rtol \le 10^{-6}$.
5. `test_fine_gold_price_per_gram_math`: Confirmed `close_fine_per_gram == close_per_gram / fine_gold_factor` with $rtol \le 10^{-6}$.
6. `test_missing_ohlc_preservation`: Confirmed 1,985 missing values remain `NaN` and are never coerced to zero.
7. `test_no_duplicate_keys`: Confirmed zero duplicate keys on `(date, symbol, expiry_date)`.
8. `test_goldten_start_date`: Confirmed `GOLDTEN` start date is strictly preserved as `2025-03-31` with 2,048 records.

---

## 5. Deliverables & Acceptance Checklist

| Deliverable | File Path | Status |
| :--- | :--- | :---: |
| **Contract Specs Config** | `config/contract_specs.json` | **PASS (Updated with 999 GOLDGUINEA)** |
| **Normalization Pipeline** | `src/normalize_prices.py` | **PASS** |
| **Normalized Dataset** | `data/processed/mcx_gold_normalized.csv` | **PASS (Regenerated)** |
| **Automated Tests** | `tests/test_normalization.py` | **PASS (8/8 Passed)** |
| **Specification Report** | `reports/contract_specifications.md` | **PASS (Updated)** |
| **Validation Report** | `reports/normalization_validation.md` | **PASS (Updated)** |
| **Project Status** | `reports/PROJECT_STATUS.md` | **PASS (Updated)** |

---
*Phase 3 Correction is complete. Ready for ChatGPT review.*
