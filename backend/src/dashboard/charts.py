"""
Gold Contract Radar — MCX Commodity Derivatives Intelligence
Interactive Plotly Financial Chart Library
Editorial Light Theme with Understated Aesthetics, High Contrast, and Precision Formatting.
"""

from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Editorial Financial Color Palette
COLOR_GOLD = "#B89137"
COLOR_GOLD_LIGHT = "#D4AF37"
COLOR_NAVY = "#1E293B"
COLOR_BLUE = "#2563EB"
COLOR_GREEN = "#0D8244"
COLOR_RED = "#D32F2F"
COLOR_PURPLE = "#7C3AED"
COLOR_GRAY = "#727985"
COLOR_GRID = "#E7E9ED"
COLOR_SURFACE = "#FFFFFF"
COLOR_TEXT = "#16181D"

def _apply_editorial_theme(fig: go.Figure, height: int = 420) -> go.Figure:
    """Apply unified, understated, editorial light financial styling to a Plotly figure."""
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=COLOR_SURFACE,
        plot_bgcolor=COLOR_SURFACE,
        margin=dict(l=45, r=35, t=45, b=40),
        height=height,
        font=dict(family="Inter, -apple-system, sans-serif", size=11, color=COLOR_TEXT),
        hoverlabel=dict(
            bgcolor=COLOR_SURFACE,
            bordercolor=COLOR_GRID,
            font_size=11,
            font_family="Inter, sans-serif",
            font_color=COLOR_TEXT
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor=COLOR_GRID,
            gridwidth=1,
            linecolor="#D1D5DB",
            tickfont=dict(color=COLOR_GRAY, size=10)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=COLOR_GRID,
            gridwidth=1,
            linecolor="#D1D5DB",
            tickfont=dict(color=COLOR_GRAY, size=10)
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor=COLOR_GRID,
            borderwidth=1,
            font=dict(size=10, color=COLOR_TEXT)
        )
    )
    return fig

# Backward-compatibility alias
def _apply_dark_theme(fig: go.Figure, height: int = 420) -> go.Figure:
    """Retained for backward compatibility with existing tests and scripts."""
    return _apply_editorial_theme(fig, height=height)

def plot_gold_price_history(norm_df: pd.DataFrame, symbols: Optional[List[str]] = None) -> go.Figure:
    """Plot historical normalized fine gold price per gram (999 pure gold equivalent) across MCX contracts."""
    fig = go.Figure()
    if norm_df.empty:
        return _apply_editorial_theme(fig)

    df = norm_df if not symbols else norm_df[norm_df['symbol'].isin(symbols)]
    df = df.copy()
    if 'days_to_expiry' not in df.columns and 'expiry_date' in df.columns and 'date' in df.columns:
        df['days_to_expiry'] = (pd.to_datetime(df['expiry_date']) - pd.to_datetime(df['date'])).dt.days
    
    # Prompt expiry: nearest expiry contract per symbol per trading date
    idx = df.groupby(['date', 'symbol'])['days_to_expiry'].idxmin()
    prompt_df = df.loc[idx].sort_values('date')
    
    color_map = {
        'GOLDM': COLOR_NAVY,
        'GOLDTEN': COLOR_GOLD,
        'GOLDGUINEA': COLOR_GREEN,
        'GOLDPETAL': COLOR_BLUE,
        'GOLD': COLOR_GRAY
    }
    
    for sym in prompt_df['symbol'].unique():
        sdf = prompt_df[prompt_df['symbol'] == sym]
        fig.add_trace(go.Scatter(
            x=sdf['date'],
            y=sdf['close_fine_per_gram'],
            name=f"{sym} (Prompt Expiry)",
            mode='lines',
            line=dict(color=color_map.get(sym, COLOR_GRAY), width=1.8),
            hovertemplate="<b>%{x|%d %b %Y}</b><br>Contract: " + sym + "<br>Normalized: ₹%{y:,.2f}/g<extra></extra>"
        ))
        
    fig.update_layout(
        title=dict(
            text="<b>Normalized Fine Gold Price (₹ / gram, 999 Fine Equivalent)</b>",
            font=dict(size=13, color=COLOR_TEXT)
        ),
        xaxis_title="Observation Date",
        yaxis_title="Normalized Price (₹ / g)"
    )
    return _apply_editorial_theme(fig, height=440)

