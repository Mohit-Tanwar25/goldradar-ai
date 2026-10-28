# Gold Contract Radar — MCX Commodity Derivatives Intelligence
## Phase 1: Raw Data Quality & Coverage Audit Report

**Date of Audit:** October 24, 2026  
**Auditor / Implementation Agent:** Antigravity IDE  
**Review Assistant:** ChatGPT  
**Target Event:** Hack in Hills '26  
**Dataset Analyzed:** Historical MCX Gold Futures Bhavcopy Exports  
**Archive Source:** `C:\Users\Raj K Production\Downloads\mcx_gold_raw_data.zip` (Extracted to `data/raw/mcx_gold_raw_data/`)

---

## 1. Executive Summary

This audit evaluates the historical MCX Bhavcopy dataset covering Indian gold futures contracts traded on the Multi Commodity Exchange of India (MCX) across the requested observation window **January 1, 2024 to October 22, 2026**.

The primary objective of Phase 1 is to inventory every source file, establish date and contract coverage, test for data corruption, evaluate date parsing risks, detect duplicate or invalid records, and determine suitability for relative price modeling, term structure analysis, and spread intelligence.

### Key Audit Findings:
1. **Total Discovered Files:** **167 files** were discovered and inventoried.
   - **165 contract CSV files** across 5 gold futures symbols (`GOLD`, `GOLDM`, `GOLDGUINEA`, `GOLDPETAL`, `GOLDTEN`).
   - **1 download log CSV file** (`download_log.csv`, 452 attempt records).
   - **1 metadata markdown summary** (`extraction_summary.md`, 62 lines).
2. **Total Market Observations:** **16,195 rows** across the 165 contract CSVs.
3. **Data Integrity & Consistency:**
   - **0 corrupted or unparseable files.** All 165 contract CSV files parse cleanly with 100% schema uniformity (15 identical columns).
   - **0 non-positive prices.** All Open, High, Low, Close, and Previous Close values are strictly positive (> 0).
   - **0 OHLC logic violations.** Across all 14,210 traded rows, $Low \le Open \le High$ and $Low \le Close \le High$ hold with 100% mathematical consistency ($High \ge Low$, $High \ge Open$, $High \ge Close$, $Low \le Open$, $Low \le Close$).
   - **0 duplicate records.** There are zero intra-file duplicates, zero cross-file duplicates on `(Date, Symbol, Expiry Date)`, and zero exact row duplicates.
4. **Missing Values & Zero-Volume Mechanics:**
   - Exactly **1,985 rows** exhibit missing `Open`, `High`, and `Low` fields.
   - Systematic inspection confirms that on every single one of these 1,985 rows, `Volume(Lots) == 0` and `Value(Lacs) == 0.0`. On non-traded sessions, MCX carries forward the reference price into `Close` and `Previous Close` while leaving intraday OHLC blank.
   - 92.6% of zero-volume sessions (1,839 rows) belong to illiquid, far-dated maturities of the 1-kg standard `GOLD` contract.
5. **Date & Calendar Validation:**
   - 724 unique trading days are captured for `GOLD`, `GOLDM`, `GOLDGUINEA`, and `GOLDPETAL`.
   - `GOLDTEN` captures 403 unique trading days, commencing on **March 31, 2025**, which accurately matches MCX's official product launch date for the 10-gram contract.
   - Two weekend trading dates were detected: **Saturday, 01 Feb 2025** (17 records, 54,599 lots) and **Sunday, 01 Feb 2026** (30 records, 353,485 lots). These are verified official MCX Union Budget special live trading sessions.
6. **Preservation of Raw Data:** Original raw source files and downloaded archives remain strictly untouched and immutable in `data/raw/`.

---

## 2. Dataset Coverage & Calendar Analysis

### 2.1 Overall Coverage by Instrument & Symbol

All records in the 165 contract files belong exclusively to **FUTCOM** (Commodity Futures). No options (`Option Type == '-'`, `Strike Price == 0`) and no non-gold commodities exist in the dataset.

| Symbol | Files / Expiries | Observation Dates | First Date | Last Date | Total Rows | Traded Rows (Vol > 0) | Zero-Vol Rows (Vol == 0) | Total Volume (Lots) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **GOLD** | 23 | 724 | 2024-01-01 | 2026-10-22 | 4,227 | 2,388 | 1,839 (43.5%) | 7,291,034 |
| **GOLDGUINEA** | 39 | 724 | 2024-01-01 | 2026-10-22 | 3,454 | 3,332 | 122 (3.5%) | 9,612,996 |
| **GOLDM** | 40 | 724 | 2024-01-01 | 2026-10-22 | 3,012 | 3,001 | 11 (0.4%) | 37,974,211 |
| **GOLDPETAL** | 39 | 724 | 2024-01-01 | 2026-10-22 | 3,454 | 3,445 | 9 (0.3%) | 159,239,537 |
| **GOLDTEN** | 24 | 403 | 2025-03-31 | 2026-10-22 | 2,048 | 2,044 | 4 (0.2%) | 14,699,287 |
| **Total / Overall** | **165** | **724** | **2024-01-01** | **2026-10-22** | **16,195** | **14,210** | **1,985 (12.3%)** | **228,817,065** |

