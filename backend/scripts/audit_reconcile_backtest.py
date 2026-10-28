import pandas as pd
import numpy as np

trades = pd.read_csv('data/processed/mcx_gold_backtest_trades.csv')
comp = trades[(trades['cost_scenario'] == 'base') & (trades['trade_completion_status'] == 'COMPLETED')].copy()

print('=== PORTFOLIO LEVEL VERIFICATION (BASE SCENARIO) ===')
print('Completed trades count:', len(comp))
wins = (comp['net_pnl_inr'] > 0).sum()
losses = (comp['net_pnl_inr'] <= 0).sum()
print('Wins count:', wins, 'Losses count:', losses)
print('Win rate %:', (wins / len(comp)) * 100)

gross_wins = comp[comp['gross_pnl_inr'] > 0]['gross_pnl_inr'].sum()
gross_losses = abs(comp[comp['gross_pnl_inr'] < 0]['gross_pnl_inr'].sum())
print('Gross Wins:', gross_wins)
print('Gross Losses:', gross_losses)
print('Profit Factor (Gross):', gross_wins / gross_losses)

net_wins = comp[comp['net_pnl_inr'] > 0]['net_pnl_inr'].sum()
net_losses = abs(comp[comp['net_pnl_inr'] < 0]['net_pnl_inr'].sum())
print('Net Wins:', net_wins)
print('Net Losses:', net_losses)
print('Profit Factor (Net):', net_wins / net_losses)

print('Gross PnL sum:', comp['gross_pnl_inr'].sum())
print('Costs sum:', comp['total_modeled_cost_inr'].sum())
print('Net PnL sum:', comp['net_pnl_inr'].sum())
print('Reconciliation diff:', abs(comp['gross_pnl_inr'].sum() - comp['total_modeled_cost_inr'].sum() - comp['net_pnl_inr'].sum()))

# Cost components breakdown
print('\n=== STATUTORY COST COMPONENTS BREAKDOWN (BASE SCENARIO) ===')
for col in ['cost_ctt_inr', 'cost_stamp_duty_inr', 'cost_exchange_turnover_inr', 'cost_sebi_turnover_inr', 'cost_gst_inr', 'cost_brokerage_inr', 'total_modeled_cost_inr']:
    if col in comp.columns:
        val = comp[col].sum()
        print(f'{col:<30}: {val:,.2f}')

# Strategy A vs Strategy B
print('\n=== STRATEGY BREAKDOWN ===')
for strat in sorted(comp['strategy_name'].unique()):
    s = comp[comp['strategy_name'] == strat]
    s_eq = s.sort_values('exit_date').copy()
    s_eq['cum'] = s_eq['net_pnl_inr'].cumsum()
    s_eq['peak'] = s_eq['cum'].cummax()
    s_eq['dd'] = s_eq['peak'] - s_eq['cum']
    s_wins = (s['net_pnl_inr'] > 0).sum()
    s_losses = (s['net_pnl_inr'] <= 0).sum()
    s_gross = s['gross_pnl_inr'].sum()
    s_costs = s['total_modeled_cost_inr'].sum()
    s_net = s['net_pnl_inr'].sum()
    print(f'Strategy: {strat}')
    print(f'  Count: {len(s)}')
    print(f'  Wins/Losses: {s_wins} / {s_losses} ({(s_wins/len(s))*100:.2f}%)')
    print(f'  Gross: {s_gross:,.2f}')
    print(f'  Costs: {s_costs:,.2f}')
    print(f'  Net: {s_net:,.2f}')
    print(f'  Max Drawdown (isolated equity): {s_eq["dd"].max():,.2f}')

# Portfolio Combined Equity Drawdown
eq = comp.sort_values('exit_date').copy()
eq['cum'] = eq['net_pnl_inr'].cumsum()
eq['peak'] = eq['cum'].cummax()
eq['dd'] = eq['peak'] - eq['cum']
print('\n=== COMBINED PORTFOLIO EQUITY DRAWDOWN ===')
print(f'Final Realized Net PnL: {eq["cum"].iloc[-1]:,.2f}')
print(f'Combined Portfolio Max Drawdown: {eq["dd"].max():,.2f}')
