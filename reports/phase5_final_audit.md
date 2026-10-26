# Gold Contract Radar — MCX Commodity Derivatives Intelligence
## Phase 5: Final Audit and Reconciliation Report

**Date of Audit:** October 25, 2026  
**Auditor / Implementation Agent:** Antigravity IDE  
**Planning & Review Assistant:** ChatGPT  
**Target Event:** Hack in Hills '26  
**Module Audited:** `src/apply_liquidity_cost_filters.py`  
**Configuration Audited:** `config/liquidity_filters.json` (v1.0.0), `config/transaction_costs.json` (v1.0.1), `config/contract_specs.json`  
**Datasets Audited:**
- `data/processed/mcx_gold_liquidity_filtered_candidates.csv` (Output A)
- `data/processed/mcx_gold_transaction_cost_scenarios.csv` (Output B)
- `data/processed/mcx_gold_eligible_candidates.csv` (Output C)
- Upstream immutable datasets: `mcx_gold_master.csv`, `mcx_gold_normalized.csv`, `mcx_gold_relative_price_radar.csv`, `mcx_gold_term_structure.csv`, `mcx_gold_term_structure_snapshots.csv`

---

## Executive Audit Summary & Scorecard

A targeted, rigorous audit of the Phase 5 implementation, configurations, generated datasets, and test suites was conducted across six distinct evaluation dimensions. All audits have been executed against active code and on-disk files.

| Audit # | Audit Area / Requirement | Status | Summary of Findings |
| :---: | :--- | :---: | :--- |
| **Audit 1** | **Filter Counts & Funnel Reconciliation** | **PASS** | Reconciled independent pass counts vs sequential funnel. Explained why $40,784 > 35,190$. Verified $43,145 - 35,190 = 7,955$ exactly equals unavailable cost candidates. Confirmed final eligible candidate count (29,726) across all outputs. |
| **Audit 2** | **Independent Cost Recalculation** | **PASS** | Recomputed turnover, notional, integer-lot matching, statutory levies, and brokerage rules. Fixed spread-oriented entry/exit tax attribution defect. Reconciled unweighted per-gram mean (₹13.49/g) vs aggregate ratio of means (₹4.63/g). |
| **Audit 3** | **Fee Sources & Scenario Labels** | **PASS** | Verified official gazette/circular URLs, effective dates, and turnover bases for CTT, Stamp Duty, SEBI charge, MCX fee, and GST. Formally labeled `low` scenario as `HYPOTHETICAL_ASSUMPTION_BASED`. |
| **Audit 4** | **Quantity Matching & Spread Orientation** | **PASS** | Validated integer-lot LCM quantity matching covering all 5 contract products. Confirmed matched exposure is 100% equal in grams across both legs for all 43,145 candidates. Verified same-date matching and expiry rules. |
| **Audit 5** | **Modeled-Net Spread Interpretation** | **PASS** | Recalculated positive net spread counts across scenarios on eligible subset ($N = 29,726$). Documented non-executable boundaries: closing marks $\neq$ executable quotes; bid-ask spread and market impact unobserved. |
| **Audit 6** | **Regression & Data Integrity** | **PASS** | Executed complete repository test suite: **46/46 passed in 95.04s** (20 Phase 5 + 18 Phase 4 + 8 Phase 3). Confirmed 100% byte-for-byte immutability of Phase 1–4 outputs via SHA-256. |

---

## Audit 1: Filter Counts & Funnel Reconciliation

### 1.1 Independent Pass Counts vs Sequential Funnel Counts
The filtering architecture in `src/apply_liquidity_cost_filters.py` evaluates individual filter dimensions independently (marginal pass rates across all 43,145 rows) and then takes their intersection for joint eligibility (`is_all_filters_eligible = is_both_data_eligible & passes_expiry_filter & passes_liquidity_filter`).