def plot_candlestick_ohlc(norm_df: pd.DataFrame, contract_key: str) -> go.Figure:
    """Plot interactive candlestick OHLC chart with volume sub-chart for a specific contract."""
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=[0.74, 0.26],
        subplot_titles=(f"<b>{contract_key} — Quoted Price (₹)</b>", "<b>Traded Volume (Lots)</b>")
    )
    
    cdf = norm_df[norm_df['contract_key'] == contract_key].sort_values('date')
    if cdf.empty:
        return _apply_editorial_theme(fig)
        
    fig.add_trace(go.Candlestick(
        x=cdf['date'],
        open=cdf['open'],
        high=cdf['high'],
        low=cdf['low'],
        close=cdf['close'],
        name="OHLC Price",
        increasing_line_color=COLOR_GREEN,
        decreasing_line_color=COLOR_RED,
        increasing_fillcolor="rgba(13, 130, 68, 0.5)",
        decreasing_fillcolor="rgba(211, 47, 47, 0.5)",
    ), row=1, col=1)
    
    vol_colors = [COLOR_GREEN if c >= o else COLOR_RED for o, c in zip(cdf['open'], cdf['close'])]
    fig.add_trace(go.Bar(
        x=cdf['date'],
        y=cdf['volume_lots'],
        name="Volume (Lots)",
        marker=dict(color=vol_colors, line_width=0),
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Volume: %{y:,} lots<extra></extra>"
    ), row=2, col=1)
    
    fig.update_layout(xaxis_rangeslider_visible=False)
    fig.update_yaxes(title_text="Quoted Price (₹)", row=1, col=1)
    fig.update_yaxes(title_text="Lots", row=2, col=1)
    return _apply_editorial_theme(fig, height=480)

def plot_volume_and_oi(norm_df: pd.DataFrame, contract_key: str) -> go.Figure:
    """Plot dual-axis volume and open-interest dynamics for a specific contract."""
    cdf = norm_df[norm_df['contract_key'] == contract_key].sort_values('date')
    fig = go.Figure()
    if cdf.empty:
        return _apply_editorial_theme(fig)
        
    fig.add_trace(go.Bar(
        x=cdf['date'],
        y=cdf['volume_lots'],
        name="Traded Volume (Lots)",
        marker_color="rgba(37, 99, 235, 0.35)",
        yaxis="y"
    ))
    fig.add_trace(go.Scatter(
        x=cdf['date'],
        y=cdf['open_interest_lots'],
        name="Open Interest (Lots)",
        line=dict(color=COLOR_GOLD, width=2.2),
        yaxis="y2"
    ))
    
    fig.update_layout(
        title=dict(
            text=f"<b>Liquidity & Open Interest Dynamics: {contract_key}</b>",
            font=dict(size=13, color=COLOR_TEXT)
        ),
        xaxis=dict(title="Observation Date"),
        yaxis=dict(title="Volume (Lots)", side="left"),
        yaxis2=dict(title="Open Interest (Lots)", side="right", overlaying="y", showgrid=False)
    )
    return _apply_editorial_theme(fig, height=400)

