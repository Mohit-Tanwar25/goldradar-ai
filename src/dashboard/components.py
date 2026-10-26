"""
Gold Contract Radar — MCX Commodity Derivatives Intelligence
Reusable UI Components, Formatting, and Visual Styling
"""

from typing import Optional, Union
import numpy as np
import pandas as pd
import streamlit as st

def inject_custom_css():
    """Inject polished, modern dark financial terminal styling."""
    st.markdown("""
        <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Metric Card Styling */
        .metric-card {
            background: linear-gradient(135deg, rgba(22, 27, 34, 0.95), rgba(30, 38, 48, 0.95));
            border: 1px solid rgba(212, 175, 55, 0.25);
            border-radius: 10px;
            padding: 16px 20px;
            margin-bottom: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .metric-card:hover {
            border-color: rgba(212, 175, 55, 0.6);
            transform: translateY(-2px);
        }
        .metric-label {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #8B949E;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .metric-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.65rem;
            font-weight: 700;
            color: #FFFFFF;
            margin-bottom: 2px;
        }
        .metric-value.positive { color: #00E676; }
        .metric-value.negative { color: #FF5252; }
        .metric-value.gold { color: #D4AF37; }
        .metric-subtext {
            font-size: 0.75rem;
            color: #78909C;
        }

        /* Disclaimer Banner */
        .disclaimer-box {
            background: rgba(245, 176, 65, 0.08);
            border-left: 4px solid #D4AF37;
            border-radius: 4px;
            padding: 12px 16px;
            margin: 16px 0;
            font-size: 0.82rem;
            color: #E6EDF3;
            line-height: 1.5;
        }

        /* Header Subtitle */
        .header-subtitle {
            font-size: 1.05rem;
            color: #8B949E;
            margin-top: -10px;
            margin-bottom: 24px;
            font-weight: 400;
        }

        /* Audit Badge */
        .badge-verified {
            background-color: rgba(0, 200, 83, 0.15);
            color: #00E676;
            border: 1px solid rgba(0, 200, 83, 0.4);
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.04em;
            display: inline-block;
        }
        </style>
    """, unsafe_allow_html=True)

def render_header(title: str, subtitle: Optional[str] = None):
    """Render unified page header with professional hierarchy."""
    st.title(title)
    if subtitle:
        st.markdown(f'<div class="header-subtitle">{subtitle}</div>', unsafe_allow_html=True)

def render_kpi_card(title: str, value: str, subtext: Optional[str] = None, variant: str = "default"):
    """Render a styled KPI metric card."""
    cls = "gold" if variant == "gold" else ("positive" if variant == "positive" else ("negative" if variant == "negative" else ""))
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{title}</div>
            <div class="metric-value {cls}">{value}</div>
            {f'<div class="metric-subtext">{subtext}</div>' if subtext else ''}
        </div>
    """, unsafe_allow_html=True)

def render_disclaimer(context: str = "general"):
    """Render mandatory institutional research disclaimer."""
    disclaimers = {
        "general": "<b>RESEARCH & SIMULATION DISCLAIMER:</b> This application is a historical quantitative research and simulation tool developed for Hack in Hills '26. All displayed statistics, signals, and simulated returns are derived from historical MCX end-of-day settlement records and modeled transaction costs. Daily bhavcopy data cannot establish whether simultaneous multi-leg orders could have been filled at modeled prices. Historical performance is not indicative of future market returns.",
        "pnl": "<b>P&L & DRAWDOWN METHODOLOGY NOTICE:</b> All cumulative equity series and drawdowns represent closed-trade realized P&L booked strictly at trade exit dates. Intermediate mark-to-market variations inside holding periods are unobserved in daily bhavcopy data. ROI, Sharpe ratios, and returns on capital are deliberately uncalculated because initial margin and account leverage are unrecorded.",
        "execution": "<b>EXECUTION FEASIBILITY NOTICE:</b> Simulated entries and exits execute strictly at the subsequent trading session's Open price to eliminate look-ahead bias. Orders require both contract legs to exhibit positive traded volume and valid continuous quotes. Zero historical overlap in backtest simulations does not guarantee continuous execution availability in live trading."
    }
    msg = disclaimers.get(context, disclaimers["general"])
    st.markdown(f'<div class="disclaimer-box">{msg}</div>', unsafe_allow_html=True)

def format_inr(val: Optional[Union[float, int]], show_sign: bool = False) -> str:
    """Format numeric value into Indian Rupee format with proper signs."""
    if val is None or pd.isna(val):
        return "₹0.00"
    sign = "+" if show_sign and val > 0 else ("-" if val < 0 else "")
    abs_v = abs(val)
    if abs_v >= 10_000_000:
        return f"{sign}₹{abs_v / 10_000_000:.2f} Cr"
    elif abs_v >= 100_000:
        return f"{sign}₹{abs_v / 100_000:.2f} L"
    else:
        return f"{sign}₹{abs_v:,.2f}"

def format_pct(val: Optional[Union[float, int]]) -> str:
    """Format percentage value."""
    if val is None or pd.isna(val):
        return "0.00%"
    return f"{val:.2f}%"

def format_number(val: Optional[Union[float, int]]) -> str:
    """Format integer with thousands separator."""
    if val is None or pd.isna(val):
        return "0"
    return f"{int(val):,}"