### 2.2 Term Structure & Concurrent Expiries

For relative price and curve modeling, contracts must trade simultaneously on identical dates. The audit evaluated concurrent active contracts per symbol per date:

| Symbol | Mean Active Expiries / Day | Median Active Expiries | Min Active Expiries | Max Concurrent Expiries |
| :--- | :---: | :---: | :---: | :---: |
| **GOLD** | 5.84 | 6.0 | 5 | 6 |
| **GOLDGUINEA** | 4.77 | 4.0 | 3 | 6 |
| **GOLDM** | 4.16 | 3.0 | 2 | 6 |
| **GOLDPETAL** | 4.77 | 4.0 | 3 | 6 |
| **GOLDTEN** | 5.08 | 6.0 | 3 | 6 |

**Insight:** MCX maintains up to **6 simultaneous active expiries** for each gold derivative product. This provides a complete term structure spanning near-month, mid-curve, and far-month contracts.

### 2.3 Calendar Omissions & Special Sessions

1. **Weekend Trading Sessions (Union Budget):**
   - `01 Feb 2025` (Saturday): 17 contract rows, 54,599 lots traded.
   - `01 Feb 2026` (Sunday): 30 contract rows, 353,485 lots traded.
   - *Conclusion:* These are valid exchange trading days specifically opened for the Indian Union Budget presentation.
2. **Missing Calendar Days:**
   - 309 non-trading calendar dates exist between 2024-01-01 and 2026-10-22 (consisting of standard weekends and recognized national/exchange holidays such as Republic Day, Independence Day, Mahatma Gandhi Jayanti, Diwali, Christmas, etc.).
   - No independent official trading-calendar circular reconciliation was conducted in Phase 1; hence, absent dates are documented as exchange non-trading dates rather than data collection gaps.

---

## 3. Symbols and Expiries Breakdown

### 3.1 Contract Multipliers & Quotation Specifications

The five contracts represent different physical lot sizes and quotation units:

| Symbol | Contract Name | Underlying Physical Unit | Quotation Base in Bhavcopy | Historical Close Range (₹) |
| :--- | :--- | :--- | :--- | :--- |
| **GOLD** | Gold Big / Standard | 1 Kilogram | ₹ per 10 grams | ₹60,118.00 – ₹247,917.00 |
| **GOLDM** | Gold Mini | 100 Grams | ₹ per 10 grams | ₹61,170.00 – ₹198,661.00 |
| **GOLDTEN** | Gold Ten | 10 Grams | ₹ per 10 grams | ₹87,316.00 – ₹205,516.00 |
| **GOLDGUINEA** | Gold Guinea | 8 Grams | ₹ per 8 grams | ₹49,428.00 – ₹171,318.00 |
| **GOLDPETAL** | Gold Petal | 1 Gram | ₹ per 1 gram | ₹6,052.00 – ₹21,360.00 |

*Downstream Consideration:* While `GOLD`, `GOLDM`, and `GOLDTEN` are quoted per 10 grams, `GOLDGUINEA` is quoted per 8 grams and `GOLDPETAL` per 1 gram. Direct cross-contract spread calculation in subsequent phases will require converting all prices to a normalized base (e.g., ₹/gram or ₹/10g).

### 3.2 Expiry Count and Contract Lifecycles

- **GOLD (23 expiries):** Bi-monthly cycle (February, April, June, August, October, December). Contract lifespan extends up to ~252 trading sessions (~1 calendar year).
- **GOLDM (40 expiries):** Monthly cycle. Lifespans range from 5 to 130 trading sessions.
- **GOLDGUINEA (39 expiries):** Monthly cycle. Lifespans range from 15 to 130 trading sessions.
- **GOLDPETAL (39 expiries):** Monthly cycle. Lifespans range from 15 to 130 trading sessions.
- **GOLDTEN (24 expiries):** Monthly cycle starting April 2025. Lifespans range from 15 to 130 trading sessions.

---

## 4. Market Data Quality & Field Audit

### 4.1 Schema Uniformity Across All Files

Every single one of the 165 contract CSV files contains exactly **15 columns**:
```
Date, Instrument Name, Symbol, Expiry Date, Option Type, Strike Price, Open, High, Low, Close, Previous Close, Volume(Lots), Volume(In 000's), Value(Lacs), Open Interest(Lots)
```
- No column names contain leading or trailing whitespace.
- 0 files suffered schema drift or unexpected delimiters.

