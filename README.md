# Gold Contract Radar — MCX Commodity Derivatives Intelligence

[![Next.js 15+](https://img.shields.io/badge/Next.js-15%2B-black.svg?logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg?logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-blue.svg?logo=typescript)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-v4-38B2AC.svg?logo=tailwind-css)](https://tailwindcss.com/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg?logo=python)](https://www.python.org/downloads/)
[![Tests Passing](https://img.shields.io/badge/tests-119%20passed-brightgreen.svg)](tests/)

**Asset Class:** Multi-Contract Gold Futures Derivatives (Multi Commodity Exchange of India — MCX)  
**Active Universe:** 4 Retail/Mini MCX Gold Contracts (`GOLDM`, `GOLDTEN`, `GOLDGUINEA`, `GOLDPETAL`)  
**Excluded Contract:** `GOLD` (1 kg Standard Wholesale Bullion — preserved in historical archive)  
**Historical Period Analyzed:** 2024 – 2026 (701 unique trading sessions, 11,968 active settlement records)

---

## 1. Project Overview & Modern Full-Stack Architecture

**Gold Contract Radar** is an institutional-grade commodity derivatives research workstation and interactive analytical dashboard designed for MCX gold futures.

The application has been completely migrated to a decoupled, high-performance web architecture:
- **Frontend:** Next.js (App Router) with React 19, TypeScript, Tailwind CSS, Lucide React, and Recharts.
- **Backend API:** Python FastAPI exposing high-performance REST endpoints powered directly by the authoritative financial calculation engine.
- **Analytics & Data Engine:** Python, Pandas, and NumPy preserving 100% of the underlying mathematical formulas, contract specifications, transaction cost models, and walk-forward backtest simulations.
- **Legacy Fallback:** The original Streamlit implementation remains available as a secondary fallback at `app.py`.

### Visual Design System
- **Minimalist Editorial Theme:** Generous whitespace, clean typography (Geist/Inter), and restrained accents.
- **Curated Palette:**
  - Background: `#F7F8FA`
  - Main Surfaces: `#FFFFFF`
  - Primary Text: `#17191D`
  - Secondary Text: `#707784`
  - Subtle Borders: `#E7E9ED`
  - Gold Accent: `#B89137`
  - Accessible Positive / Negative: `#0D8244` / `#D32F2F`
  - Informational Blue: `#2563EB`
- **Zero Decorative Clutter:** Elimination of heavy bordered containers, redundant explanation panels, repeated badges, and oversized hero sections. Key financial numbers and interactive charts take visual prominence.

---

## 2. Six Primary Pages

### 🏠 Page 1 — Overview
- **Executive KPIs:** Standardized 999 fine gold price per gram, active contracts count (4), historical session count (701), market curve regime (Contango), and walk-forward net strategy P&L.
- **Normalized Trend Chart:** Historical price trajectory across prompt contracts (`GOLDM`, `GOLDTEN`, `GOLDGUINEA`, `GOLDPETAL`) in ₹/g.
- **Contract Universe Grid:** Specification cards detailing lot sizes, quotation divisors, purity standards, and latest settlement rates.
- **Recent Opportunities Table:** Screened relative-value opportunities exceeding round-trip statutory costs.
- **Data Integrity Scorecard:** Upstream data pipeline validation status and SHA-256 integrity confirmation.

### 🔍 Page 2 — Compare Contracts
- **Single Compact Toolbar:** Select any two contracts (e.g. `GOLDM` vs `GOLDTEN`) with optional positive traded volume filter.
- **Spread Statistics:** Mean, median, standard deviation ($\sigma$), minimum, maximum, and latest relative percentage difference.
- **Historical Spread Chart:** Interactive timeseries with 30-day moving average and $\pm 2\sigma$ rolling volatility channels.
- **Spread Distribution:** Empirical frequency histogram of historical price differences.
- **Specifications Comparison Table:** Side-by-side comparison of physical lot sizes, quotation units, purity, and settlement terms.

### 📈 Page 3 — Futures Curve
- **Forward Curve Chart:** Term structure scatter plot depicting ₹/g fine gold price against days to expiry across all forward contracts.
- **Snapshot Selector:** Dropdown menu allowing inspection of any historical settlement date.
- **Annualized Roll Yield Chart:** Historical carry yield (% p.a.) across calendar spreads over time.
- **Maturity Schedule Table:** Granular tabular view of contract keys, maturity dates, days to expiry, and settlement rates.

### ⚡ Page 4 — Opportunities & Costs
- **Screening Funnel:** Attrition waterfall tracking raw pairs $\rightarrow$ liquidity screened $\rightarrow$ cost hurdle passed $\rightarrow$ fully eligible opportunities.
- **Multi-Scenario Cost Schedule:** Transparent statutory fee breakdown across `base`, `low`, and `high` tiers (CTT, Stamp Duty, Exchange Fee, SEBI Turnover Fee, GST 18%, Brokerage, Slippage).
- **Filterable Opportunities Ledger:** Screened candidates displaying gross spread, modeled round-trip friction, and estimated net spread per gram.
- **Risk Disclosures:** Prominent research notice confirming that historical spreads do not represent risk-free arbitrage.

### 🧪 Page 5 — Backtest Performance
- **Audited Financial Metrics:** Single-scenario evaluation displaying Gross P&L (+₹59,812.00), Fees (₹52,516.15), Net P&L (+₹7,295.85), Win Rate (40.57%), and Max Drawdown (₹186,188.75).
- **Mathematical Reconciliation:** Gross P&L − Modeled Costs = Net P&L verified to $10^{-4}$ Rupee precision.
- **Cumulative Equity Curve:** Chronological cumulative net P&L with peak equity line and drawdown shading.
- **Strategy Breakdown:** Side-by-side comparison of Spread Convergence vs. Calendar Roll strategies.
- **Walk-Forward Fold Results:** Performance across all 10 rolling test folds.
- **Simulated Trade Ledger:** Filterable trade execution ledger with signal date, entry/exit dates, fees, and outcomes.

### 📚 Page 6 — Data & Methodology
- **Active Universe Policy:** Explanation of retail/mini contracts and mathematical rationale for excluding 1 kg wholesale bullion (1,000:1 lot disparity).
- **Normalization Formula:** Mathematical derivation: $\text{Normalized Price} = \frac{\text{Quoted Price}}{\text{Quotation Divisor}} \times \frac{\text{Purity Fineness}}{0.999}$.
- **Dataset Inventory:** Tabular status of all 12 canonical Phase 1–6 datasets with row counts, file sizes, and SHA-256 verification.
- **Execution Controls:** Tender period restriction ($\le 5$ DTE) and execution assumptions.
- **Institutional Disclaimer:** Comprehensive research and regulatory disclosure.

---

## 3. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend Framework** | Next.js 15+ (App Router), React 19, TypeScript |
| **Styling & UI** | Tailwind CSS v4, Lucide React, clsx, tailwind-merge |
| **Interactive Charts** | Recharts 3.x (Light Minimalist Financial Theme) |
| **Backend API** | Python 3.10+, FastAPI 0.110+, Uvicorn, Pydantic 2.x |
| **Analytics Engine** | Pandas 2.0+, NumPy 1.24+, python-dateutil |
| **Testing** | Python `unittest` (119 automated tests passing) |
| **Legacy Fallback** | Streamlit 1.30+ (`app.py`) |

---

## 4. Local Development & Installation

### Step 1: Clone Repository & Set Up Python Environment
```bash
git clone https://github.com/Mohit-Tanwar25/goldradar-ai.git
cd goldradar-ai

# Create and activate virtual environment
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Start the Application (Unified Root Commands)

You can run the entire application directly from the project root without needing to `cd` into any subdirectories:

#### Option A: Run Both Backend & Frontend Together (Recommended)
```bash
python run.py
```
*(On Windows, you can also simply double-click or run `.\run.bat`)*

This launches:
- **FastAPI Backend:** `http://127.0.0.1:8000` (Docs: `http://127.0.0.1:8000/docs`)
- **Next.js Web Frontend:** `http://localhost:3000`

#### Option B: Run Frontend Separately from Root
```bash
npm run dev
```

#### Option C: Run Backend Separately from Root
```bash
npm run api
# or
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

### Step 3 (Optional): Run Legacy Streamlit Application
If you wish to inspect the legacy Streamlit UI as a fallback:
```bash
streamlit run app.py
```

---

## 5. Automated Testing

Run the complete 119-test automated test suite covering data loaders, mathematical transformations, KPI reconciliations, and FastAPI endpoint routes:
```bash
python -m unittest discover tests
```

To run only the FastAPI endpoint integration tests:
```bash
python -m unittest tests/test_api.py
```

To verify the Next.js frontend build and TypeScript checks:
```bash
cd frontend
npm run build
```

---

## 6. Environment Variables

### Frontend (`frontend/.env.local` optional)
```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```
In production, set `NEXT_PUBLIC_API_URL` to your deployed FastAPI backend URL.

---

## 7. Production Deployment

### Backend (Render / Railway / Docker)
Deploy using the included `render.yaml`:
```yaml
services:
  - type: web
    name: gold-contract-radar-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

### Frontend (Vercel / Netlify / Node Web Service)
1. Link the repository to [Vercel](https://vercel.com) or your preferred host.
2. Set Root Directory to `frontend`.
3. Set Environment Variable: `NEXT_PUBLIC_API_URL=https://your-api-domain.com`.
4. Deploy!

---

## 8. Financial Research Disclaimer

Gold Contract Radar is a quantitative commodity derivatives research platform. All spread analytics, transaction cost estimates, and walk-forward backtests are simulated historical research results. They do not constitute financial advice, guaranteed trading performance, or live execution guarantees. Past performance does not predict future market outcomes.
