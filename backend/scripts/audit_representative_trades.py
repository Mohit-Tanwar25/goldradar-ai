import pandas as pd

df = pd.read_csv('data/processed/mcx_gold_backtest_trades.csv')
comp = df[(df['cost_scenario'] == 'base') & (df['trade_completion_status'] == 'COMPLETED')]

samples = [
    ('strategy_a_cross_product', 'GOLD', 'GOLDM'),
    ('strategy_a_cross_product', 'GOLDGUINEA', 'GOLDPETAL'),
    ('strategy_a_cross_product', 'GOLDPETAL', 'GOLDTEN'),
    ('strategy_a_cross_product', 'GOLDGUINEA', 'GOLDTEN'),
    ('strategy_b_calendar_spread', 'GOLD', 'GOLD'),
    ('strategy_b_calendar_spread', 'GOLDM', 'GOLDM'),
    ('strategy_b_calendar_spread', 'GOLDGUINEA', 'GOLDGUINEA'),
    ('strategy_b_calendar_spread', 'GOLDPETAL', 'GOLDPETAL'),
    ('strategy_b_calendar_spread', 'GOLDTEN', 'GOLDTEN'),
]

for strat, sa, sb in samples:
    match = comp[(comp['strategy_name'] == strat) & (comp['symbol_leg_a'] == sa) & (comp['symbol_leg_b'] == sb)]
    if len(match) > 0:
        t = match.iloc[0]
        tid = t['trade_id']
        ent_d = t['entry_date']
        ext_d = t['exit_date']
        pa_ent, pb_ent = t['entry_price_leg_a'], t['entry_price_leg_b']
        pa_ext, pb_ext = t['exit_price_leg_a'], t['exit_price_leg_b']
        hdays = t['holding_period_days']
        reason = t['exit_trigger_reason']
        la, lb = t['lots_leg_a'], t['lots_leg_b']
        grams = t['matched_exposure_grams']
        dirn = t['signal_direction']
        gross = t['gross_pnl_inr']
        gross_g = t['gross_pnl_per_gram']
        c_ent = t['entry_cost_inr']
        c_ext = t['exit_cost_inr']
        c_tot = t['total_modeled_cost_inr']
        c_g = t['total_modeled_cost_per_gram']
        net = t['net_pnl_inr']
        net_g = t['net_pnl_per_gram']
        diff = abs((gross - c_tot) - net)
        
        print(f"\n--- {strat.upper()}: {sa} vs {sb} ---")
        print(f"Trade ID: {tid}")
        print(f"Entry: {ent_d} Open (A={pa_ent:.2f}, B={pb_ent:.2f})")
        print(f"Exit:  {ext_d} Open (A={pa_ext:.2f}, B={pb_ext:.2f}) | Holding: {hdays} sessions | Reason: {reason}")
        print(f"Lots: A={la}, B={lb} | Matched Grams: {grams}g | Direction: {dirn}")
        print(f"Gross PnL: Rs.{gross:,.2f} (Rs.{gross_g:.4f}/g)")
        print(f"Costs: Entry=Rs.{c_ent:,.2f}, Exit=Rs.{c_ext:,.2f}, Total=Rs.{c_tot:,.2f} (Rs.{c_g:.4f}/g)")
        print(f"Net PnL:   Rs.{net:,.2f} (Rs.{net_g:.4f}/g)")
        assert diff < 1e-4, f"Reconciliation failure for {tid}: {diff}"
        print("RECONCILED: Gross - Costs == Net (PASS)")
    else:
        print(f"\n--- {strat.upper()}: {sa} vs {sb} --- NO COMPLETED TRADES")
