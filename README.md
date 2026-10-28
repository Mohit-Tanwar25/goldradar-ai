# Gold Contract Radar — MCX Commodity Derivatives Intelligence

[![Next.js 16](https://img.shields.io/badge/Next.js-16%2B-black.svg?logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg?logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-blue.svg?logo=typescript)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-v4-38B2AC.svg?logo=tailwind-css)](https://tailwindcss.com/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg?logo=python)](https://www.python.org/downloads/)
[![Tests Passing](https://img.shields.io/badge/tests-72%2F72%20passing-brightgreen.svg)](backend/tests/)

**Asset Class:** Multi-Contract Gold Futures Derivatives (Multi Commodity Exchange of India — MCX)  
**Active Universe:** 4 Retail/Mini MCX Gold Contracts (`GOLDM`, `GOLDTEN`, `GOLDGUINEA`, `GOLDPETAL`)  
**Historical Period Analyzed:** 2024 – 2026 (Official MCX Bhavcopy EOD settlement records)

---

## 1. Project Overview & Architecture

**Gold Contract Radar** is a quantitative research workstation and financial analytics platform engineered for Indian gold commodity derivatives. It normalizes distinct contract purities and lot sizes to a common 999 fine-gold benchmark (₹/gram), tracks relative-value spreads, models statutory friction, and evaluates walk-forward backtest simulations.

The project is structured as a decoupled, high-performance monorepo:

- **`/frontend`**: Modern Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, Lucide Icons, and Recharts. Contains the complete user interface, custom data uploader, and interactive quote simulator.
- **`/backend`**: Lean Python FastAPI REST service, Pandas/NumPy analytics engine, MCX contract specifications, and authoritative processed datasets.

```
goldradar-ai/
├── backend/
│   ├── api/                     # FastAPI app & endpoints (data_service.py, main.py)
│   ├── config/                  # Contract specs, cost schedules, liquidity configs
│   ├── data/
│   │   └── processed/           # 12 canonical production CSV datasets (~98 MB)
│   ├── src/                     # Core math, normalization, radar, & backtesting logic
│   ├── tests/                   # 7 test suites (72 unit & regression tests)
│   └── requirements.txt         # Lean production dependencies (no Streamlit/Plotly)
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js App Router (layout.tsx, page.tsx, globals.css)
│   │   ├── components/          # Recharts visualizations, single dashboard, & views
│   │   ├── lib/                 # Type-safe API client & formatting utilities
│   │   └── types/               # TypeScript interfaces matching backend models
│   ├── package.json
│   ├── next.config.ts
│   └── tsconfig.json
├── package.json                 # Monorepo root scripts
├── render.yaml                  # Production blueprint for Render cloud deployment
├── run.py                       # Unified local development launcher
├── run.bat                      # 1-click Windows runner
└── README.md
```

### Lightweight & Optimized Deployment
- **Zero Legacy Bloat:** All legacy prototypes (Streamlit UI, redundant scratch scripts, raw scrape files) have been removed.
- **Fast Build Times:** Lightweight backend dependencies allow sub-minute installations on free-tier container platforms like Render and Vercel.
- **Pure Web Dashboard:** The entire UI is 100% Next.js + React.

---

## 2. Dashboard Features & Analytical Workflow

The single-page dashboard organizes the complete analytical pipeline into an accessible viewport scroll:

```
[ A. Compact Header ]
         │
[ B. Market Overview (4 Key Parity KPIs) ]
         │
[ C. Interactive MCX Simulator & CSV File Uploader ]
         │
[ D. Opportunity Radar (Screened Pairs + CSV Export) ] ──▶ [ E. Opportunity Detail Card ]
         │
[ F. Contract Comparison (4 Contract Specs + Pair Selector) ]
         │
[ G. Market Analytics (Price History | Relative Spread | Futures Curve) ]
         │
[ H. Strategy Performance Summary (Walk-Forward Equity Curve & Breakdown) ]
```

### A. Header & Market Synchronization
- **Data Status Badge:** Confirms verified settlement data loaded from the backend.
- **Active Refresh:** Single-click synchronization to re-query the latest market metrics.

### B. Market Overview KPIs
Four top-level metrics normalized to ₹/gram (999 pure fine gold):
- **Normalized Gold Price:** Prompt contract benchmark rate in ₹/g.
- **Market Structure:** Regime across maturities (Contango, Backwardation, or Neutral).
- **Active Contracts:** Number of active MCX gold instruments tracked (4).
- **Eligible Research Opportunities:** Count of contract pairs clearing statutory transaction cost hurdles.

### C. Interactive MCX Custom Inspector & CSV Uploader
Allows users and evaluators to interactively simulate quotes or upload custom datasets:
- **Live Quote Simulator:** Enter custom prices for any two MCX contracts (`GOLDM`, `GOLDTEN`, `GOLDGUINEA`, `GOLDPETAL`) to view real-time normalized fine prices, gross spread, itemized statutory friction (CTT, Stamp Duty, Exchange fees, SEBI, GST, Slippage), and an instant parity verdict.
- **CSV / Bhavcopy File Upload:** Drag-and-drop custom `.csv` files to batch-normalize prices to fine gold and generate a pairwise relative-spread matrix.
- **Quick Test Buttons:** Includes **"Load Sample MCX Quotes"** for 1-click testing and **"Download Template (.csv)"** for easy formatting.

### D. Opportunity Radar & One-Click CSV Export
The primary relative-value research table:
- **Scenario Toggle:** Switch between friction scenarios (`Base Case`, `Low Cost`, `High Cost`).
- **Cost Schedule Drawer:** View the exact tax breakdown (CTT, Stamp Duty, GST, Exchange & SEBI fees, slippage bps).
- **Opportunity Table:** Displays contract pair, status badge (`Potential opportunity`, `Waiting for trigger`, `Not currently eligible`), gross spread, modeled round-trip friction, and color-coded **Net Spread (₹/g)** pill.
- **Export to CSV:** Direct browser download of screened opportunities into a `.csv` file.

### E. Opportunity Detail & Chart Shortcut
Selecting any candidate pair opens an inline inspection card:
- Displays fine spread, statistical z-score ($\sigma$), and modeled net edge.
- **Execution & Expiry Constraints:** Detailed leg specifications, days to expiry (DTE), and fill conventions.
- **"Plot in Spread / Futures Curve" Action:** Smoothly scrolls and automatically focuses the analytics chart on the selected pair.

### F. Contract Comparison
Side-by-side specification cards for the 4 active MCX contracts:
- **`GOLDM`** (100g, 995 fineness)
- **`GOLDTEN`** (10g, 999 fineness)
- **`GOLDGUINEA`** (8g sovereign, 916 / 22K fineness)
- **`GOLDPETAL`** (1g, 999 fineness)
- Interactive **Leg A / Leg B** selector with an instant swap button to update the spread charts below.

### G. Market Analytics & Multi-View Charts
Interactive chart with a view switcher:
- **Historical Price Trend:** Multi-line normalized fine-gold price trajectory across all active contracts.
- **Relative Spread:** Interactive timeseries showing spread dynamics with a 30-day moving average and $\pm 2\sigma$ volatility bands.
- **Futures Curve:** Forward term structure plotting fine-gold price against days to expiry with an interactive snapshot date picker.

### H. Strategy Performance Summary
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
| **Testing** | Python `unittest` (72 verified tests) |
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

### Step 2: Set Up Python Backend
```bash
# Create and activate virtual environment
python -m venv .venv

# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..
```

### Step 3: Set Up Frontend
```bash
cd frontend
npm install
cd ..
```

### Step 4: Run Application (Unified Launcher)
Start both the FastAPI backend and Next.js frontend concurrently with a single command from the project root:

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

### Option A: Deploy via Render Blueprint (Recommended)
1. Go to [dashboard.render.com](https://dashboard.render.com) $\rightarrow$ **New +** $\rightarrow$ **Blueprint**.
2. Connect your GitHub repository `Mohit-Tanwar25/goldradar-ai`.
3. Render automatically provisions both services:
   - `goldradar-api` (FastAPI backend)
   - `goldradar-frontend` (Next.js frontend)
4. Click **Apply**.
5. Once `goldradar-api` is deployed, set `NEXT_PUBLIC_API_URL` in `goldradar-frontend` environment variables to your backend URL (e.g. `https://goldradar-api.onrender.com`).

### Option B: Manual Service Configuration
If creating services manually in the Render dashboard:

1. **Backend Web Service:**
   - **Runtime:** Python 3
   - **Root Directory:** `backend`
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
cd backend
python -m unittest tests/test_dashboard.py tests/test_independent_audit_reconciliation.py tests/test_normalization.py tests/test_relative_price_radar.py tests/test_liquidity_cost_filters.py
cd ..
```
*Expected: 72 tests passing with zero errors or warnings.*

Run frontend TypeScript and production build checks:
```bash
cd frontend
npx tsc --noEmit
npm run build
```

---

## 7. Data Sources & Methodology

- **Source:** Historical official Bhavcopy settlement data from the **Multi Commodity Exchange of India (MCX)** ([mcxindia.com](https://www.mcxindia.com/market-data/bhavcopy)) covering Jan 2024 – Oct 2026.
- **Normalization Formula:**
  $$\text{Normalized Fine Price (₹/g)} = \left(\frac{\text{Quoted Price}}{\text{Lot Size (grams)}}\right) \times \left(\frac{1000}{\text{Purity Fineness}}\right)$$
- **Nature of Tool:** Gold Contract Radar is an **analytical research utility**. All relative spreads, transaction friction estimates, and walk-forward simulations are historical research models. It does not connect to live broker order routing, execute trades, or provide investment advice.
