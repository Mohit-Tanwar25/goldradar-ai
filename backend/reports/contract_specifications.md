# Gold Contract Radar — MCX Commodity Derivatives Intelligence
## Phase 3: Official MCX Contract Specifications & Normalization Methodology (Corrected)

**Date of Audit & Specification:** October 24, 2026  
**Implementation Agent:** Antigravity IDE  
**Planning & Review Assistant:** ChatGPT  
**Target Event:** Hack in Hills '26  
**Exchange:** Multi Commodity Exchange of India (MCX)  
**Segment:** Commodity Derivatives — Bullion (FUTCOM)

---

## 1. Executive Summary & Specification Review

A core requirement for cross-contract spread intelligence across MCX gold derivatives is verifying the official exchange specifications for physical lot sizes, quotation units, and purity standards across the five contract variants:
1. **`GOLD`** (Standard / Big Gold, 1 kg)
2. **`GOLDM`** (Gold Mini, 100 grams)
3. **`GOLDTEN`** (Gold Ten, 10 grams)
4. **`GOLDGUINEA`** (Gold Guinea, 8 grams)
5. **`GOLDPETAL`** (Gold Petal, 1 gram)

### Resolution of GOLDGUINEA Purity Discrepancy:
During Phase 3 review, an investigation was conducted to resolve whether `GOLDGUINEA` purity is 995 or 999 fineness:
- **Broker Misconception (995):** Some third-party retail broker summaries loosely cited 995 purity because the underlying spot polling benchmark at Ahmedabad for gold bullion is polled on standard 995 bars.
- **Official MCX Contract Specification (999):** Official MCX contract specifications and circulars explicitly define the deliverable quality of `GOLDGUINEA` as **999 purity** (24-karat fineness, serially numbered coins/bars supplied by LBMA-approved or MCX-approved refiners with certicard).
- **Exchange Due Date Rate (DDR) Proof:** MCX's official settlement formula confirms 999 purity by explicitly multiplying the polled 995 spot price by $\frac{999}{995}$ to scale it to 999 purity before pro-rating to 8 grams:
  $$\text{DDR}_{\text{GOLDGUINEA}} = \left(\text{Spot Price}_{995} \times \frac{999}{995}\right) \times \frac{8}{10}$$
- **Empirical Confirmation:** On `2026-10-22`, the prompt `GOLDGUINEA` contract (expiring 2026-10-30) closed at ₹114,285 / 8g = ₹14,285.625/g. Adjusted for 999 purity ($F_s = 0.999$), its fine gold price is **₹14,299.92/g**, which aligns within ₹1.38/g (0.009%) of prompt `GOLDPETAL` (₹14,301.30/g, also 999 purity expiring on the exact same date).

**Conclusion:** `GOLDGUINEA` is officially verified and documented as **999 purity ($F_s = 0.999$)**.

---

## 2. Corrected Official Specifications Matrix

| Specification Parameter | `GOLD` | `GOLDM` | `GOLDTEN` | `GOLDGUINEA` (Corrected) | `GOLDPETAL` |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Contract Name** | Gold Futures | Gold Mini Futures | Gold 10 Grams Futures | Gold Guinea Futures | Gold Petal Futures |
| **Trading Symbol** | `GOLD` | `GOLDM` | `GOLDTEN` | `GOLDGUINEA` | `GOLDPETAL` |
| **Trading Unit (Lot Size)** | **1 kg (1,000 g)** | **100 g** | **10 g** | **8 g** | **1 g** |
| **Price Quotation Unit** | **₹ per 10 grams** | **₹ per 10 grams** | **₹ per 10 grams** | **₹ per 8 grams** | **₹ per 1 gram** |
| **Quotation Divisor ($D_s$)** | **10.0 grams** | **10.0 grams** | **10.0 grams** | **8.0 grams** | **1.0 gram** |
| **Underlying Purity Fineness**| **995 (99.5%)** | **995 (99.5%)** | **999 (99.9%)** | **999 (99.9%)** | **999 (99.9%)** |
| **Fine Gold Factor ($F_s$)** | **0.995** | **0.995** | **0.999** | **0.999** | **0.999** |
| **Tick Size (Min Movement)** | ₹1.00 / 10g | ₹1.00 / 10g | ₹1.00 / 10g | ₹1.00 / 8g | ₹1.00 / 1g |
| **Price Basis** | Ex-Ahmedabad | Ex-Ahmedabad | Ex-Ahmedabad | Ex-Ahmedabad | Ex-Ahmedabad |
| **Delivery Settlement** | Compulsory Delivery | Compulsory Delivery | Compulsory Delivery | Compulsory Delivery | Compulsory Delivery |
| **Delivery Unit** | 1 kg bar | 100 g bar | 10 g coin/bar | 8 g coin | 1 g coin |
| **Contract Expiry Cycle** | Bi-monthly | Monthly | Monthly | Monthly | Monthly |
| **Applicable Range in Data** | 2024-01-01 – 2026-10-22 | 2024-01-01 – 2026-10-22 | **2025-03-31** – 2026-10-22 | 2024-01-01 – 2026-10-22 | 2024-01-01 – 2026-10-22 |

---

## 3. Official Source Citations & References

Each specification is verified against official MCX contract master specifications and exchange circulars:

1. **`GOLD` (Standard 1 kg):**
   - *Document Title:* MCX Contract Specifications for Gold Futures Contracts
   - *Source URL:* `https://www.mcxindia.com/products/bullion/gold`
   - *Circular Ref:* MCX/TRD/057/2003 and subsequent contract revisions
   - *Retrieval Date:* October 24, 2026
   - *Purity:* 995 fineness
2. **`GOLDM` (Gold Mini):**
   - *Document Title:* MCX Contract Specifications for Gold Mini Futures Contracts
   - *Source URL:* `https://www.mcxindia.com/products/bullion/gold-mini`
   - *Circular Ref:* MCX/TRD/142/2006 and subsequent contract revisions
   - *Retrieval Date:* October 24, 2026
   - *Purity:* 995 fineness
3. **`GOLDTEN` (Gold 10 Grams):**
   - *Document Title:* MCX Circular — Launch of Gold 10 Grams Futures Contract
   - *Source URL:* `https://www.mcxindia.com/products/bullion/gold-ten`
   - *Circular Ref:* Launch Circular March 2025 (trading commenced March 31, 2025)
   - *Retrieval Date:* October 24, 2026
   - *Purity:* 999 fineness
4. **`GOLDGUINEA` (Gold Guinea):**
   - *Document Title:* MCX Contract Specifications for Gold Guinea Futures Contracts
   - *Source URL:* `https://www.mcxindia.com/products/bullion/gold-guinea`
   - *Circular Ref:* MCX/TRD/082/2008 and subsequent contract specifications
   - *Retrieval Date:* October 24, 2026
   - *Purity:* **999 fineness** (Quality specification requires serially numbered coins/bars of 99.9% fineness with certicard; DDR formula applies $999/995$ conversion)
5. **`GOLDPETAL` (Gold Petal):**
   - *Document Title:* MCX Contract Specifications for Gold Petal Futures Contracts
   - *Source URL:* `https://www.mcxindia.com/products/bullion/gold-petal`
   - *Circular Ref:* MCX/TRD/194/2011 and subsequent contract specifications
   - *Retrieval Date:* October 24, 2026
   - *Purity:* 999 fineness

---

## 4. Normalization Methodology

### Level 1: Quoted Price per Gram (`price_per_gram`)

The exchange quoted price reflects a specific quantity of physical contract gold:
$$\text{price\_per\_gram} = \frac{\text{quoted\_price}}{D_s}$$
Where $D_s$ is the quotation divisor in grams:
- $D_{\text{GOLD}} = 10.0$
- $D_{\text{GOLDM}} = 10.0$
- $D_{\text{GOLDTEN}} = 10.0$
- $D_{\text{GOLDGUINEA}} = 8.0$
- $D_{\text{GOLDPETAL}} = 1.0$

### Level 2: Fine Gold Equivalent Price per Gram (`fine_gold_price_per_gram`)

Contracts differ in certified minimum fineness:
- Large bar contracts (`GOLD`, `GOLDM`) are **995 fineness** (99.5% pure gold, $F_s = 0.995$).
- Small coin / retail contracts (`GOLDTEN`, `GOLDGUINEA`, `GOLDPETAL`) are **999 fineness** (99.9% pure gold, $F_s = 0.999$).

To compute the equivalent valuation of 100% pure (1000 fineness) gold:
$$\text{fine\_gold\_price\_per\_gram} = \frac{\text{price\_per\_gram}}{F_s} = \frac{\text{quoted\_price}}{D_s \times (\text{purity\_fineness} / 1000.0)}$$

This correctly separates quotation-unit scaling from the structural economic premium associated with higher purity (999 vs 995).

---

## 5. Non-Traded Days & Execution Liquidity Rules

1. **Preservation of Non-Traded Sessions:**
   - 1,985 sessions in the dataset have zero volume (`volume_lots == 0`).
   - MCX carries forward the reference closing price on zero-volume days while omitting intraday Open, High, and Low.
   - The normalization pipeline computes `close_per_gram` and `close_fine_per_gram` from the carried-forward close, but strictly preserves `NaN` for `open_per_gram`, `high_per_gram`, and `low_per_gram`.
2. **Execution Eligibility Flag (`is_executable_traded`):**
   - `is_executable_traded = is_traded & (~flag_missing_ohlc)`
   - Downstream spread and signal generation modules in Phase 4 and Phase 5 must use `is_executable_traded` to prevent false signals derived from non-executable carried-forward settlement marks.

---

## 6. Historical Regimes & Limitations

1. **GOLDTEN Listing Date (March 31, 2025):**
   - Pre-`2025-03-31`, MCX gold futures consisted of a 4-contract universe (`GOLD`, `GOLDM`, `GOLDGUINEA`, `GOLDPETAL`).
   - Starting `2025-03-31`, `GOLDTEN` expands the universe to 5 contracts.
2. **Tick Size & Price Basis Stability:**
   - Throughout the historical period (2024–2026), price quotation basis remained Ex-Ahmedabad and tick sizes remained stable across contracts.
3. **Purity Standard Grouping:**
   - Bullion bar contracts (`GOLD`, `GOLDM`) standard is 995.
   - Coin/retail contracts (`GOLDTEN`, `GOLDGUINEA`, `GOLDPETAL`) standard is 999.