#### A. Independent Marginal Pass Counts (Evaluated across all 43,145 screened candidates):
| Filter Condition | Metric Field Name | Total Passed | % of Total (43,145) | Radar Passed (9,059) | Calendar Passed (34,086) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Data Eligibility** | `is_both_data_eligible` | **35,190** | 81.56% | 8,903 (98.28%) | 26,287 (77.12%) |
| **Expiry & Maturity Filter** | `passes_expiry_filter` | **40,784** | 94.53% | 8,720 (96.26%) | 32,064 (94.07%) |
| **Traded Volume Threshold** | `passes_volume_filter` | **32,356** | 74.99% | 8,548 (94.36%) | 23,808 (69.85%) |
| **Open Interest Threshold** | `passes_open_interest_filter` | **32,293** | 74.85% | 8,513 (93.97%) | 23,780 (69.76%) |
| **Combined Liquidity Filter**| `passes_liquidity_filter` | **31,659** | 73.38% | 8,419 (92.94%) | 23,240 (68.18%) |
| **All Filters Eligible** | `is_all_filters_eligible` | **29,726** | **68.90%** | **8,136 (89.81%)** | **21,590 (63.34%)** |

#### B. Sequential Funnel Progression (Step-by-step attrition):
| Funnel Stage | Criteria Applied | Cumulative Remaining | Stage Retention (%) | Attrition from Previous Stage |
| :---: | :--- | :---: | :---: | :---: |
| **Stage 0** | Total Screened Candidate Universe | 43,145 | 100.00% | 0 |
| **Stage 1** | Stage 0 + Positive Traded Volume & Complete Session OHLC (`is_both_data_eligible`) | 35,190 | 81.56% | -7,955 (18.44%) |
| **Stage 2** | Stage 1 + Expiry & Tender Period ($DTE \ge 5$ days) (`passes_expiry_filter`) | 32,990 | 76.46% (93.75% of St. 1) | -2,200 (6.25%) |
| **Stage 3** | Stage 2 + Traded Volume Above Threshold (`passes_volume_filter`) | 30,313 | 70.26% (91.89% of St. 2) | -2,677 (8.11%) |
| **Stage 4** | Stage 3 + Open Interest Above Threshold (`passes_open_interest_filter`) | **29,726** | **68.90% (98.06% of St. 3)** | -587 (1.94%) |

### 1.2 Mathematical Explanation: Why Expiry-Pass Count (40,784) Exceeds Data-Eligible Count (35,190)
The expiry filter checks time-to-maturity calendar rules ($DTE \ge 5$, $DTE > 0$, and for calendar spreads $DTE_{\text{near}} < DTE_{\text{def}}$). This is a purely temporal condition that depends solely on contract trading dates and expiry dates.
In contrast, data eligibility checks actual market participation ($Volume > 0$, session $Open/High/Low/Close > 0$, and price validity).

In the MCX gold market, standard `GOLD` (1 kg) has far-deferred expiries extending 6 to 12 months forward (e.g. an October 2024 contract observed in January 2024). This pair has $DTE \approx 280$ days, which easily passes the expiry filter ($280 \ge 5$). However, because these far-deferred expiries often have zero trading volume, they fail data eligibility ($Volume = 0$).
Because `passes_expiry_filter` is evaluated independently across all 43,145 candidates without conditioning on volume, contracts with zero volume still pass the expiry filter. Thus, the independent expiry pass count ($40,784$) naturally exceeds the data-eligible count ($35,190$).

### 1.3 Exact Identity Reconciliation: 43,145 - 35,190 = 7,955 Unavailable Costs
- Total Screened Candidates: 43,145
- Total Data-Eligible Candidates: 35,190
- Difference: $43,145 - 35,190 = 7,955$ candidates.
- In `data/processed/mcx_gold_transaction_cost_scenarios.csv` (129,435 rows across 3 scenarios), exactly $7,955 \times 3 = 23,865$ rows have `cost_model_status == 'unavailable_zero_volume'` and `modeled_round_trip_cost_per_gram.isna()`.
- Set identity verification:
  $$\{ \text{candidate\_id} \in \text{Output A} \mid \neg \text{is\_both\_data\_eligible} \} \equiv \{ \text{candidate\_id} \in \text{Output B} \mid \text{cost\_model\_status} \neq \text{'available'} \}$$
  The set of non-data-eligible candidate IDs in Output A matches the set of unavailable cost candidate IDs in Output B **with 100% precision (0 mismatched IDs)**.

### 1.4 Complete Exclusion Reason Frequency Table
Every non-eligible candidate in Output A receives explicit, machine-readable exclusion reasons separated by semicolons:

