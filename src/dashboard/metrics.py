"""
Gold Contract Radar — MCX Commodity Derivatives Intelligence
KPI Calculations, Financial Transformations, and Reconciliation Checks
"""

from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np

def filter_trades(
    trades_df: pd.DataFrame,
    cost_scenario: str = "base",
    strategy_name: Optional[str] = None,
    fold_id: Optional[str] = None,
    trade_status: Optional[str] = None,
    date_range: Optional[Tuple[pd.Timestamp, pd.Timestamp]] = None
) -> pd.DataFrame:
    """
    Filter trade records with strict isolation of cost scenarios to prevent double counting.
    Returns an immutable copy.
    """
    if trades_df.empty:
        return trades_df.copy()

    df = trades_df.copy()
    
    # 1. Mandatory single-scenario isolation
    if cost_scenario and 'cost_scenario' in df.columns:
        df = df[df['cost_scenario'] == cost_scenario]
        
    # 2. Strategy filtering
    if strategy_name and strategy_name != "All Strategies" and 'strategy_name' in df.columns:
        df = df[df['strategy_name'] == strategy_name]
        
    # 3. Fold filtering
    if fold_id and fold_id != "All Folds" and 'fold_id' in df.columns:
        df = df[df['fold_id'] == fold_id]
        
    # 4. Status filtering
    if trade_status and trade_status != "All Statuses" and 'trade_completion_status' in df.columns:
        df = df[df['trade_completion_status'] == trade_status]
        
    # 5. Date range filtering (by signal_date)
    if date_range and len(date_range) == 2 and 'signal_date' in df.columns:
        start_date, end_date = date_range
        if pd.notnull(start_date) and pd.notnull(end_date):
            df = df[(df['signal_date'] >= pd.to_datetime(start_date)) & (df['signal_date'] <= pd.to_datetime(end_date))]
            
    return df

def calculate_trade_kpis(trades_df: pd.DataFrame, cost_scenario: str = "base") -> Dict[str, Any]:
    """
    Calculate executive trading KPIs strictly from completed trades of a single cost scenario.
    """
    if trades_df.empty:
        return {
            'trade_attempts': 0, 'completed_trades': 0, 'rejected_trades': 0, 'unresolved_trades': 0,
            'completion_rate_pct': 0.0, 'winning_trades': 0, 'losing_trades': 0, 'win_rate_pct': 0.0,
            'gross_pnl_inr': 0.0, 'total_costs_inr': 0.0, 'net_pnl_inr': 0.0,
            'mean_net_pnl_per_trade_inr': 0.0, 'median_net_pnl_per_trade_inr': 0.0,
            'mean_net_pnl_per_gram': 0.0, 'profit_factor': 0.0, 'realized_max_drawdown_inr': 0.0,
            'mean_holding_days': 0.0, 'pnl_reconciled': True, 'max_reconciliation_diff': 0.0
        }

    # Strict scenario filtering
    sc_df = trades_df[trades_df['cost_scenario'] == cost_scenario] if 'cost_scenario' in trades_df.columns else trades_df
    total_attempts = len(sc_df)
    
    comp = sc_df[sc_df['trade_completion_status'] == 'COMPLETED']
    rej = sc_df[sc_df['trade_completion_status'] == 'REJECTED']
    unres = sc_df[sc_df['trade_completion_status'] == 'UNRESOLVED']
    
    n_comp = len(comp)
    n_rej = len(rej)
    n_unres = len(unres)
    comp_rate = (n_comp / total_attempts * 100.0) if total_attempts > 0 else 0.0
    
    if n_comp == 0:
        return {
            'trade_attempts': total_attempts, 'completed_trades': 0, 'rejected_trades': n_rej, 'unresolved_trades': n_unres,
            'completion_rate_pct': comp_rate, 'winning_trades': 0, 'losing_trades': 0, 'win_rate_pct': 0.0,
            'gross_pnl_inr': 0.0, 'total_costs_inr': 0.0, 'net_pnl_inr': 0.0,
            'mean_net_pnl_per_trade_inr': 0.0, 'median_net_pnl_per_trade_inr': 0.0,
            'mean_net_pnl_per_gram': 0.0, 'profit_factor': 0.0, 'realized_max_drawdown_inr': 0.0,
            'mean_holding_days': 0.0, 'pnl_reconciled': True, 'max_reconciliation_diff': 0.0
        }
        
    wins = comp[comp['net_pnl_inr'] > 0]
    losses = comp[comp['net_pnl_inr'] <= 0]
    n_wins = len(wins)
    n_losses = len(losses)
    win_rate = (n_wins / n_comp * 100.0) if n_comp > 0 else 0.0
    
    gross_pnl = float(comp['gross_pnl_inr'].sum())
    tot_costs = float(comp['total_modeled_cost_inr'].sum())
    net_pnl = float(comp['net_pnl_inr'].sum())
    
    # Financial reconciliation check
    pnl_diff = (comp['gross_pnl_inr'] - comp['total_modeled_cost_inr']) - comp['net_pnl_inr']
    max_diff = float(pnl_diff.abs().max()) if n_comp > 0 else 0.0
    is_reconciled = max_diff < 1e-4
    
    mean_pnl = float(comp['net_pnl_inr'].mean())
    median_pnl = float(comp['net_pnl_inr'].median())
    mean_pnl_g = float(comp['net_pnl_per_gram'].mean()) if 'net_pnl_per_gram' in comp.columns else 0.0
    
    tot_win_inr = float(wins['net_pnl_inr'].sum()) if len(wins) > 0 else 0.0
    tot_loss_inr = float(abs(losses['net_pnl_inr'].sum())) if len(losses) > 0 else 0.0
    profit_factor = (tot_win_inr / tot_loss_inr) if tot_loss_inr > 0 else np.nan
    
    # Realized P&L drawdown
    if n_comp > 1 and 'exit_date' in comp.columns:
        sorted_comp = comp.sort_values(by=['exit_date', 'trade_id'])
        cum_pnl = sorted_comp['net_pnl_inr'].cumsum()
        running_peak = cum_pnl.cummax()
        dd = running_peak - cum_pnl
        max_dd = float(dd.max())
    else:
        max_dd = 0.0
        
    mean_holding = float(comp['holding_period_days'].mean()) if 'holding_period_days' in comp.columns else 0.0
    
    return {
        'trade_attempts': total_attempts,
        'completed_trades': n_comp,
        'rejected_trades': n_rej,
        'unresolved_trades': n_unres,
        'completion_rate_pct': comp_rate,
        'winning_trades': n_wins,
        'losing_trades': n_losses,
        'win_rate_pct': win_rate,
        'gross_pnl_inr': gross_pnl,
        'total_costs_inr': tot_costs,
        'net_pnl_inr': net_pnl,
        'mean_net_pnl_per_trade_inr': mean_pnl,
        'median_net_pnl_per_trade_inr': median_pnl,
        'mean_net_pnl_per_gram': mean_pnl_g,
        'profit_factor': profit_factor,
        'realized_max_drawdown_inr': max_dd,
        'mean_holding_days': mean_holding,
        'pnl_reconciled': is_reconciled,
        'max_reconciliation_diff': max_diff
    }

