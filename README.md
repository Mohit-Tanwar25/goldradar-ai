# Gold Contract Radar — MCX Commodity Derivatives Intelligence

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Streamlit 1.30+](https://img.shields.io/badge/streamlit-1.30%2B-FF4B4B.svg)](https://streamlit.io/)
[![Plotly 5.18+](https://img.shields.io/badge/plotly-5.18%2B-3F4F75.svg)](https://plotly.com/)
[![Tests Passing](https://img.shields.io/badge/tests-111%20passed-brightgreen.svg)](tests/)

**Target Event:** Hack in Hills ’26  
**Asset Class:** Multi-Contract Gold Futures Derivatives (Multi Commodity Exchange of India — MCX)  
**Active Contract Universe:** 4 Retail/Mini MCX Gold Contracts (`GOLDM`, `GOLDTEN`, `GOLDGUINEA`, `GOLDPETAL`)  
**Excluded Wholesale Contract:** `GOLD` (1 kg Standard Bullion — preserved in historical archive)  
**Historical Period Analyzed:** 2024 – 2026 (701 unique trading sessions, 11,968 active settlement records; 16,195 in preserved 5-product archive)  

---

## 1. Project Overview

**Gold Contract Radar** is an institutional-grade commodity derivatives research engine and interactive analytical dashboard designed for MCX gold futures.

In the Indian commodities market, gold futures trade across multiple contract specifications. For retail, jeweller, and non-institutional participants targeted by the Hack in Hills '26 scope, the active universe is restricted to **four retail/mini contracts**:
- **`GOLDM`** (MCX Gold Mini — 100g trading unit, 995 fineness)
- **`GOLDTEN`** (MCX Gold Ten — 10g trading unit, 999 fineness)
- **`GOLDGUINEA`** (MCX Gold Guinea — 8g trading unit, 999 fineness)
- **`GOLDPETAL`** (MCX Gold Petal — 1g trading unit, 999 fineness)

The standard 1 kg wholesale contract (`GOLD`) is excluded from active analysis to eliminate extreme integer-lot sizing mismatches and outsized nominal dollar drawdown distortion, while remaining preserved in the historical baseline archive for scientific reproducibility.

### The Problem Addressed
Because different MCX contracts trade in different quotation units (per 10g, per 8g, per 1g) and different physical purities (995 vs 999 parts per thousand), quoted screen prices cannot be compared directly. Gold Contract Radar economically normalizes all contracts into standard **₹ per gram of 999 fine gold**, enabling transparent cross-contract basis tracking, forward curve carry analysis, statutory transaction-cost modeling, and walk-forward backtesting.

---

## 2. Key Features

The application provides a streamlined, intuitive 6-page analytical workflow answering key questions from market overview to data provenance:

### 🏠 Page 1 — Overview: "What is happening in the gold market?"
- **Macro Market Metrics:** Total observations (11,968), active symbols (4), latest prompt gold price (₹/g 999 fine gold), active forward curve structure (Contango/Backwardation), and statutory cost regime status.
- **Prompt Price Trajectory:** Multi-series normalized historical settlement price trend across prompt contracts (`GOLDM`, `GOLDTEN`, `GOLDGUINEA`, `GOLDPETAL`).
- **Strategy Highlights:** High-level performance overview of relative-value spread convergence (Strategy A) and calendar roll yield capture (Strategy B).
- **Data Integrity Scorecard:** Upstream data pipeline validation status and SHA-256 integrity confirmation.
- **Trader-Facing Opportunities:** Identified candidate spreads with z-scores, alongside a clear fallback empty-state when no trades satisfy tender/cost screens.

### 🔍 Page 2 — Compare Contracts: "Which contract looks cheaper or more expensive?"
- **Normalization Derivation:** Transparent fine-gold parity math ($P_{\text{fine}} = \frac{P_{\text{quoted}}}{D_s \times F_s}$).
- **Pair Selector:** Interactive selection between any active contract pairs (e.g. `GOLDM` vs `GOLDTEN`).
- **Normalized Spread Trajectory:** Historical spread timeseries with rolling $\pm 2\sigma$ Bollinger bands for relative mispricing detection.
- **Spread Distribution:** Statistical histogram and quantile dispersion analysis.
- **Historical Candlestick & Volume:** Underlying contract volume, open interest, and session OHLC dynamics.

### 📈 Page 3 — Futures Curve: "How do prices change with expiry?"
- **Interactive Forward Curve:** Forward curves across chronological settlement dates and actual maturities.
- **Contango vs. Backwardation State:** Annualized roll yield trajectory ($% \text{ p.a.}$) over time.
- **Term Structure Table:** Detailed snapshot table listing quotation prices, normalized ₹/g rates, and days to maturity.

### ⚡ Page 4 — Opportunities & Costs: "Is the opportunity meaningful after costs?"
- **Candidate Funnel & Attrition:** Visual attrition waterfall from 31,483 screened candidates to 26,822 trade-eligible opportunities.
- **Statutory Fee Schedule:** Granular breakdown of CTT (0.010% sell), Stamp Duty (0.002% buy), Exchange turnover fees (0.0021%), SEBI charges (0.0001%), and GST (18%).
- **Multi-Scenario Comparison:** Realized cost impact across `base`, `low`, and `high` broker expense tiers.
- **Filter Rejection Breakdown:** Root causes of ineligible candidates (tender window $\le 5$ DTE, minimum volume, minimum open interest).

### 🧪 Page 5 — Backtest Performance: "How did the strategy perform historically?"
- **Audited Financial Metrics:** Single-scenario evaluation (`base`, `low`, `high`) displaying audited Gross P&L (+₹59,812.00), Fees (₹52,516.15), Net P&L (+₹7,295.85), Win Rate (40.57%), and Max Drawdown (₹186,188.75).
- **Cumulative Realized Equity Curve:** Chronological cumulative net P&L ordered strictly by trade exit date, with realized drawdown overlay.
- **Strategy Breakdown:** Side-by-side performance comparison of Strategy A (Spread Convergence: +₹56,968.83 Net) vs. Strategy B (Calendar Roll: -₹49,672.98 Net).
- **Market Neutrality / Gold Beta Separation:** Statistical confirmation that strategy returns are isolated from general gold directional price beta ($r = -0.06$).
- **Walk-Forward Fold Performance:** Out-of-sample breakdown across 10 rolling folds (no lookahead bias).
- **Filterable Trade Ledger:** Complete 244-trade ledger with entry/exit dates, fill prices, fees, and outcomes.

### 📚 Page 6 — Data & Methodology: "Where does the analysis come from?"
- **Active Contract Universe Policy:** Explicit disclosure of the four active contracts and historical retention of the 1 kg contract.
- **Contract Specifications Table:** Official MCX contract parameters for `GOLDM`, `GOLDTEN`, `GOLDGUINEA`, and `GOLDPETAL`.
- **Normalization Methodology:** Mathematical derivation of fine-gold economic parity.
- **Walk-Forward Mechanics:** Rolling fold construction, out-of-sample isolation, and quarantine rules for newly listed products.
- **Portfolio Exposure Limits:** Deterministic allocation rules, concurrent position limits, and verified 0 concurrent contract collisions.
- **Execution Feasibility Disclosures:** Bhavcopy settlement proxy limitations, lack of intraday tick/depth data, and simulated open fills.

---

## 3. Technology Stack

- **Core Language:** Python 3.10+ (tested on Python 3.11.1)
- **User Interface:** Streamlit 1.30+
- **Interactive Visualization:** Plotly 5.18+
- **Data Processing & Analytics:** Pandas 2.0+, NumPy 1.24+
- **Date Handling:** python-dateutil 2.8+
- **Automated Testing:** Python `unittest` framework (111 tests)

---

## 4. Prerequisites

- **Python:** Python 3.10, 3.11, or 3.12 installed on your system.
- **Git:** Git version control installed.
- **Operating System:** Platform-independent (tested on Windows 11, compatible with Linux and macOS).
- **Network / Secrets:** None required. The project runs completely self-contained on included datasets without external API keys or subscriptions.

---

## 5. Installation and Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Mohit-Tanwar25/goldradar-ai.git
cd goldradar-ai
```

### 2. Set Up Virtual Environment

#### Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> **PowerShell Activation Note:** If PowerShell displays an execution policy error such as `cannot be loaded because running scripts is disabled on this system`, activate with process-level bypass without altering system-wide security settings:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
> .\.venv\Scripts\Activate.ps1
> ```
> Alternatively, use Windows Command Prompt (`.venv\Scripts\activate.bat`).

#### macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 6. Run the Dashboard

To launch the interactive dashboard locally:

```bash
streamlit run app.py
```

Streamlit will compile and open the web workstation in your default browser at:
- **Local URL:** `http://localhost:8501`
- **Network URL:** displayed in your terminal

The dashboard will load all pre-processed datasets directly and initialize instantly.

---

## 7. Run Automated Tests

The repository includes a comprehensive 111-test automated test suite covering normalization math, relative price radar, liquidity screening, walk-forward backtesting, dashboard metric calculations, and independent financial reconciliation.

### Run Full Test Suite:
```bash
python -m unittest discover tests
```

### Expected Output:
```
.............................................................................................
----------------------------------------------------------------------
Ran 111 tests in 38.194s

OK
```

### Run Specific Test Modules:
```bash
# Independent Financial Reconciliation & Hash Audit (7 tests):
python -m unittest tests/test_independent_audit_reconciliation.py

# Normalization Unit Tests (9 tests):
python -m unittest tests/test_normalization.py

# Relative Price Radar Unit Tests (18 tests):
python -m unittest tests/test_relative_price_radar.py

# Liquidity & Transaction Cost Unit Tests (20 tests):
python -m unittest tests/test_liquidity_cost_filters.py

# Walk-Forward Backtest Unit Tests (39 tests):
python -m unittest tests/test_walk_forward_backtest.py

# Dashboard UI & Metric Unit Tests (18 tests):
python -m unittest tests/test_dashboard.py
```

---

## 8. Run the Data Pipeline

### Option A: Using Pre-Committed Processed Data (Recommended)
You do **not** need to rebuild the pipeline to use the dashboard or run tests. All 12 validated production CSV files are committed in `data/processed/` with verified SHA-256 hashes.

### Option B: Rebuilding the Pipeline From Scratch
If you wish to re-execute the end-to-end data processing and quantitative modeling pipeline from raw bhavcopy data, execute the pipeline scripts in their strict dependency order:

```bash
# Step 1: Ingest raw MCX bhavcopy files and assemble the master dataset
python src/prepare_master_dataset.py

# Step 2: Normalize prices across contract quotation units and purities into ₹/g 999 fine gold
python src/normalize_prices.py

# Step 3: Compute pairwise relative-price radar spreads and forward curve term structures
python src/build_relative_price_radar.py

# Step 4: Screen candidates via liquidity, volume, OI, and statutory transaction cost models
python src/apply_liquidity_cost_filters.py

# Step 5: Execute 10-fold walk-forward backtest with next-session Open execution
python src/run_walk_forward_backtest.py
```

---

## 9. Data Methodology & Limitations

### 1. Mathematical Price Normalization
To compare contracts on an exact physical gold parity, raw quoted prices are normalized into **₹ per gram of 999 fine gold**:
$$P_{\text{fine}} = \frac{P_{\text{quoted}}}{\text{Quotation Divisor} \times \text{Fine Gold Factor}}$$
- **`GOLDM`** (100g, 995 fineness): Quoted per 10g $\rightarrow$ Divisor = 10, Factor = $0.995/0.999 = 0.995996$ $\rightarrow$ effective divisor = 9.95
- **`GOLDTEN`** (10g, 999 fineness): Quoted per 10g $\rightarrow$ Divisor = 10, Factor = 0.999 $\rightarrow$ effective divisor = 9.99
- **`GOLDGUINEA`** (8g, 999 fineness): Quoted per 8g $\rightarrow$ Divisor = 8, Factor = 0.999 $\rightarrow$ effective divisor = 7.992
- **`GOLDPETAL`** (1g, 999 fineness): Quoted per 1g $\rightarrow$ Divisor = 1, Factor = 0.999 $\rightarrow$ effective divisor = 0.999

### 2. Simulated Execution Proxies vs. Guaranteed Fills
Backtest fills are simulated at the subsequent trading session's **Open price** following signal generation at previous settlement. Daily bhavcopy records lack continuous intraday order-book depth, bid-ask quotes, and queue priority. Simulated fills are reference proxies, not guaranteed executable fills.

### 3. Transaction Costs & Regulatory Levies
Statutory levies are deducted on all executed notionals:
- **CTT:** 0.010% on sell leg turnover (Finance Act 2013).
- **Stamp Duty:** 0.002% on buy leg turnover (Indian Stamp Act).
- **Exchange Fees:** 0.0021% on total turnover.
- **SEBI Charges:** 0.0001% on total turnover.
- **GST:** 18% on brokerage, exchange fees, and SEBI charges.
- **Brokerage:** Discount broker benchmark (Min(₹20, 0.03% of turnover) per executed leg).

### 4. Compulsory Tender Notice Avoidance
MCX gold contracts enforce compulsory physical delivery during the 5-day pre-expiry tender window. The backtesting engine enforces position liquidation at **$DTE \le 5$**, preventing delivery assignment and penalty risks.

### 5. Research Disclaimer
> **IMPORTANT NOTICE:** This application is an academic and quantitative research tool developed for **Hack in Hills ’26**. Its outputs, analytics, and simulated backtest results are strictly for educational research purposes and do **NOT** constitute financial, investment, or trading advice. Historical backtest performance does not guarantee future results.

---

## 10. Repository Structure

```
├── app.py                                # Streamlit application entry point (6-page redesigned workflow)
├── render.yaml                           # Render Web Service blueprint
├── requirements.txt                      # Production dependencies
├── .env.example                          # Environment variable configuration template
├── .gitignore                            # Clean repository exclusions
├── .streamlit/
│   └── config.toml                       # Headless server & dark institutional theme configuration
├── config/
│   ├── contract_specs.json               # Verified MCX contract specifications
│   ├── liquidity_filters.json            # Liquidity, volume, and OI thresholds
│   ├── transaction_costs.json            # Statutory taxes and multi-scenario fee schedules
│   └── backtest_config.json              # Walk-forward, portfolio exposure & execution rules
├── data/
│   ├── raw/                              # Historical bhavcopy and download manifests (2.49 MB)
│   └── processed/                        # 12 verified production datasets + 5-product archive
├── reports/                              # Detailed validation, audit, and methodology reports
├── scripts/                              # Reproducible audit and calculation scripts
├── src/
│   ├── prepare_master_dataset.py         # Phase 2 master dataset pipeline
│   ├── normalize_prices.py               # Phase 3 price normalization engine
│   ├── build_relative_price_radar.py     # Phase 4 relative price & term structure model
│   ├── apply_liquidity_cost_filters.py   # Phase 5 liquidity & cost screening engine
│   ├── run_walk_forward_backtest.py      # Phase 6 walk-forward backtest engine
│   └── dashboard/                        # Phase 7 Streamlit dashboard modules
│       ├── __init__.py
│       ├── data_loader.py                # Cached data ingestion & schema validation
│       ├── metrics.py                    # Financial reconciliation & equity curve math
│       ├── charts.py                     # 12 interactive Plotly dark-themed charts
│       ├── components.py                 # Custom CSS, KPI cards & disclaimers
│       └── views.py                      # Page renderers (Pages 1 through 6)
└── tests/
    ├── test_normalization.py             # Normalization unit tests (9 tests)
    ├── test_relative_price_radar.py      # Relative price radar unit tests (18 tests)
    ├── test_liquidity_cost_filters.py    # Liquidity & cost filters unit tests (20 tests)
    ├── test_walk_forward_backtest.py     # Walk-forward backtest unit tests (39 tests)
    ├── test_dashboard.py                 # Dashboard unit tests (18 tests)
    └── test_independent_audit_reconciliation.py # Independent reconciliation & audit tests (7 tests)
```

---

## 11. Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **PowerShell script execution disabled** | Restricted Windows PowerShell execution policy | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` in your current terminal session, or use `.venv\Scripts\activate.bat`. |
| **Streamlit port already in use (`Port 8501 is already in use`)** | Another Streamlit process is running | Launch on an alternative port: `streamlit run app.py --server.port 8502`. |
| **Missing required module (e.g. `ModuleNotFoundError: No module named 'streamlit'`)** | Virtual environment not activated or dependencies not installed | Activate `.venv` and run `pip install -r requirements.txt`. |
| **File not found when running scripts** | Current working directory is not the repository root | Ensure terminal is in `goldradar-ai/` root directory before running commands (`cd /path/to/goldradar-ai`). |
| **Test execution failure** | Using non-standard test discovery | Run `python -m unittest discover tests` from the repository root. |

---

## 12. Contribution & Workflow

1. Fork or branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your targeted code or documentation modifications.
3. Verify that all 111 tests pass:
   ```bash
   python -m unittest discover tests
   ```
4. Commit your changes with clear, descriptive commit messages:
   ```bash
   git commit -m "feat: describe your change"
   ```
5. Open a Pull Request targeting the `main` branch.

---

## 13. License and Attribution

- **License:** No formal open-source license file is currently provided. All rights reserved by the original authors.
- **Data Attribution:** Historical commodity settlement records are sourced from public daily bhavcopy files published by the [Multi Commodity Exchange of India (MCX)](https://www.mcxindia.com).
- **Target Event:** Hack in Hills ’26.
