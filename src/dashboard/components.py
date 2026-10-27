"""
Gold Contract Radar — MCX Commodity Derivatives Intelligence
Reusable UI Components, Formatting, and Editorial Visual Styling
Designed to deliver an understated, premium financial research experience.
"""

from typing import Optional, Union, Dict, Any
import numpy as np
import pandas as pd
import streamlit as st

def inject_custom_css():
    """Inject polished, modern editorial financial styling with a warm neutral palette."""
    st.markdown("""
        <style>
        /* Import Professional Typography */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

        /* Global Reset & Base Typography */
        html, body, [class*="css"], .stApp {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: #16181D;
            background-color: #F7F8FA;
        }

        /* Streamlit Main Container Spacing */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1280px;
        }

        /* Top Header Styling */
        .page-header-container {
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #E7E9ED;
        }
        .page-header-tag {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.72rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #B89137;
            background: rgba(184, 145, 55, 0.08);
            border: 1px solid rgba(184, 145, 55, 0.22);
            padding: 3px 9px;
            border-radius: 999px;
            margin-bottom: 8px;
        }
        .page-header-title {
            font-size: 1.65rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            color: #16181D;
            margin: 0 0 6px 0;
            line-height: 1.25;
        }
        .page-header-subtitle {
            font-size: 0.92rem;
            font-weight: 400;
            color: #727985;
            margin: 0;
            line-height: 1.5;
        }

        /* KPI Metric Card Styling */
        .metric-card {
            background-color: #FFFFFF;
            border: 1px solid #E7E9ED;
            border-radius: 12px;
            padding: 16px 18px;
            margin-bottom: 12px;
            box-shadow: 0 1px 3px rgba(16, 24, 40, 0.04), 0 1px 2px rgba(16, 24, 40, 0.02);
            transition: all 0.15s ease-in-out;
            position: relative;
            overflow: hidden;
        }
        .metric-card:hover {
            border-color: #D1D5DB;
            box-shadow: 0 4px 8px -2px rgba(16, 24, 40, 0.06), 0 2px 4px -2px rgba(16, 24, 40, 0.04);
            transform: translateY(-1px);
        }
        .metric-card-accent-gold {
            border-top: 3px solid #B89137;
        }
        .metric-card-accent-green {
            border-top: 3px solid #0D8244;
        }
        .metric-card-accent-red {
            border-top: 3px solid #D32F2F;
        }
        .metric-card-accent-blue {
            border-top: 3px solid #2563EB;
        }
        .metric-label {
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #727985;
            font-weight: 600;
            margin-bottom: 6px;
        }
        .metric-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.45rem;
            font-weight: 600;
            color: #16181D;
            margin-bottom: 4px;
            line-height: 1.2;
        }
        .metric-value.positive { color: #0D8244; }
        .metric-value.negative { color: #D32F2F; }
        .metric-value.gold { color: #B89137; }
        .metric-value.blue { color: #2563EB; }
        .metric-subtext {
            font-size: 0.75rem;
            color: #727985;
            line-height: 1.4;
        }

        /* Information / Disclaimer Boxes */
        .callout-box {
            background-color: #FFFFFF;
            border: 1px solid #E7E9ED;
            border-left: 3px solid #B89137;
            border-radius: 8px;
            padding: 12px 16px;
            margin: 14px 0;
            font-size: 0.82rem;
            color: #374151;
            line-height: 1.55;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.03);
        }
        .callout-box.info {
            border-left-color: #2563EB;
            background-color: #F8FAFC;
        }
        .callout-box.warning {
            border-left-color: #B89137;
            background-color: #FDFBF7;
        }
        .callout-title {
            font-weight: 600;
            color: #16181D;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        /* Status & Audit Badges */
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.03em;
        }
        .badge-verified {
            background-color: rgba(13, 130, 68, 0.09);
            color: #0D8244;
            border: 1px solid rgba(13, 130, 68, 0.25);
        }
        .badge-gold {
            background-color: rgba(184, 145, 55, 0.09);
            color: #B89137;
            border: 1px solid rgba(184, 145, 55, 0.25);
        }
        .badge-neutral {
            background-color: #F1F3F5;
            color: #4B5563;
            border: 1px solid #E5E7EB;
        }
        .badge-blue {
            background-color: rgba(37, 99, 235, 0.08);
            color: #2563EB;
            border: 1px solid rgba(37, 99, 235, 0.22);
        }

        /* Contract Summary Card */
        .contract-spec-card {
            background-color: #FFFFFF;
            border: 1px solid #E7E9ED;
            border-radius: 10px;
            padding: 14px 16px;
            margin-bottom: 10px;
        }
        .contract-spec-title {
            font-weight: 700;
            font-size: 0.95rem;
            color: #16181D;
            margin-bottom: 4px;
        }
        .contract-spec-meta {
            font-size: 0.75rem;
            color: #727985;
            line-height: 1.5;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #FAFAFC;
            border-right: 1px solid #E7E9ED;
        }
        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.5rem;
            padding-left: 1.25rem;
            padding-right: 1.25rem;
        }

        /* Clean Streamlit Expander */
        .streamlit-expanderHeader {
            background-color: #FFFFFF !important;
            border: 1px solid #E7E9ED !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            color: #16181D !important;
            font-size: 0.88rem !important;
        }
        div[data-testid="stExpander"] {
            border: none !important;
            box-shadow: none !important;
            margin-bottom: 12px;
        }

        /* Tables & DataFrames */
        div[data-testid="stDataFrame"] {
            border: 1px solid #E7E9ED;
            border-radius: 8px;
            overflow: hidden;
            background-color: #FFFFFF;
        }

        /* Section Headings */
        .section-header {
            font-size: 1.05rem;
            font-weight: 600;
            color: #16181D;
            letter-spacing: -0.01em;
            margin: 1.25rem 0 0.75rem 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

def render_header(title: str, subtitle: Optional[str] = None, tag: str = "MCX Derivatives Intelligence"):
    """Render an understated, editorial page header with a refined hierarchy."""
    st.markdown(f"""
        <div class="page-header-container">
            <div class="page-header-tag">{tag}</div>
            <h1 class="page-header-title">{title}</h1>
            {f'<p class="page-header-subtitle">{subtitle}</p>' if subtitle else ''}
        </div>
    """, unsafe_allow_html=True)

def render_kpi_card(
    title: str,
    value: str,
    subtext: Optional[str] = None,
    variant: str = "default",
    accent_bar: bool = False
):
    """
    Render a clean, minimalist financial KPI card.
    Variants: 'default', 'positive', 'negative', 'gold', 'blue'.
    """
    cls = ""
    accent_cls = ""
    if variant == "positive":
        cls = "positive"
        if accent_bar: accent_cls = "metric-card-accent-green"
    elif variant == "negative":
        cls = "negative"
        if accent_bar: accent_cls = "metric-card-accent-red"
    elif variant == "gold":
        cls = "gold"
        if accent_bar: accent_cls = "metric-card-accent-gold"
    elif variant == "blue":
        cls = "blue"
        if accent_bar: accent_cls = "metric-card-accent-blue"

    sub_html = f'<div class="metric-subtext">{subtext}</div>' if subtext else ''
    st.markdown(f"""
        <div class="metric-card {accent_cls}">
            <div class="metric-label">{title}</div>
            <div class="metric-value {cls}">{value}</div>
            {sub_html}
        </div>
    """, unsafe_allow_html=True)

def render_disclaimer(context: str = "general"):
    """Render mandatory institutional research disclaimer in a restrained format."""
    disclaimers = {
        "general": (
            "Institutional Research & Simulation Notice",
            "This application is an educational and quantitative research workstation developed for MCX gold derivatives analysis. "
            "All statistics, price spreads, and backtest signals are derived from historical MCX end-of-day settlement bhavcopy records "
            "and modeled statutory transaction costs. Daily settlement data cannot establish whether simultaneous multi-leg orders "
            "could have been executed at recorded prices. Historical performance is not indicative of future market returns."
        ),
        "pnl": (
            "P&L & Drawdown Methodology Notice",
            "Cumulative equity series and drawdowns represent closed-trade realized P&L booked strictly on trade exit dates. "
            "Intermediate mark-to-market variations inside holding periods are unobserved in daily bhavcopy settlement data. "
            "Return on Capital (ROC) and Sharpe ratios are deliberately omitted because account leverage and initial margin deposits "
            "are participant-specific and unrecorded."
        ),
        "execution": (
            "Execution Feasibility & Look-Ahead Isolation",
            "Simulated entries and exits execute strictly at the subsequent trading session's Open price to eliminate look-ahead bias. "
            "Signals require both contract legs to exhibit positive traded volume and valid continuous quotes. "
            "Zero historical overlap across backtested portfolios does not guarantee continuous execution availability in live markets."
        )
    }
    title, body = disclaimers.get(context, disclaimers["general"])
    st.markdown(f"""
        <div class="callout-box warning">
            <div class="callout-title">⚠️ {title}</div>
            <div>{body}</div>
        </div>
    """, unsafe_allow_html=True)

def render_info_box(title: str, body: str):
    """Render an informational callout box with neutral styling."""
    st.markdown(f"""
        <div class="callout-box info">
            <div class="callout-title">ℹ️ {title}</div>
            <div>{body}</div>
        </div>
    """, unsafe_allow_html=True)

def format_inr(val: Optional[Union[float, int]], show_sign: bool = False) -> str:
    """Format numeric value into Indian Rupee format with standard accounting notation."""
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
    """Format percentage value with two decimal precision."""
    if val is None or pd.isna(val):
        return "0.00%"
    return f"{val:.2f}%"

def format_number(val: Optional[Union[float, int]]) -> str:
    """Format integer or float with thousands separator."""
    if val is None or pd.isna(val):
        return "0"
    return f"{int(val):,}"
