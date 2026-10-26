"""
Gold Contract Radar — MCX Commodity Derivatives Intelligence
Phase 7: Interactive Financial Research Dashboard
Streamlit Application Entry Point
"""

import sys
import os
import streamlit as st
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.dashboard.components import inject_custom_css
from src.dashboard.data_loader import (
    load_contract_specs,
    load_backtest_config,
    load_transaction_costs_config,
    load_liquidity_filters_config,
    load_normalized_data,
    load_relative_price_radar,
    load_term_structure,
    load_term_structure_snapshots,
    load_liquidity_filtered_candidates,
    load_transaction_cost_scenarios,
    load_eligible_candidates,
    load_backtest_trades,
    load_walk_forward_metrics,
    load_backtest_summary,
    load_execution_diagnostics,
    get_dataset_inventory
)
from src.dashboard.views import (
    render_page_overview,
    render_page_compare_contracts,
    render_page_futures_curve,
    render_page_opportunities_costs,
    render_page_backtest,
    render_page_methodology
)

# 1. Page Configuration
st.set_page_config(
    page_title="Gold Contract Radar — MCX Commodity Derivatives Intelligence",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Polished CSS
inject_custom_css()

# 3. Sidebar Navigation & Branding
st.sidebar.markdown("""
<div style="text-align: center; padding: 10px 0 20px 0;">
    <h2 style="color: #D4AF37; margin: 0; font-size: 1.5rem; letter-spacing: 0.05em;">🪙 GOLD RADAR</h2>
    <p style="color: #8B949E; font-size: 0.75rem; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.1em;">
        MCX Derivatives Intelligence
    </p>
</div>
""", unsafe_allow_html=True)

nav_options = [
    "🏠 1. Overview",
    "🔍 2. Compare Contracts",
    "📈 3. Futures Curve",
    "⚡ 4. Opportunities & Costs",
    "🧪 5. Backtest Performance",
    "📚 6. Data & Methodology"
]

selected_page = st.sidebar.radio("Navigation Menu", nav_options, index=0)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="font-size: 0.75rem; color: #78909C; line-height: 1.6;">
    <b>Event:</b> Hack in Hills '26<br>
    <b>Exchange:</b> MCX India (Gold)<br>
    <b>Coverage:</b> 2024–2026 (701 sessions)<br>
    <b>Active Universe:</b> 4 Contracts (GOLDM, GOLDTEN, GOLDGUINEA, GOLDPETAL)<br>
    <b>Excluded:</b> GOLD (1kg Standard Bullion)<br>
    <b>Audit Status:</b> <span style="color: #00E676; font-weight:600;">Active Universe Verified</span>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("🔄 Refresh Application Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# 4. Global Dataset Loading with Graceful Degradation
try:
    with st.spinner("Loading production datasets..."):
        specs_cfg = load_contract_specs()
        bt_cfg = load_backtest_config()
        costs_cfg = load_transaction_costs_config()
        liq_cfg = load_liquidity_filters_config()
        
        norm_df = load_normalized_data()
        radar_df = load_relative_price_radar()
        term_df = load_term_structure()
        snapshots_df = load_term_structure_snapshots()
        liq_df = load_liquidity_filtered_candidates()
        costs_df = load_transaction_cost_scenarios()
        elig_df = load_eligible_candidates()
        trades_df = load_backtest_trades()
        metrics_df = load_walk_forward_metrics()
        summary_df = load_backtest_summary()
        diag_df = load_execution_diagnostics()
except Exception as e:
    st.error(f"⚠️ Error loading production datasets: {str(e)}")
    st.info("Ensure all canonical Phase 1-6 datasets exist in `data/processed/`.")
    st.stop()

# 5. Route Page Views
if selected_page == "🏠 1. Overview":
    render_page_overview(norm_df, summary_df, diag_df, elig_df, trades_df, radar_df)
elif selected_page == "🔍 2. Compare Contracts":
    render_page_compare_contracts(norm_df, radar_df, specs_cfg)
elif selected_page == "📈 3. Futures Curve":
    render_page_futures_curve(snapshots_df, term_df, specs_cfg)
elif selected_page == "⚡ 4. Opportunities & Costs":
    render_page_opportunities_costs(liq_df, costs_df, elig_df, radar_df)
elif selected_page == "🧪 5. Backtest Performance":
    render_page_backtest(trades_df, metrics_df, summary_df, diag_df, bt_cfg)
elif selected_page == "📚 6. Data & Methodology":
    render_page_methodology(specs_cfg, bt_cfg, costs_cfg, liq_cfg)

