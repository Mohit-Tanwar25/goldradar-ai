# Gold Contract Radar — MCX Commodity Derivatives Intelligence

[![Next.js 16](https://img.shields.io/badge/Next.js-16%2B-black.svg?logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg?logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-blue.svg?logo=typescript)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-v4-38B2AC.svg?logo=tailwind-css)](https://tailwindcss.com/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg?logo=python)](https://www.python.org/downloads/)
[![Tests Passing](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)

**Asset Class:** Multi-Contract Gold Futures Derivatives (Multi Commodity Exchange of India — MCX)  
**Active Universe:** 4 Retail/Mini MCX Gold Contracts (`GOLDM`, `GOLDTEN`, `GOLDGUINEA`, `GOLDPETAL`)  
**Historical Period Analyzed:** 2024 – 2026 (Official MCX Bhavcopy EOD settlement records)

---

## 1. Project Overview & Architecture

**Gold Contract Radar** is a quantitative research workstation and financial analytics dashboard engineered for Indian gold commodity derivatives. It normalizes distinct contract purities and lot sizes to a common 999 fine-gold benchmark (₹/gram), tracks relative-value spreads, models statutory friction, and evaluates walk-forward backtest simulations.

The entire user experience is consolidated into a **single, unified, minimalist dashboard**:

- **Frontend:** Next.js (App Router), React 19, TypeScript, Tailwind CSS, Lucide Icons, and Recharts.
- **Backend API:** Python FastAPI exposing high-performance REST endpoints.
- **Analytics Engine:** Python, Pandas, and NumPy preserving 100% of the underlying mathematical formulas, purity normalization, statutory cost schedules, and walk-forward simulations.

### Minimalist Financial Design
- **Content-Driven:** Pure white content cards on a subtle `#F7F8FA` background with clean `#E7E9ED` dividers and dark typography (`#17191D`).
- **Subtle Gold Accents:** `#B89137` accents for key active indicators and benchmarks.
- **Zero Decorative Clutter:** No multi-page navigation menus, redundant banners, or excessive boxes. Everything is accessible from a single viewport scroll.

---

## 2. Dashboard Sections

The single dashboard provides an end-to-end analytical workflow:

```
[ A. Compact Header ]
         │
[ B. Market Overview (4 Key Parity KPIs) ]
         │
[ C. Opportunity Radar (Screened Pairs + CSV Export) ] ──▶ [ D. Opportunity Evaluation Card ]
         │
[ E. Contract Comparison (4 Contract Specs + Pair Selector) ]
         │
[ F. Market Analytics (Price History | Relative Spread | Futures Curve) ]
         │
[ G. Strategy Performance Summary (Equity Curve & Breakdown) ]
```

### A. Compact Header
- **Page Title:** Gold Market Dashboard with gold `Au` emblem.
- **Data Status:** Real-time indicator confirming verified EOD settlement data from the backend.
- **Active Refresh:** Single-click re-querying and synchronizing the dashboard with backend data.

### B. Market Overview
Four compact top-level metrics normalized to ₹/gram (999 pure fine gold):
- **Normalized Gold Price:** Prompt contract benchmark rate in ₹/g.
- **Market Structure:** Calculated regime across maturities (Contango, Backwardation, or Neutral).
- **Active Contracts:** Number of active MCX gold instruments tracked (4).
- **Eligible Research Opportunities:** Count of contract pairs currently clearing modeled transaction cost hurdles.

### C. Opportunity Radar & One-Click CSV Export
The primary research screen evaluating cross-contract relative-value differences:
- **Filters:** Interactive toggle between friction scenarios (`Base Case`, `Low Cost`, `High Cost`) and contract symbol filters.
- **Cost Schedule Drawer:** Expandable breakdown of statutory taxes (CTT, Stamp Duty, GST, Exchange & SEBI fees, slippage bps).
- **Opportunity Table:** Displays contract pair, status badge (`Potential opportunity`, `Waiting for trigger`, `Not currently eligible`), gross spread, modeled round-trip friction, and color-coded **Net Spread (₹/g)** pill.
- **Export to CSV:** Direct browser download of screened opportunities into a `.csv` file for external analysis.

### D. Opportunity Evaluation & Plot Shortcut
Selecting any candidate pair opens an inline inspection card:
- Displays fine spread, statistical z-score ($\sigma$), and modeled net edge.
- **Execution & Expiry Constraints:** Detailed leg specifications, days to expiry (DTE), and fill conventions.
- **"Plot in Spread / Futures Curve" Action:** Smoothly scrolls and automatically focuses the interactive analytics chart on the selected pair.

### E. Contract Comparison
Side-by-side specification cards for the 4 active MCX contracts:
- **`GOLDM`** (100g, 995 fineness)
- **`GOLDTEN`** (10g, 999 fineness)
- **`GOLDGUINEA`** (8g sovereign, 916 / 22K fineness)
- **`GOLDPETAL`** (1g, 999 fineness)
- Displays trading unit, quotation basis, underlying fineness, and normalized ₹/g price.
- Interactive **Leg A / Leg B** selector with an instant swap button to update the spread charts below.

### F. Market Analytics & Multi-View Charts
Interactive chart with a compact view switcher:
- **Historical Price Trend:** Multi-line normalized fine-gold price trajectory across all active contracts.
- **Relative Spread:** Interactive timeseries showing spread dynamics with 30-day moving average and $\pm 2\sigma$ volatility bands.
- **Futures Curve:** Forward term structure plotting fine-gold price against days to expiry with an interactive snapshot date picker.

### G. Strategy Performance Summary
Historical walk-forward backtest evaluation:
- Summary metrics: Net P&L after modeled costs, Win Rate %, Maximum Drawdown, and Completed Trades.
- Multi-strategy performance breakdown table (`Spread Convergence` vs. `Calendar Spread Roll`).
- Interactive cumulative equity curve and drawdown chart.

---

## 3. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | Next.js 16+ (App Router), React 19, TypeScript, Tailwind CSS v4, Lucide React |
| **Charts** | Recharts 3.x (Clean Minimalist Financial Theme) |
| **Backend API** | Python 3.10+, FastAPI, Uvicorn, Pydantic |
| **Data Engine** | Pandas, NumPy, python-dateutil |
| **Testing** | Python `unittest` |
| **Deployment** | Render (`render.yaml` Blueprint) |

---

## 4. Local Development & Setup

### Prerequisites
- Python 3.10 or higher
- Node.js 18.x or higher
- npm or pnpm

### Step 1: Clone Repository
```bash
git clone https://github.com/Mohit-Tanwar25/goldradar-ai.git
cd goldradar-ai
```

### Step 2: Set Up Python Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate on Windows:
.\.venv\Scripts\activate
# Activate on macOS/Linux:
source .venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt
```

### Step 3: Set Up Frontend
```bash
cd frontend
npm install
cd ..
```

### Step 4: Run Application (Unified Runner)
You can start both the FastAPI backend and Next.js frontend concurrently with a single command from the project root:

```bash
python run.py
```
*(On Windows, you can also double-click `run.bat`)*

- **Frontend Dashboard:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Backend:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 5. Deployment on Render

The repository includes a ready-to-use [`render.yaml`](render.yaml) Blueprint that automatically provisions both the Python backend and Next.js frontend.

### Option A: One-Click Deploy via Render Blueprint (Recommended)
1. Go to [dashboard.render.com](https://dashboard.render.com) $\rightarrow$ **New +** $\rightarrow$ **Blueprint**.
2. Connect your GitHub repository `Mohit-Tanwar25/goldradar-ai`.
3. Render automatically discovers both services:
   - `goldradar-api` (FastAPI backend)
   - `goldradar-frontend` (Next.js frontend)
4. Click **Apply**.
5. Once `goldradar-api` is deployed, set `NEXT_PUBLIC_API_URL` in `goldradar-frontend` environment variables to your backend URL (e.g. `https://goldradar-api.onrender.com`).

### Option B: Manual Service Setup
If creating services manually in the Render dashboard:

1. **Backend Web Service:**
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variable:** `PYTHON_VERSION=3.11.1`

2. **Frontend Web Service:**
   - **Runtime:** Node
   - **Root Directory:** `frontend`
   - **Build Command:** `npm install && npm run build`
   - **Start Command:** `npm start`
   - **Environment Variables:**
     - `NODE_VERSION=20.10.0`
     - `NEXT_PUBLIC_API_URL=https://<your-backend-api-name>.onrender.com`

---

## 6. Testing & Quality Verification

Run the complete backend test suite:
```bash
python -m unittest tests/test_dashboard.py tests/test_independent_audit_reconciliation.py
```

Run frontend TypeScript and production build checks:
```bash
cd frontend
npx tsc --noEmit
npm run build
```

---

## 7. Data Sources & Limitations

- **Source:** Historical official Bhavcopy settlement data from the **Multi Commodity Exchange of India (MCX)** ([mcxindia.com](https://www.mcxindia.com/market-data/bhavcopy)) covering Jan 2024 – Oct 2026.
- **Normalization Formula:**
  $$\text{Normalized Fine Price (₹/g)} = \left(\frac{\text{Quoted Price}}{\text{Lot Size (grams)}}\right) \times \left(\frac{1000}{\text{Purity Fineness}}\right)$$
- **Nature of Tool:** Gold Contract Radar is an **analytical research utility**. All relative spreads, transaction friction estimates, and walk-forward simulations are historical research models. It does not connect to live broker order routing, execute trades, or provide investment advice.