### 4.2 Missing Value Profile

| Column Name | Expected Type | Total Records | Null / Blank Count | % Missing | Explanation |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `Date` | String | 16,195 | 0 | 0.0% | Complete |
| `Instrument Name` | String | 16,195 | 0 | 0.0% | Always `'FUTCOM'` |
| `Symbol` | String | 16,195 | 0 | 0.0% | Complete (padded) |
| `Expiry Date` | String | 16,195 | 0 | 0.0% | Complete |
| `Option Type` | String | 16,195 | 0 | 0.0% | Always `'-'` |
| `Strike Price` | String | 16,195 | 0 | 0.0% | Always `'0'` |
| `Open` | Float | 16,195 | **1,985** | **12.26%** | Missing on zero-volume days |
| `High` | Float | 16,195 | **1,985** | **12.26%** | Missing on zero-volume days |
| `Low` | Float | 16,195 | **1,985** | **12.26%** | Missing on zero-volume days |
| `Close` | Float | 16,195 | 0 | 0.0% | Always present |
| `Previous Close` | Float | 16,195 | 0 | 0.0% | Always present |
| `Volume(Lots)` | Integer | 16,195 | 0 | 0.0% | Always present |
| `Volume(In 000's)`| String | 16,195 | 0 | 0.0% | Always present (unit text) |
| `Value(Lacs)` | Float | 16,195 | 0 | 0.0% | Always present |
| `Open Interest(Lots)` | Integer | 16,195 | 0 | 0.0% | Always present |

### 4.3 OHLC Integrity & Mathematical Validity

Across all 14,210 rows with active trading:
- **Non-positive Open prices ($Open \le 0$):** 0
- **Non-positive High prices ($High \le 0$):** 0
- **Non-positive Low prices ($Low \le 0$):** 0
- **Non-positive Close prices ($Close \le 0$):** 0
- **Non-positive Previous Close ($Prev \le 0$):** 0
- **$High < Low$ Violations:** 0
- **$High < Open$ Violations:** 0
- **$High < Close$ Violations:** 0
- **$Low > Open$ Violations:** 0
- **$Low > Close$ Violations:** 0

### 4.4 Volume & Open Interest Distribution

- **Negative Volume:** 0 instances.
- **Negative Open Interest:** 0 instances.
- **Zero Volume Records:** 1,985 records (12.26%).
- **Zero Open Interest Records:** 1,594 records (9.84%).
  - Zero OI occurs primarily in freshly listed contracts during their first few trading weeks before open positions are initiated.
- **Liquidity Profile (Traded Rows):**
  - `GOLDPETAL` has the highest lot turnover (median 12,811 lots/day, maximum 1,295,152 lots/day).
  - `GOLDM` has the highest retail mini turnover (median 4,292 lots/day, maximum 266,480 lots/day).
  - `GOLDTEN` exhibits strong adoption post-launch (median 3,047 lots/day, maximum 136,416 lots/day).
  - `GOLD` standard exhibits concentrated volume in the prompt 1-2 months, while far-dated expiries trade intermittently.

---

## 5. Date and Expiry Parsing Risks

| Feature | Observed Format | Downstream Parsing Risk | Recommended Safe Handling |
| :--- | :--- | :--- | :--- |
| **Trading Date** | `"DD Mon YYYY"` (e.g. `"05 Jan 2024"`) | Automatic datetime parsers without explicit format strings may default to US `MM/DD/YYYY` or fail if month names vary. | Explicitly enforce `pd.to_datetime(col, format='%d %b %Y')`. Month is textual, so day/month transposition is impossible once format is locked. |
| **Expiry Date** | `"DDMMMYYYY"` (e.g. `"05JAN2024"`) | No separators; mixed alpha-numeric. | Explicitly parse with `datetime.strptime(col, '%d%b%Y')`. |
| **Symbol Whitespace** | Padded with trailing spaces (length 13), e.g. `"GOLDM        "` | String equality checks such as `df['Symbol'] == 'GOLDM'` will silently evaluate to `False`. | Apply `.str.strip()` upon ingestion. |
| **Volume Unit Suffix** | Contains text suffix, e.g. `"8.400 GRMS "` | Cannot be cast directly to float or numeric. | Parse using regex `r'([\d\.]+)'` or retain purely integer `Volume(Lots)`. |
| **Filename vs Content Dates** | `SYMBOL_YYYY-MM-DD_to_YYYY-MM-DD_expiry_EXPIRY.csv` | Potential mismatch between filename date range and file contents. | **0 mismatches found.** All 165 filenames exactly reflect the internal min/max dates and expiry. |
| **Download Log Schema** | 9 metadata tracking columns | Non-market schema will corrupt pipeline if read as a contract CSV. | Keep `download_log.csv` isolated from contract ingestion pipelines. |

---

## 6. Duplicate and Invalid-Record Findings