def plot_cross_product_spread(radar_df: pd.DataFrame, pair_selection: Optional[str] = None) -> go.Figure:
    """Plot cross-product relative price spread (₹/g) over time with zero-basis line."""
    fig = go.Figure()
    if radar_df.empty:
        return _apply_editorial_theme(fig)
        
    df = radar_df.copy()
    if 'pair_key' not in df.columns:
        df['pair_key'] = df['symbol_leg_a'] + " vs " + df['symbol_leg_b']
    
    if pair_selection and pair_selection != "All Pairs":
        df = df[df['pair_key'] == pair_selection]
        
    df = df.sort_values('date')
    
    palette = [COLOR_NAVY, COLOR_GOLD, COLOR_GREEN, COLOR_BLUE, COLOR_PURPLE, COLOR_GRAY]
    
    for idx, pk in enumerate(df['pair_key'].unique()[:6]):
        pdf = df[df['pair_key'] == pk]
        color = palette[idx % len(palette)]
        fig.add_trace(go.Scatter(
            x=pdf['date'],
            y=pdf['fine_price_spread_per_gram'],
            name=pk,
            mode='lines',
            line=dict(color=color, width=1.6),
            hovertemplate="<b>%{x|%d %b %Y}</b><br>Pair: " + pk + "<br>Fine Spread: ₹%{y:,.2f}/g<extra></extra>"
        ))
        
    fig.add_hline(y=0.0, line_dash="dash", line_color=COLOR_GRAY, line_width=1, annotation_text="Zero Basis (Parity)")
    fig.update_layout(
        title=dict(
            text="<b>Cross-Product Price Spread Over Time (₹ / gram, 999 Fine Equivalent)</b>",
            font=dict(size=13, color=COLOR_TEXT)
        ),
        xaxis_title="Observation Date",
        yaxis_title="Fine Spread (₹ / g)"
    )
    return _apply_editorial_theme(fig, height=440)

def plot_spread_distribution_and_bands(pair_df: pd.DataFrame, pair_title: str = "") -> go.Figure:
    """Plot historical spread with 20-day rolling mean & ±2 sigma statistical bands."""
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=False,
        vertical_spacing=0.12,
        row_heights=[0.65, 0.35],
        subplot_titles=(f"<b>{pair_title} Spread with Rolling Statistical Bands (₹/g)</b>", "<b>Historical Spread Distribution</b>")
    )
    if pair_df.empty:
        return _apply_editorial_theme(fig)

    pdf = pair_df.sort_values('date').copy()
    spread_col = 'fine_price_spread_per_gram' if 'fine_price_spread_per_gram' in pdf.columns else 'quoted_price_difference_per_gram'
    
    # Calculate rolling statistics
    pdf['rolling_mean'] = pdf[spread_col].rolling(20, min_periods=5).mean()
    pdf['rolling_std'] = pdf[spread_col].rolling(20, min_periods=5).std()
    pdf['upper_band'] = pdf['rolling_mean'] + 2 * pdf['rolling_std']
    pdf['lower_band'] = pdf['rolling_mean'] - 2 * pdf['rolling_std']

    # Subplot 1: Spread with bands
    fig.add_trace(go.Scatter(
        x=pdf['date'], y=pdf['upper_band'],
        name="+2σ Band", line=dict(color="rgba(114, 121, 133, 0.4)", dash="dot", width=1),
        showlegend=False
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=pdf['date'], y=pdf['lower_band'],
        name="-2σ Band", line=dict(color="rgba(114, 121, 133, 0.4)", dash="dot", width=1),
        fill='tonexty', fillcolor="rgba(184, 145, 55, 0.05)",
        showlegend=False
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=pdf['date'], y=pdf['rolling_mean'],
        name="20-Session Mean", line=dict(color=COLOR_GOLD, width=1.4),
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=pdf['date'], y=pdf[spread_col],
        name="Fine Spread", line=dict(color=COLOR_NAVY, width=1.8),
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Spread: ₹%{y:,.2f}/g<extra></extra>"
    ), row=1, col=1)

    # Subplot 2: Histogram
    spread_vals = pdf[spread_col].dropna()
    fig.add_trace(go.Histogram(
        x=spread_vals,
        nbinsx=35,
        marker=dict(color="rgba(37, 99, 235, 0.6)", line=dict(color="#FFFFFF", width=0.5)),
        name="Spread Density",
        hovertemplate="Spread: ₹%{x:,.2f}/g<br>Count: %{y}<extra></extra>"
    ), row=2, col=1)

    fig.update_yaxes(title_text="Spread (₹/g)", row=1, col=1)
    fig.update_xaxes(title_text="Spread Bin (₹/g)", row=2, col=1)
    fig.update_yaxes(title_text="Count", row=2, col=1)

    return _apply_editorial_theme(fig, height=520)