| Exclusion Reason Code | Criteria Description | Occurrences | % of Total Candidates (43,145) |
| :--- | :--- | :---: | :---: |
| **`NONE`** | Passed all data, expiry, and liquidity filters (Fully Eligible) | **29,726** | **68.90%** |
| **`open_interest_below_threshold_leg_b`** | Leg B open interest < configured symbol threshold | 10,417 | 24.14% |
| **`volume_below_threshold_leg_b`** | Leg B volume < configured symbol threshold | 10,395 | 24.09% |
| **`incomplete_ohlc_leg_b`** | Leg B session OHLC incomplete / missing | 7,804 | 18.09% |
| **`zero_volume_leg_b`** | Leg B has zero traded volume | 7,804 | 18.09% |
| **`volume_below_threshold_leg_a`** | Leg A volume < configured symbol threshold | 3,006 | 6.97% |
| **`open_interest_below_threshold_leg_a`** | Leg A open interest < configured symbol threshold | 2,883 | 6.68% |
| **`insufficient_days_to_expiry`** | Contract in tender notice window ($0 < DTE < 5$) | 1,784 | 4.13% |
| **`incomplete_ohlc_leg_a`** | Leg A session OHLC incomplete / missing | 1,779 | 4.12% |
| **`zero_volume_leg_a`** | Leg A has zero traded volume | 1,779 | 4.12% |
| **`expired_or_expiry_day`** | Observation date on or after contract expiry ($DTE \le 0$) | 577 | 1.34% |

---

## Audit 2: Independent Transaction Cost Recalculation

### 2.1 Component-by-Component Statutory & Regulatory Fee Verification
All transaction cost formulas were audited against official exchange rules, circulars, and statutes:

1. **Exchange Notional / Turnover Calculation:**
   $$\text{Turnover}_{\text{leg}} = \text{Close}_{\text{quoted, per gram}} \times U_{\text{trading unit grams}} \times \text{Lots}$$
   - Verified: No fineness/purity adjustments are applied to turnover. Purity applies only to physical delivery DDR invoices, not to exchange transaction notional.
2. **Commodity Transaction Tax (CTT):**
   - Rate: $0.0100\%$ ($10$ bps / ₹1,000 per crore)
   - Basis: **Sell turnover only**. Buy transactions attract ₹0 CTT.
3. **Stamp Duty:**
   - Rate: $0.0020\%$ ($2$ bps / ₹200 per crore)
   - Basis: **Buy turnover only**. Sell transactions attract ₹0 Stamp Duty.
4. **Exchange Turnover Fee:**
   - Base Rate: $0.0021\%$ (₹210 per crore) applied to **total turnover (Buy + Sell)**.
5. **SEBI Turnover Charge:**
   - Rate: $0.0001\%$ (₹10 per crore) applied to **total turnover (Buy + Sell)**.
6. **Brokerage Models:**
   - `base`: $\min(₹20, 0.03\% \times \text{turnover})$ per executed order per leg.
   - `low`: $\min(₹10, 0.01\% \times \text{turnover})$ per executed order per leg.
   - `high`: $0.02\%$ ($2$ bps) of turnover per executed order per leg.
7. **Goods & Services Tax (GST):**
   - Rate: $18.0\%$ levied strictly on **service charges** ($\text{Brokerage} + \text{Exchange Fee} + \text{SEBI Fee}$).
   - Verified: CTT and Stamp Duty are statutory taxes and are **exempt from GST**.
8. **Round-Trip Totals:**
   - A round trip comprises 2 legs entering (1 Buy + 1 Sell) and 2 legs exiting (1 Sell + 1 Buy).
   - Total round-trip cost = $\text{Entry Cost} + \text{Exit Cost}$.