def build_cumulative_equity_series(comp_trades_df: pd.DataFrame) -> pd.DataFrame:
    """
    Construct strictly chronological cumulative realized P&L equity curve and drawdown series.
    """
    if comp_trades_df.empty:
        return pd.DataFrame(columns=['exit_date', 'trade_id', 'net_pnl_inr', 'cum_net_pnl', 'running_peak', 'drawdown'])
        
    df = comp_trades_df.sort_values(by=['exit_date', 'trade_id']).copy()
    df['cum_net_pnl'] = df['net_pnl_inr'].cumsum()
    df['running_peak'] = df['cum_net_pnl'].cummax()
    df['drawdown'] = df['running_peak'] - df['cum_net_pnl']
    df['drawdown_pct'] = np.where(df['running_peak'] > 0, (df['drawdown'] / df['running_peak']) * 100.0, 0.0)
    return df

def calculate_market_kpis(norm_df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate market coverage and volume summary metrics."""
    if norm_df.empty:
        return {'total_records': 0, 'unique_dates': 0, 'unique_symbols': 0, 'symbols': [], 'min_date': None, 'max_date': None, 'total_volume_lots': 0}
        
    return {
        'total_records': len(norm_df),
        'unique_dates': int(norm_df['date'].nunique()),
        'unique_symbols': int(norm_df['symbol'].nunique()),
        'symbols': sorted(norm_df['symbol'].unique().tolist()),
        'unique_contracts': int(norm_df['contract_key'].nunique()),
        'min_date': norm_df['date'].min(),
        'max_date': norm_df['date'].max(),
        'total_volume_lots': int(norm_df['volume_lots'].sum()),
        'avg_daily_volume_lots': float(norm_df.groupby('date')['volume_lots'].sum().mean())
    }

def verify_reconciliation(trades_df: pd.DataFrame) -> Tuple[bool, float]:
    """Verify that Gross P&L - Costs == Net P&L for all completed trades."""
    comp = trades_df[trades_df['trade_completion_status'] == 'COMPLETED']
    if comp.empty:
        return True, 0.0
    diff = (comp['gross_pnl_inr'] - comp['total_modeled_cost_inr']) - comp['net_pnl_inr']
    max_d = float(diff.abs().max())
    return (max_d < 1e-4), max_d