def plot_term_structure_curve(snapshots_df: pd.DataFrame, snapshot_date: pd.Timestamp, symbol: Optional[str] = None) -> go.Figure:
    """Plot MCX gold futures term structure curve across chronological actual expiries."""
    fig = go.Figure()
    if snapshots_df.empty:
        return _apply_editorial_theme(fig)
        
    sdf = snapshots_df[snapshots_df['date'] == pd.to_datetime(snapshot_date)].copy()
    if symbol and symbol != "All Contracts" and symbol != "All Symbols":
        sdf = sdf[sdf['symbol'] == symbol]
        
    sdf = sdf.sort_values('expiry_date')
    
    color_map = {
        'GOLDM': COLOR_NAVY,
        'GOLDTEN': COLOR_GOLD,
        'GOLDGUINEA': COLOR_GREEN,
        'GOLDPETAL': COLOR_BLUE,
        'GOLD': COLOR_GRAY
    }
    
    for sym in sdf['symbol'].unique():
        sym_df = sdf[sdf['symbol'] == sym]
        fig.add_trace(go.Scatter(
            x=sym_df['expiry_date'].dt.strftime('%d-%b-%Y'),
            y=sym_df['close_fine_per_gram'],
            name=f"{sym}",
            mode='lines+markers',
            marker=dict(size=8, color=color_map.get(sym, COLOR_NAVY)),
            line=dict(color=color_map.get(sym, COLOR_NAVY), width=2),
            hovertemplate="<b>Expiry: %{x}</b><br>Contract: " + sym + "<br>Fine Price: ₹%{y:,.2f}/g<extra></extra>"
        ))
        
    date_str = pd.to_datetime(snapshot_date).strftime('%d %b %Y')
    fig.update_layout(
        title=dict(
            text=f"<b>MCX Gold Term Structure Forward Curve ({date_str})</b>",
            font=dict(size=13, color=COLOR_TEXT)
        ),
        xaxis_title="Contract Expiry Date (Chronological)",
        yaxis_title="Normalized Fine Price (₹ / g)"
    )
    return _apply_editorial_theme(fig, height=400)

def plot_annualized_roll_yield(term_df: pd.DataFrame, symbol: Optional[str] = None) -> go.Figure:
    """Plot calendar spread annualized roll yield (%) over time."""
    fig = go.Figure()
    if term_df.empty:
        return _apply_editorial_theme(fig)
        
    df = term_df if not symbol or symbol in ["All Contracts", "All Symbols"] else term_df[term_df['symbol'] == symbol]
    df = df.sort_values('date')
    
    daily = df.groupby('date')['fine_annualized_spread_pct'].agg(['median', 'min', 'max']).reset_index()
    
    fig.add_trace(go.Scatter(
        x=daily['date'],
        y=daily['median'],
        name="Median Annualized Contango (%)",
        line=dict(color=COLOR_NAVY, width=1.8),
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Annualized Spread: %{y:.2f}%<extra></extra>"
    ))
    fig.add_hline(y=0.0, line_dash="dash", line_color=COLOR_RED, line_width=1, annotation_text="Contango / Backwardation Parity (0%)")
    
    fig.update_layout(
        title=dict(
            text="<b>Calendar Spread Annualized Roll Yield Over Time (%)</b>",
            font=dict(size=13, color=COLOR_TEXT)
        ),
        xaxis_title="Observation Date",
        yaxis_title="Annualized Roll Yield (%)"
    )
    return _apply_editorial_theme(fig, height=400)