### 2.2 Spread-Oriented Entry/Exit Tax Attribution Defect & Correction
- **Defect Discovered:** An earlier draft of the transaction cost engine attributed Stamp Duty to the entry of both legs and CTT to the exit of both legs, implicitly treating both legs as long positions (outright purchases) entering simultaneously and exiting simultaneously.
- **Economic Reality of Spread Trading:** A relative-price spread or calendar spread is a long-short position. At entry, one leg is bought and the other leg is sold. At exit, the positions are reversed:
  - For Calendar Spreads: The nearer leg (Leg A) is sold at entry (attracts CTT @ 0.01%) and bought at exit (attracts Stamp Duty @ 0.002%); the deferred leg (Leg B) is bought at entry (attracts Stamp Duty @ 0.002%) and sold at exit (attracts CTT @ 0.01%).
  - For Cross-Product Spreads: The overpriced leg is sold at entry (CTT) and bought at exit (Stamp Duty); the underpriced leg is bought at entry (Stamp Duty) and sold at exit (CTT).
- **Correction Made:** Updated vectorized entry/exit attribution in `src/apply_liquidity_cost_filters.py`. Entry cost and exit cost are now balanced (~₹1,135 entry and ~₹1,135 exit for 1 kg GOLD, matching the simultaneous buy+sell structure). Total round-trip cost is mathematically preserved, but leg-level and side-level accounting is now fully authentic.

### 2.3 Independent Recalculation Results (Sample Benchmarks across all 5 Products):
Using `scripts/audit_independent_cost_check.py`, modeled costs in Output B were checked against independent manual scratch calculations:

| Candidate ID | Symbols & Lots | Matched Grams | Notional (Leg A / Leg B) | Modeled Base Cost | Independent Manual Cost | Absolute Difference |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `RADAR_...` | `GOLD` (1 lot) vs `GOLDM` (10 lots) | 1,000g | ₹63.32L / ₹63.30L | ₹2,271.20 | ₹2,271.20 | **0.000036 (PASS)** |
| `RADAR_...` | `GOLDM` (1 lot) vs `GOLDPETAL` (100 lots) | 100g | ₹6.91L / ₹6.93L | ₹332.37 | ₹332.37 | **0.000045 (PASS)** |
| `RADAR_...` | `GOLDGUINEA` (1 lot) vs `GOLDPETAL` (8 lots)| 8g | ₹51.06k / ₹49.78k | ₹88.74 | ₹88.74 | **0.000028 (PASS)** |
| `RADAR_...` | `GOLDGUINEA` (5 lots) vs `GOLDTEN` (4 lots) | 40g | ₹3.64L / ₹3.63L | ₹219.43 | ₹219.43 | **0.000001 (PASS)** |
| `RADAR_...` | `GOLDPETAL` (10 lots) vs `GOLDTEN` (1 lot) | 10g | ₹91.52k / ₹90.74k | ₹125.73 | ₹125.73 | **0.000020 (PASS)** |
| `CAL_...` | `GOLDTEN` Near (1 lot) vs Def (1 lot) | 10g | ₹90.74k / ₹91.10k | ₹125.66 | ₹125.66 | **0.000029 (PASS)** |

### 2.4 Reconciliation of Per-Gram Means vs Ratio of Aggregate Means
In `reports/liquidity_cost_filter_validation.md`, the reported base scenario mean round-trip cost per gram across eligible candidates is **₹13.49/g**, whereas the ratio of aggregate mean cost to aggregate mean exposure is **₹4.63/g**.

The audit verified why these two metrics differ and confirmed that both are mathematically correct:
1. **Unweighted Candidate-Level Mean ($\frac{1}{N}\sum \frac{\text{Cost}_i}{\text{Grams}_i}$):**
   - Each screened pair receives equal weight ($1/N$).
   - For micro-denomination contracts like `GOLDPETAL` (1g) and `GOLDGUINEA` (8g), the flat brokerage minimum (₹20 per order per leg $\times$ 4 order legs = ₹80 flat) represents a large fixed friction per gram (~₹12.50/g).
   - Because micro-contracts account for over 85% of eligible rows, the unweighted arithmetic mean is **₹13.4858/g** (Base), **₹7.8292/g** (Low), and **₹16.9768/g** (High).
2. **Ratio of Aggregate Means ($\frac{\sum \text{Cost}_i}{\sum \text{Grams}_i}$):**
   - In contrast, weighting by total physical grams assigns high weight to large contracts (`GOLD` 1,000g and `GOLDM` 100g).
   - Standard 1 kg `GOLD` has a low round-trip friction of only ~₹2.27/g.
   - Summing all costs across the 29,726 candidates (₹16.58M) and dividing by total matched grams (3.58M grams) yields **₹4.6269/g** (Base), **₹3.9600/g** (Low), and **₹15.1809/g** (High).

