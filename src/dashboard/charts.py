"""
Gold Contract Radar — MCX Commodity Derivatives Intelligence
Interactive Plotly Financial Chart Library
"""

from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Premium Dark Financial Palette
COLOR_GOLD = "#D4AF37"
COLOR_GOLD_LIGHT = "#F5B041"
COLOR_GREEN = "#00C853"
COLOR_RED = "#FF3D00"
COLOR_BLUE = "#29B6F6"
COLOR_PURPLE = "#AB47BC"
COLOR_GRAY = "#78909C"
COLOR_BG = "#0E1117"
COLOR_CARD = "#161B22"
COLOR_GRID = "#21262D"

def _apply_dark_theme(fig: go.Figure, height: int = 450) -> go.Figure:
    """Apply unified responsive dark styling to a Plotly figure."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=50, b=40),
        height=height,
        font=dict(family="Inter, Roboto, sans-serif", size=12, color="#E6EDF3"),
        hoverlabel=dict(bgcolor=COLOR_CARD, font_size=12, font_color="#FFFFFF"),
        xaxis=dict(showgrid=True, gridcolor=COLOR_GRID, linecolor="#30363D"),
        yaxis=dict(showgrid=True, gridcolor=COLOR_GRID, linecolor="#30363D"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(22, 27, 34, 0.7)",
            bordercolor=COLOR_GRID
        )
    )
    return fig

def plot_gold_price_history(norm_df: pd.DataFrame, symbols: Optional[List[str]] = None) -> go.Figure:
    """Plot historical fine gold price per gram (999 fine equivalent) across MCX contracts."""
    fig = go.Figure()
    if norm_df.empty:
        return _apply_dark_theme(fig)

    df = norm_df if not symbols else norm_df[norm_df['symbol'].isin(symbols)]
    df = df.copy()
    if 'days_to_expiry' not in df.columns and 'expiry_date' in df.columns and 'date' in df.columns:
        df['days_to_expiry'] = (pd.to_datetime(df['expiry_date']) - pd.to_datetime(df['date'])).dt.days
    
    # Representative prompt price: nearest expiry per symbol per date
    idx = df.groupby(['date', 'symbol'])['days_to_expiry'].idxmin()
    prompt_df = df.loc[idx].sort_values('date')
    
    color_map = {
        'GOLD': COLOR_GOLD,
        'GOLDM': COLOR_BLUE,
        'GOLDTEN': COLOR_PURPLE,
        'GOLDGUINEA': COLOR_GREEN,
        'GOLDPETAL': COLOR_GOLD_LIGHT
    }
    
    for sym in prompt_df['symbol'].unique():
        sdf = prompt_df[prompt_df['symbol'] == sym]
        fig.add_trace(go.Scatter(
            x=sdf['date'],
            y=sdf['close_fine_per_gram'],
            name=f"{sym} (Prompt Expiry)",
            mode='lines',
            line=dict(color=color_map.get(sym, COLOR_GRAY), width=1.8),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Symbol: " + sym + "<br>Fine Price: ₹%{y:,.2f}/g<extra></extra>"
        ))
        
    fig.update_layout(
        title="<b>MCX Gold Normalized Fine Price Trend (₹ / gram, 999 Fine Equivalent)</b>",
        xaxis_title="Observation Date",
        yaxis_title="Normalized Price (₹ / g)"
    )
    return _apply_dark_theme(fig, height=480)

def plot_candlestick_ohlc(norm_df: pd.DataFrame, contract_key: str) -> go.Figure:
    """Plot interactive candlestick OHLC chart with volume sub-chart for a specific contract."""
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.75, 0.25],
        subplot_titles=(f"<b>{contract_key} — Price Quotation (₹)</b>", "<b>Traded Volume (Lots)</b>")
    )
    
    cdf = norm_df[norm_df['contract_key'] == contract_key].sort_values('date')
    if cdf.empty:
        return _apply_dark_theme(fig)
        
    fig.add_trace(go.Candlestick(
        x=cdf['date'],
        open=cdf['open'],
        high=cdf['high'],
        low=cdf['low'],
        close=cdf['close'],
        name="OHLC Price",
        increasing_line_color=COLOR_GREEN,
        decreasing_line_color=COLOR_RED,
        increasing_fillcolor="rgba(0, 200, 83, 0.4)",
        decreasing_fillcolor="rgba(255, 61, 0, 0.4)",
    ), row=1, col=1)
    
    vol_colors = [COLOR_GREEN if c >= o else COLOR_RED for o, c in zip(cdf['open'], cdf['close'])]
    fig.add_trace(go.Bar(
        x=cdf['date'],
        y=cdf['volume_lots'],
        name="Volume (Lots)",
        marker=dict(color=vol_colors, line_width=0),
        hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Volume: %{y:,} lots<extra></extra>"
    ), row=2, col=1)
    
    fig.update_layout(xaxis_rangeslider_visible=False)
    fig.update_yaxes(title_text="Quoted Price (₹)", row=1, col=1)
    fig.update_yaxes(title_text="Lots", row=2, col=1)
    return _apply_dark_theme(fig, height=520)

def plot_volume_and_oi(norm_df: pd.DataFrame, contract_key: str) -> go.Figure:
    """Plot dual-axis volume and open-interest dynamics for a specific contract."""
    cdf = norm_df[norm_df['contract_key'] == contract_key].sort_values('date')
    fig = go.Figure()
    if cdf.empty:
        return _apply_dark_theme(fig)
        
    fig.add_trace(go.Bar(
        x=cdf['date'],
        y=cdf['volume_lots'],
        name="Traded Volume (Lots)",
        marker_color="rgba(41, 182, 246, 0.4)",
        yaxis="y"
    ))
    fig.add_trace(go.Scatter(
        x=cdf['date'],
        y=cdf['open_interest_lots'],
        name="Open Interest (Lots)",
        line=dict(color=COLOR_GOLD, width=2.5),
        yaxis="y2"
    ))
    
    fig.update_layout(
        title=f"<b>Liquidity & Open Interest Dynamics: {contract_key}</b>",
        xaxis=dict(title="Date"),
        yaxis=dict(title="Volume (Lots)", side="left"),
        yaxis2=dict(title="Open Interest (Lots)", side="right", overlaying="y", showgrid=False)
    )
    return _apply_dark_theme(fig, height=450)

def plot_cross_product_spread(radar_df: pd.DataFrame, pair_selection: Optional[str] = None) -> go.Figure:
    """Plot cross-product relative price spread (₹/g) over time."""
    fig = go.Figure()
    if radar_df.empty:
        return _apply_dark_theme(fig)
        
    df = radar_df.copy()
    df['pair_key'] = df['symbol_leg_a'] + " vs " + df['symbol_leg_b']
    
    if pair_selection and pair_selection != "All Pairs":
        df = df[df['pair_key'] == pair_selection]
        
    df = df.sort_values('date')
    
    for pk in df['pair_key'].unique()[:6]:  # Limit top 6 for visual clarity
        pdf = df[df['pair_key'] == pk]
        fig.add_trace(go.Scatter(
            x=pdf['date'],
            y=pdf['fine_price_spread_per_gram'],
            name=pk,
            mode='lines',
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Pair: " + pk + "<br>Fine Spread: ₹%{y:,.2f}/g<extra></extra>"
        ))
        
    fig.add_hline(y=0.0, line_dash="dash", line_color=COLOR_GRAY, annotation_text="Zero Basis")
    fig.update_layout(
        title="<b>Cross-Product Price Spread Over Time (₹ / gram, 999 Fine Equivalent)</b>",
        xaxis_title="Observation Date",
        yaxis_title="Fine Gold Price Difference (₹ / g)"
    )
    return _apply_dark_theme(fig, height=480)

def plot_term_structure_curve(snapshots_df: pd.DataFrame, snapshot_date: pd.Timestamp, symbol: Optional[str] = None) -> go.Figure:
    """Plot MCX gold term structure curve across expiries on a specific date."""
    fig = go.Figure()
    if snapshots_df.empty:
        return _apply_dark_theme(fig)
        
    sdf = snapshots_df[snapshots_df['date'] == pd.to_datetime(snapshot_date)].copy()
    if symbol and symbol != "All Symbols":
        sdf = sdf[sdf['symbol'] == symbol]
        
    sdf = sdf.sort_values('expiry_date')
    
    color_map = {'GOLD': COLOR_GOLD, 'GOLDM': COLOR_BLUE, 'GOLDTEN': COLOR_PURPLE, 'GOLDGUINEA': COLOR_GREEN, 'GOLDPETAL': COLOR_GOLD_LIGHT}
    
    for sym in sdf['symbol'].unique():
        sym_df = sdf[sdf['symbol'] == sym]
        fig.add_trace(go.Scatter(
            x=sym_df['expiry_date'].dt.strftime('%d-%b-%Y'),
            y=sym_df['close_fine_per_gram'],
            name=f"{sym} Term Curve",
            mode='lines+markers',
            marker=dict(size=8, color=color_map.get(sym, COLOR_GOLD)),
            line=dict(color=color_map.get(sym, COLOR_GOLD), width=2),
            hovertemplate="<b>Expiry: %{x}</b><br>Fine Price: ₹%{y:,.2f}/g<extra></extra>"
        ))
        
    date_str = pd.to_datetime(snapshot_date).strftime('%Y-%m-%d')
    fig.update_layout(
        title=f"<b>MCX Gold Futures Term Structure Curve ({date_str})</b>",
        xaxis_title="Contract Expiry Date (Chronological)",
        yaxis_title="Normalized Fine Price (₹ / g)"
    )
    return _apply_dark_theme(fig, height=450)

def plot_annualized_roll_yield(term_df: pd.DataFrame, symbol: Optional[str] = None) -> go.Figure:
    """Plot calendar spread annualized roll yield (%) over time."""
    fig = go.Figure()
    if term_df.empty:
        return _apply_dark_theme(fig)
        
    df = term_df if not symbol or symbol == "All Symbols" else term_df[term_df['symbol'] == symbol]
    df = df.sort_values('date')
    
    # Group by date to show median and interquartile spread
    daily = df.groupby('date')['fine_annualized_spread_pct'].agg(['median', 'min', 'max']).reset_index()
    
    fig.add_trace(go.Scatter(
        x=daily['date'],
        y=daily['median'],
        name="Median Annualized Spread (%)",
        line=dict(color=COLOR_GOLD, width=2),
        hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Annualized Contango: %{y:.2f}%<extra></extra>"
    ))
    fig.add_hline(y=0.0, line_dash="dash", line_color=COLOR_RED, annotation_text="Contango / Backwardation Parity (0%)")
    
    fig.update_layout(
        title="<b>MCX Gold Calendar Spread Annualized Roll Yield Over Time (%)</b>",
        xaxis_title="Observation Date",
        yaxis_title="Annualized Spread (%)"
    )
    return _apply_dark_theme(fig, height=450)

def plot_cumulative_realized_pnl(equity_df: pd.DataFrame, title_prefix: str = "") -> go.Figure:
    """Plot chronological cumulative realized P&L curve with high-water mark and drawdown."""
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.72, 0.28],
        subplot_titles=(f"<b>{title_prefix} Cumulative Realized P&L (₹)</b>", "<b>Realized Drawdown from Peak (₹)</b>")
    )
    
    if equity_df.empty:
        return _apply_dark_theme(fig)
        
    # Main equity curve
    fig.add_trace(go.Scatter(
        x=equity_df['exit_date'],
        y=equity_df['cum_net_pnl'],
        name="Cumulative Net Realized P&L",
        line=dict(color=COLOR_GREEN if equity_df['cum_net_pnl'].iloc[-1] >= 0 else COLOR_RED, width=2.2),
        fill='tozeroy',
        fillcolor="rgba(0, 200, 83, 0.1)" if equity_df['cum_net_pnl'].iloc[-1] >= 0 else "rgba(255, 61, 0, 0.1)",
        hovertemplate="<b>Exit: %{x|%Y-%m-%d}</b><br>Cum Net P&L: ₹%{y:,.2f}<extra></extra>"
    ), row=1, col=1)
    
    # Running Peak (High Water Mark)
    fig.add_trace(go.Scatter(
        x=equity_df['exit_date'],
        y=equity_df['running_peak'],
        name="High-Water Mark",
        line=dict(color=COLOR_GOLD, dash="dash", width=1.5),
        hovertemplate="<b>Exit: %{x|%Y-%m-%d}</b><br>Peak: ₹%{y:,.2f}<extra></extra>"
    ), row=1, col=1)
    
    # Drawdown Subplot
    fig.add_trace(go.Scatter(
        x=equity_df['exit_date'],
        y=-equity_df['drawdown'],
        name="Drawdown (₹)",
        line=dict(color=COLOR_RED, width=1.5),
        fill='tozeroy',
        fillcolor="rgba(255, 61, 0, 0.2)",
        hovertemplate="<b>Exit: %{x|%Y-%m-%d}</b><br>Drawdown: -₹%{text:,.2f}<extra></extra>",
        text=equity_df['drawdown']
    ), row=2, col=1)
    
    fig.update_yaxes(title_text="Realized P&L (₹)", row=1, col=1)
    fig.update_yaxes(title_text="Drawdown (₹)", row=2, col=1)
    return _apply_dark_theme(fig, height=520)

def plot_pnl_distribution(comp_trades_df: pd.DataFrame) -> go.Figure:
    """Plot trade-level Net Realized P&L distribution histogram."""
    fig = go.Figure()
    if comp_trades_df.empty:
        return _apply_dark_theme(fig)
        
    pnl = comp_trades_df['net_pnl_inr']
    fig.add_trace(go.Histogram(
        x=pnl,
        nbinsx=40,
        marker=dict(
            color=np.where(comp_trades_df['net_pnl_inr'] >= 0, COLOR_GREEN, COLOR_RED),
            line=dict(color="#30363D", width=1)
        ),
        hovertemplate="P&L Bin: ₹%{x:,.2f}<br>Count: %{y}<extra></extra>"
    ))
    fig.add_vline(x=0.0, line_dash="dash", line_color="#FFFFFF", annotation_text="Breakeven (₹0)")
    fig.add_vline(x=pnl.mean(), line_dash="dot", line_color=COLOR_GOLD, annotation_text=f"Mean: ₹{pnl.mean():,.2f}")
    
    fig.update_layout(
        title="<b>Trade-Level Net Realized P&L Distribution (₹)</b>",
        xaxis_title="Net Realized P&L (₹)",
        yaxis_title="Trade Count"
    )
    return _apply_dark_theme(fig, height=420)

def plot_walk_forward_fold_performance(metrics_df: pd.DataFrame, cost_scenario: str = "base") -> go.Figure:
    """Plot walk-forward fold net P&L comparison across strategies."""
    fig = go.Figure()
    if metrics_df.empty:
        return _apply_dark_theme(fig)
        
    mdf = metrics_df[metrics_df['cost_scenario'] == cost_scenario]
    
    for sname in mdf['strategy_name'].unique():
        smdf = mdf[mdf['strategy_name'] == sname].sort_values('fold_id')
        display_name = "Strategy A (Cross-Product)" if "cross_product" in sname else "Strategy B (Calendar Spread)"
        color = COLOR_GOLD if "cross_product" in sname else COLOR_BLUE
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
        title=f"<b>Walk-Forward Out-of-Sample Fold Performance ({cost_scenario.upper()} Scenario)</b>",
        xaxis_title="Walk-Forward Fold (Chronological)",
        yaxis_title="Net Realized P&L (₹)"
    )
    return _apply_dark_theme(fig, height=450)

def plot_cost_scenarios_comparison(summary_df: pd.DataFrame) -> go.Figure:
    """Plot side-by-side comparison of Gross P&L, Modeled Costs, and Net P&L across scenarios."""
    fig = go.Figure()
    if summary_df.empty:
        return _apply_dark_theme(fig)
        
    scenarios = summary_df['cost_scenario'].unique()
    
    for metric, label, color in [
        ('gross_pnl_inr', 'Gross P&L', COLOR_BLUE),
        ('total_costs_inr', 'Modeled Transaction Costs', COLOR_RED),
        ('net_pnl_inr', 'Net Realized P&L', COLOR_GREEN)
    ]:
        fig.add_trace(go.Bar(
            x=summary_df['strategy_name'] + " (" + summary_df['cost_scenario'] + ")",
            y=summary_df[metric],
            name=label,
            marker_color=color,
            hovertemplate="<b>%{x}</b><br>" + label + ": ₹%{y:,.2f}<extra></extra>"
        ))
        
    fig.update_layout(
        barmode='group',
        title="<b>Strategy Performance vs Transaction Cost Scenarios (Low, Base, High)</b>",
        xaxis_title="Strategy & Scenario",
        yaxis_title="Amount (₹)"
    )
    return _apply_dark_theme(fig, height=480)

def plot_execution_diagnostics_chart(diag_df: pd.DataFrame) -> go.Figure:
    """Plot execution rejections and diagnostics breakdown."""
    fig = go.Figure()
    if diag_df.empty:
        return _apply_dark_theme(fig)
        
    rejs = diag_df[diag_df['diagnostic_category'] == 'Execution Rejections'].copy()
    rejs = rejs.sort_values('count', ascending=True)
    
    fig.add_trace(go.Bar(
        y=rejs['metric_name'],
        x=rejs['count'],
        orientation='h',
        marker_color=COLOR_GOLD_LIGHT,
        hovertemplate="<b>%{y}</b><br>Count: %{x:,} rejections<extra></extra>"
    ))
    
    fig.update_layout(
        title="<b>Execution Rejection Breakdown (Audit Diagnostics)</b>",
        xaxis_title="Rejected Candidate Attempts",
        yaxis_title="Rejection Reason"
    )
    return _apply_dark_theme(fig, height=450)