def plot_cumulative_realized_pnl(equity_df: pd.DataFrame, title_prefix: str = "") -> go.Figure:
    """Plot chronological cumulative realized P&L curve with high-water mark and drawdown subplot."""
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=[0.72, 0.28],
        subplot_titles=(f"<b>{title_prefix} Cumulative Realized P&L (₹)</b>", "<b>Realized Drawdown from Peak (₹)</b>")
    )
    
    if equity_df.empty:
        return _apply_editorial_theme(fig)
        
    last_pnl = equity_df['cum_net_pnl'].iloc[-1]
    pnl_color = COLOR_GREEN if last_pnl >= 0 else COLOR_RED
    
    # Main equity curve
    fig.add_trace(go.Scatter(
        x=equity_df['exit_date'],
        y=equity_df['cum_net_pnl'],
        name="Net Realized Equity",
        line=dict(color=pnl_color, width=2.2),
        fill='tozeroy',
        fillcolor="rgba(13, 130, 68, 0.08)" if last_pnl >= 0 else "rgba(211, 47, 47, 0.08)",
        hovertemplate="<b>Exit: %{x|%d %b %Y}</b><br>Cum Net P&L: ₹%{y:,.2f}<extra></extra>"
    ), row=1, col=1)
    
    # High Water Mark
    fig.add_trace(go.Scatter(
        x=equity_df['exit_date'],
        y=equity_df['running_peak'],
        name="High-Water Mark",
        line=dict(color=COLOR_GOLD, dash="dash", width=1.4),
        hovertemplate="<b>Exit: %{x|%d %b %Y}</b><br>Peak: ₹%{y:,.2f}<extra></extra>"
    ), row=1, col=1)
    
    # Drawdown Subplot
    fig.add_trace(go.Scatter(
        x=equity_df['exit_date'],
        y=-equity_df['drawdown'],
        name="Drawdown (₹)",
        line=dict(color=COLOR_RED, width=1.4),
        fill='tozeroy',
        fillcolor="rgba(211, 47, 47, 0.12)",
        hovertemplate="<b>Exit: %{x|%d %b %Y}</b><br>Drawdown: -₹%{text:,.2f}<extra></extra>",
        text=equity_df['drawdown']
    ), row=2, col=1)
    
    fig.update_yaxes(title_text="Realized P&L (₹)", row=1, col=1)
    fig.update_yaxes(title_text="Drawdown (₹)", row=2, col=1)
    return _apply_editorial_theme(fig, height=480)

def plot_pnl_distribution(comp_trades_df: pd.DataFrame) -> go.Figure:
    """Plot trade-level Net Realized P&L distribution histogram."""
    fig = go.Figure()
    if comp_trades_df.empty:
        return _apply_editorial_theme(fig)
        
    pnl = comp_trades_df['net_pnl_inr']
    fig.add_trace(go.Histogram(
        x=pnl,
        nbinsx=35,
        marker=dict(
            color=np.where(comp_trades_df['net_pnl_inr'] >= 0, COLOR_GREEN, COLOR_RED),
            line=dict(color=COLOR_SURFACE, width=1)
        ),
        hovertemplate="P&L Bin: ₹%{x:,.2f}<br>Trades: %{y}<extra></extra>"
    ))
    fig.add_vline(x=0.0, line_dash="dash", line_color=COLOR_GRAY, annotation_text="Breakeven (₹0)")
    fig.add_vline(x=pnl.mean(), line_dash="dot", line_color=COLOR_GOLD, annotation_text=f"Mean: ₹{pnl.mean():,.2f}")
    
    fig.update_layout(
        title=dict(
            text="<b>Trade-Level Net Realized P&L Distribution (₹)</b>",
            font=dict(size=13, color=COLOR_TEXT)
        ),
        xaxis_title="Net Realized P&L (₹)",
        yaxis_title="Trade Count"
    )
    return _apply_editorial_theme(fig, height=380)