---

## Audit 3: Fee Sources, Statutory Rates & Scenario Labels

### 3.1 Verified Statutory Fee Schedule
Every fee rate in `config/transaction_costs.json` was traced to its statutory authority and verified for temporal applicability across the historical dataset (2024–2026):

| Fee Component | Verified Rate | Applicable Side | Charge Turnover Base | Statutory Authority / Act | Relevant Effective Date | Official Source URL / Reference |
| :--- | :---: | :---: | :---: | :--- | :---: | :--- |
| **Commodity Transaction Tax (CTT)** | 0.0100% (₹1,000/Cr) | Sell only | Sell Turnover | Finance Act 2013 (Ch. VII, Sec. 116) | 2013-07-01 | [Income Tax India Finance Act 2013](https://www.incometaxindia.gov.in/Acts/Finance%20Acts/2013/102120000000037142.htm) |
| **Stamp Duty** | 0.0020% (₹200/Cr) | Buy only | Buy Turnover | Indian Stamp Act, 1899 (Finance Act 2019 amendment) | 2020-07-01 | [Department of Financial Services Stamp Rules](https://financialservices.gov.in/sites/default/files/Indian%20Stamp%20Rules%202019.pdf) |
| **SEBI Turnover Charge** | 0.0001% (₹10/Cr) | Both | Total Turnover | SEBI (Stock Brokers) Regulations, 1992 | 2016-09-28 | [SEBI Turnover Fee Circular](https://www.sebi.gov.in/legal/circulars/sep-2016/turnover-fee-for-commodity-derivatives_33423.html) |
| **MCX Base Fee** | 0.0021% (₹210/Cr) | Both | Total Turnover | MCX Transaction Tariff Schedule | 2023-10-01 | [MCX Transaction Charges Circular](https://www.mcxindia.com/membership/notice-circulars/circular-details/transaction-charges-on-futures-contracts) |
| **Goods & Services Tax (GST)** | 18.00% | Both | Service Charges (Brokerage + Exch + SEBI) | Central Goods and Services Tax Act, 2017 | 2017-07-01 | [CBIC GST Portal](https://cbic-gst.gov.in/) |

### 3.2 Participant Scenario Labels & Boundaries
- **Base Scenario:** Labeled `VERIFIED_STATUTORY_WITH_BENCHMARK_BROKERAGE`. Reflects standard retail discount brokerage tariffs (₹20/order) and verified MCX base transaction fee slabs.
- **Low Scenario:** Labeled `HYPOTHETICAL_ASSUMPTION_BASED`. Explicitly models hypothetical exchange volume rebate tiers (for proprietary desks generating >₹1,500 Cr ADT) and negotiated institutional brokerage (₹10/order). It is clearly stated that this is **not an automatic entitlement** for general market participants.
- **High Scenario:** Labeled `ASSUMPTION_BASED_WITH_VERIFIED_STATUTORY_RATES`. Models full-service retail broker tariffs (0.02% of turnover) and standard top-tier exchange fees.

---

## Audit 4: Quantity Matching & Spread Orientation

### 4.1 Verification of Product Specifications
Specifications from `config/contract_specs.json` were cross-checked against official MCX contract specifications:

| Product Symbol | Display Name | Trading Unit | Quotation Unit | Quotation Divisor | Fine Gold Factor | Physical Delivery Unit |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **`GOLD`** | Gold Standard Futures | 1,000g (1 kg) | ₹ per 10 grams | 10.0 | 0.995 (995 fineness) | 1 kg bar |
| **`GOLDM`** | Gold Mini Futures | 100g | ₹ per 10 grams | 10.0 | 0.995 (995 fineness) | 100g bar |
| **`GOLDGUINEA`** | Gold Guinea Futures | 8g | ₹ per 8 grams | 8.0 | 0.999 (999 fineness) | 8g coin |
| **`GOLDPETAL`** | Gold Petal Futures | 1g | ₹ per 1 gram | 1.0 | 0.999 (999 fineness) | 1g coin |
| **`GOLDTEN`** | Gold Ten Futures | 10g | ₹ per 10 grams | 10.0 | 0.995 (995 fineness) | 10g bar |

### 4.2 Representative Cross-Product & Calendar Bundles
Exposure matching requires that the underlying grams transacted on Leg A strictly equal the underlying grams transacted on Leg B:

| Strategy / Pair | Leg A Contract | Leg B Contract | Integer Lots (A : B) | Matched Grams | Exposure Match Check |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Cross-Product** | `GOLD` (1,000g) | `GOLDM` (100g) | 1 : 10 | 1,000g | **1,000g == 1,000g (EXACT)** |
| **Cross-Product** | `GOLDGUINEA` (8g) | `GOLDPETAL` (1g) | 1 : 8 | 8g | **8g == 8g (EXACT)** |
| **Cross-Product** | `GOLDGUINEA` (8g) | `GOLDTEN` (10g) | 5 : 4 | 40g | **40g == 40g (EXACT)** |
| **Cross-Product** | `GOLDPETAL` (1g) | `GOLDTEN` (10g) | 10 : 1 | 10g | **10g == 10g (EXACT)** |
| **Cross-Product** | `GOLDM` (100g) | `GOLDPETAL` (1g) | 1 : 100 | 100g | **100g == 100g (EXACT)** |
| **Cross-Product** | `GOLDGUINEA` (8g) | `GOLDM` (100g) | 25 : 2 | 200g | **200g == 200g (EXACT)** |
| **Calendar Spread**| Nearer `GOLD` (1,000g) | Deferred `GOLD` (1,000g) | 1 : 1 | 1,000g | **1,000g == 1,000g (EXACT)** |
| **Calendar Spread**| Nearer `GOLDPETAL` (1g)| Deferred `GOLDPETAL` (1g)| 1 : 1 | 1g | **1g == 1g (EXACT)** |

Across all 43,145 candidates in Output A and Output B, `exposure_grams_leg_a == exposure_grams_leg_b` was verified for **100% of rows**.

---

## Audit 5: Modeled-Net Spread Interpretation & Non-Executable Boundaries

### 5.1 Sensitivity Analysis Across Scenarios
For candidate evaluation, the gross spread between normalized prices is compared against modeled round-trip costs per gram:

$$\text{Modeled Net Spread per Gram} = |\text{Gross Spread per Gram}| - \text{Modeled Round-Trip Cost per Gram}$$

#### Recalculated Counts on Trade-Eligible Candidates Subset ($N = 29,726$ in Output C):
| Cost Scenario | Mean Round-Trip Cost (₹ per candidate) | Mean Round-Trip Cost (₹ per gram) | Candidates Where Gross Spread > Modeled Cost | % of Eligible Candidates ($N = 29,726$) |
| :--- | :---: | :---: | :---: | :---: |
| **Low** (Institutional Rebate) | ₹477.30 | ₹7.83 / g | **28,661** | **96.42%** |
| **Base** (Discount Broker Benchmark) | ₹557.68 | ₹13.49 / g | **28,239** | **94.99%** |
| **High** (Full-Service Retail) | ₹1,829.77 | ₹16.98 / g | **27,611** | **92.89%** |

### 5.2 Strict Boundaries & Non-Executability Disclaimers
A positive modeled net spread does **NOT** indicate a risk-free arbitrage opportunity or executable profit for the following structural reasons:
1. **Closing Reference Marks vs Synchronized Quotes:** Prices are end-of-day official settlement marks from daily bhavcopies. They do not represent simultaneous fill prices across both legs.
2. **Unobserved Bid-Ask Spread:** Entering and exiting positions requires crossing the bid-ask spread on both legs. In deferred and illiquid contracts, the bid-ask spread can easily exceed ₹10–₹20/g.
3. **Unobserved Market Impact:** Executing large integer-lot bundles (e.g. 100 lots of `GOLDPETAL` or 25 lots of `GOLDGUINEA`) would cause substantial market impact in the order book.
4. **Physical Delivery Non-Fungibility:** Cross-product contracts have different delivery fineness (995 bars vs 999 coins) and delivery locations. They cannot be physically exchanged to close out an arbitrage.

---

## Audit 6: Regression, Test Suite Results & Data Integrity

### 6.1 Automated Test Suite Execution
The automated test suite was executed across all test modules in the repository:
```bash
python -m unittest discover tests
```
**Execution Outcome:**
```text
Ran 46 tests in 95.042s

OK
```
All 46 unit tests passed:
- `tests/test_liquidity_cost_filters.py` (20 Phase 5 tests) — **20/20 PASS**
- `tests/test_relative_price_radar.py` (18 Phase 4 regression tests) — **18/18 PASS**
- `tests/test_normalization.py` (8 Phase 3 regression tests) — **8/8 PASS**

### 6.2 Full 64-Character SHA-256 Hash Inventory & Immutability Verification
All raw files and upstream processed datasets were verified byte-for-byte unchanged:

| File Path | Phase Origin | File Size (Bytes) | Exact Full SHA-256 Hash | Integrity Status |
| :--- | :---: | :---: | :--- | :---: |
| `reports/file_inventory.csv` | Phase 1 | 56,742 | `00155a0245084ceb044d081bc26c9fa12db264c8ffcf86bf8f4f6cff932782e4` | **VERIFIED (165 raw CSVs match inventory)** |
| `data/processed/mcx_gold_master.csv` | Phase 2 | 4,828,791 | `ac57299101fef7092ae956dc35fa9e9f15d9e8a195a340621ddd245f3f510088` | **IMMUTABLE (100% byte-identical)** |
| `data/processed/mcx_gold_normalized.csv` | Phase 3 | 7,127,915 | `26c57ce9ad54f271875e816ce865ef0121adadbe517136289494a8bae48c2020` | **IMMUTABLE (100% byte-identical)** |
| `data/processed/mcx_gold_relative_price_radar.csv` | Phase 4 | 3,724,677 | `38f13aeddb2454f928ae5a043319b525c01d198283be0e050f292d8efa2386c4` | **IMMUTABLE (100% byte-identical)** |
| `data/processed/mcx_gold_term_structure.csv` | Phase 4 | 12,837,972 | `d81102755b7f1b85766ea699a99dc1c6f998eaf50b034c2924d1bf133fac6201` | **IMMUTABLE (100% byte-identical)** |
| `data/processed/mcx_gold_term_structure_snapshots.csv`| Phase 4 | 2,647,180 | `f064bf4e75ff6791b1839f4b8152cabf51d99478ecf310b6696a0aefb3120037` | **IMMUTABLE (100% byte-identical)** |
| `data/processed/mcx_gold_liquidity_filtered_candidates.csv`| Phase 5 (Output A) | 28,713,069 | `b2385ab75c9f0a2d6a65f6da580725b8979f6834e433042df5f9c51d4efac135` | **VERIFIED (43,145 rows, 48 cols)** |
| `data/processed/mcx_gold_transaction_cost_scenarios.csv` | Phase 5 (Output B) | 35,850,688 | `1f58b74593db05e5a521f289870ac0368a06f14963e0676ed20d90f4e5c9158a` | **VERIFIED (129,435 rows, 31 cols)** |
| `data/processed/mcx_gold_eligible_candidates.csv` | Phase 5 (Output C) | 19,027,212 | `774b872b9aae45d06129c970f70f852e2efdb0f1ba6358381af19cb34b6fa22f` | **VERIFIED (29,726 rows, 48 cols)** |

---

## 7. Remaining Limitations

1. **Intraday Liquidity Dynamics:** The filtering engine uses daily aggregated volume and open interest. Intraday liquidity drying up during market stress cannot be captured without tick-level order book data.
2. **Margin Financing & Roll Yield Dynamics:** Margin carrying costs and calendar roll policies are not yet modeled; they form the core objective of Phase 6.
3. **Execution Routing & Partial Fills:** Fills are modeled as binary (either complete or unexecuted); partial order fills are unobserved in bhavcopy data.

---

## 8. Final Audit Sign-Off

The Phase 5 Liquidity and Transaction Cost Filters engine, datasets, test fixtures, and documentation are **100% audited, reconciled, and verified**.

Phase 5 is complete and ready for final review and sign-off. **Phase 6 has not been started.**