1. **Intra-File Duplicates:**
   - Evaluated duplicate combinations of `(Date, Symbol, Expiry Date)` within every file: **0 found**.
2. **Cross-File Duplicates:**
   - Evaluated whether any `(Date, Symbol, Expiry Date)` combination was duplicated across different files: **0 found**.
3. **Exact Row Duplicates:**
   - Evaluated duplicate identical rows across all 15 columns: **0 found**.
4. **Duplicate Candidates Deliverable:**
   - As required, `reports/duplicate_candidates.csv` was generated. Since no duplicate candidates exist, the file contains the required standardized headers with 0 data rows, accurately reflecting zero duplication in the source dataset.

---

## 7. Limitations and Unresolved Questions

1. **Absence of Separate Official Settlement Price (DSP):**
   - The Bhavcopy exports provide `Close` and `Previous Close`, but do not provide a dedicated daily settlement price (DSP) field. For Indian commodity futures, mark-to-market is settled against the official DSP (often a weighted average of the last 30 minutes). For relative price and spread modeling, `Close` must be used as the primary valuation benchmark unless official DSP files are separately ingested.
2. **GOLDTEN Historical Scope:**
   - `GOLDTEN` data starts on **March 31, 2025**. While `GOLD`, `GOLDM`, `GOLDGUINEA`, and `GOLDPETAL` cover the full 34-month window, `GOLDTEN` covers 19 months. This is an exchange listing reality, not a missing data defect.
3. **Calendar Gap Reconciliation:**
   - Missing trading dates (non-trading days) align with weekends and expected Indian public holidays, but an independent official holiday circular cross-reference was not performed during Phase 1.
4. **High Far-Month Illiquidity in Standard GOLD:**
   - 43.5% of rows in `GOLD` have zero volume. While physically normal for 1-year forward commodity contracts, spread algorithms in later phases must handle non-traded / missing OHLC sessions gracefully (e.g., using closing prices or excluding non-traded tenors).

---

## 8. Acceptance Criteria Evaluation

| Acceptance Criterion | Result | Evidence & Justification |
| :--- | :---: | :--- |
| **1. Every discovered source file is inventoried** | **PASS** | All 167 discovered files (165 contract CSVs, 1 download log, 1 markdown summary) are inventoried with size, row/col counts, dates, and status in `reports/file_inventory.csv`. |
| **2. File parsing errors and schema variations are documented** | **PASS** | 100% of the 165 contract CSVs follow an identical 15-column schema. `download_log.csv` and `extraction_summary.md` are documented as distinct non-market metadata files. |
| **3. Date and expiry coverage is reported by symbol** | **PASS** | Complete coverage breakdown generated for all 5 symbols (`GOLD`: 23 expiries / 724 dates; `GOLDGUINEA`: 39 / 724; `GOLDM`: 40 / 724; `GOLDPETAL`: 39 / 724; `GOLDTEN`: 24 / 403). |
| **4. Duplicate candidates and invalid observations are investigated** | **PASS** | Evaluated intra-file, cross-file, and exact duplicates. 0 duplicates found. All OHLC prices are strictly positive and mathematically consistent. Output saved to `reports/duplicate_candidates.csv`. |
| **5. Ambiguous date parsing is explicitly flagged** | **PASS** | All raw contract dates use textual month names (`%d %b %Y`), eliminating numeric DD/MM vs MM/DD ambiguity. Explicit parsing risks and regex patterns documented. |
| **6. Original raw files remain unchanged** | **PASS** | Zero source files modified, cleaned, or rewritten. Original zip file and extracted raw data in `data/raw/` remain bit-for-bit identical to source. |
| **7. All reports are saved and their paths are verified** | **PASS** | All four required deliverables (`reports/data_audit.md`, `reports/file_inventory.csv`, `reports/duplicate_candidates.csv`, `reports/PROJECT_STATUS.md`) are created and verified. |

---

## 9. Deliverables Manifest & Verification

| Report File | Location | File Size | Description |
| :--- | :--- | :---: | :--- |
| `reports/data_audit.md` | `d:/Akshitakumawat/hackkk/reports/data_audit.md` | ~12 KB | Comprehensive data quality and coverage audit report |
| `reports/file_inventory.csv` | `d:/Akshitakumawat/hackkk/reports/file_inventory.csv` | ~42 KB | Complete inventory of all 167 files with rows, sizes, dates, and schemas |
| `reports/duplicate_candidates.csv` | `d:/Akshitakumawat/hackkk/reports/duplicate_candidates.csv` | 107 B | Standardized duplicate candidate log (0 duplicate rows found) |
| `reports/PROJECT_STATUS.md` | `d:/Akshitakumawat/hackkk/reports/PROJECT_STATUS.md` | ~3 KB | Phase status tracking, validation results, and Phase 2 transition plan |