def plot_walk_forward_fold_performance(metrics_df: pd.DataFrame, cost_scenario: str = "base") -> go.Figure:
    """Plot walk-forward fold net P&L comparison across strategies."""
    fig = go.Figure()
    if metrics_df.empty:
        return _apply_editorial_theme(fig)
        
    mdf = metrics_df[metrics_df['cost_scenario'] == cost_scenario]
    
    for sname in mdf['strategy_name'].unique():
        smdf = mdf[mdf['strategy_name'] == sname].sort_values('fold_id')
        display_name = "Strategy A (Cross-Product)" if "cross_product" in sname else "Strategy B (Calendar Spread)"
        color = COLOR_GOLD if "cross_product" in sname else COLOR_NAVY
        fig.add_trace(go.Bar(
            x=smdf['fold_id'],
            y=smdf['net_pnl_inr'],
            name=display_name,
            marker_color=color,
            hovertemplate="<b>%{x}</b><br>" + display_name + "<br>Net P&L: ₹%{y:,.2f}<br>Win Rate: %{text:.1f}%<extra></extra>",
            text=smdf['win_rate_pct']
        ))
        
    fig.add_hline(y=0.0, line_color=COLOR_GRAY, line_width=1)
    fig.update_layout(
        barmode='group',
        title=dict(
            text=f"<b>Walk-Forward Out-of-Sample Fold Performance ({cost_scenario.upper()} Scenario)</b>",
            font=dict(size=13, color=COLOR_TEXT)
        ),
        xaxis_title="Walk-Forward Fold Window",
        yaxis_title="Net Realized P&L (₹)"
    )
    return _apply_editorial_theme(fig, height=400)

def plot_cost_scenarios_comparison(summary_df: pd.DataFrame) -> go.Figure:
    """Plot side-by-side comparison of Gross P&L, Modeled Costs, and Net P&L across scenarios."""
    fig = go.Figure()
    if summary_df.empty:
        return _apply_editorial_theme(fig)
        
    for metric, label, color in [
        ('gross_pnl_inr', 'Gross P&L', COLOR_BLUE),
        ('total_costs_inr', 'Modeled Statutory Costs', COLOR_RED),
        ('net_pnl_inr', 'Net Realized P&L', COLOR_GREEN)
    ]:
        fig.add_trace(go.Bar(
            x=summary_df['strategy_name'] + " (" + summary_df['cost_scenario'].str.upper() + ")",
            y=summary_df[metric],
            name=label,
            marker_color=color,
            hovertemplate="<b>%{x}</b><br>" + label + ": ₹%{y:,.2f}<extra></extra>"
        ))
        
    fig.update_layout(
        barmode='group',
        title=dict(
            text="<b>Strategy Performance vs Transaction Cost Regimes (Low, Base, High)</b>",
            font=dict(size=13, color=COLOR_TEXT)
        ),
        xaxis_title="Strategy & Cost Regime",
        yaxis_title="Amount (₹)"
    )
    return _apply_editorial_theme(fig, height=420)

def plot_execution_diagnostics_chart(diag_df: pd.DataFrame) -> go.Figure:
    """Plot execution rejections and diagnostics breakdown."""
    fig = go.Figure()
    if diag_df.empty:
        return _apply_editorial_theme(fig)
        
    rejs = diag_df[diag_df['diagnostic_category'] == 'Execution Rejections'].copy()
    rejs = rejs.sort_values('count', ascending=True)
    
    fig.add_trace(go.Bar(
        y=rejs['metric_name'],
        x=rejs['count'],
        orientation='h',
        marker_color=COLOR_NAVY,
        hovertemplate="<b>%{y}</b><br>Excluded Attempts: %{x:,}<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(
            text="<b>Candidate Exclusion Breakdown (Audit Diagnostics)</b>",
            font=dict(size=13, color=COLOR_TEXT)
        ),
        xaxis_title="Candidate Attempts Excluded",
        yaxis_title="Exclusion Reason"
    )
    return _apply_editorial_theme(fig, height=380)
