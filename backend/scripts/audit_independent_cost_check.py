import pandas as pd
import numpy as np
import json
import math

with open('config/transaction_costs.json') as f:
    cost_cfg = json.load(f)

with open('config/contract_specs.json') as f:
    specs = json.load(f)['contracts']

# Load data
df_a = pd.read_csv('data/processed/mcx_gold_liquidity_filtered_candidates.csv')
df_b = pd.read_csv('data/processed/mcx_gold_transaction_cost_scenarios.csv')

print("=== AUDIT 2: INDEPENDENT TRANSACTION COST RECALCULATION ===")

# Test representative pairs covering all 5 products
sample_indices = []
# 1. GOLD calendar spread (data-eligible)
sample_indices.append(df_a[(df_a['symbol_leg_a'] == 'GOLD') & (df_a['is_both_data_eligible'])].index[0])
# 2. GOLDM calendar spread (data-eligible)
sample_indices.append(df_a[(df_a['symbol_leg_a'] == 'GOLDM') & (df_a['is_both_data_eligible'])].index[0])
# 3. GOLDGUINEA calendar spread (data-eligible)
sample_indices.append(df_a[(df_a['symbol_leg_a'] == 'GOLDGUINEA') & (df_a['is_both_data_eligible'])].index[0])
# 4. GOLDPETAL calendar spread (data-eligible)
sample_indices.append(df_a[(df_a['symbol_leg_a'] == 'GOLDPETAL') & (df_a['is_both_data_eligible'])].index[0])
# 5. GOLDTEN calendar spread (data-eligible)
sample_indices.append(df_a[(df_a['symbol_leg_a'] == 'GOLDTEN') & (df_a['is_both_data_eligible'])].index[0])
# 6. GOLD vs GOLDM cross-product (data-eligible)
sample_indices.append(df_a[(df_a['symbol_leg_a'] == 'GOLD') & (df_a['symbol_leg_b'] == 'GOLDM') & (df_a['is_both_data_eligible'])].index[0])
# 7. GOLDGUINEA vs GOLDPETAL cross-product (data-eligible)
sample_indices.append(df_a[(df_a['symbol_leg_a'] == 'GOLDGUINEA') & (df_a['symbol_leg_b'] == 'GOLDPETAL') & (df_a['is_both_data_eligible'])].index[0])
# 8. GOLDGUINEA vs GOLDTEN cross-product (data-eligible)
sample_indices.append(df_a[(df_a['symbol_leg_a'] == 'GOLDGUINEA') & (df_a['symbol_leg_b'] == 'GOLDTEN') & (df_a['is_both_data_eligible'])].index[0])
# 9. GOLDPETAL vs GOLDTEN cross-product (data-eligible)
sample_indices.append(df_a[(df_a['symbol_leg_a'] == 'GOLDPETAL') & (df_a['symbol_leg_b'] == 'GOLDTEN') & (df_a['is_both_data_eligible'])].index[0])

for idx in sample_indices:
    row = df_a.iloc[idx]
    cid = row['candidate_id']
    sym_a = row['symbol_leg_a']
    sym_b = row['symbol_leg_b']
    u_a = specs[sym_a]['trading_unit_grams']
    u_b = specs[sym_b]['trading_unit_grams']
    c_rows = df_b[df_b['candidate_id'] == cid]
    first_sc = c_rows.iloc[0]
    lots_a = first_sc['matched_lots_leg_a']
    lots_b = first_sc['matched_lots_leg_b']
    grams = first_sc['exposure_grams_leg_a']
    
    p_a = row['close_per_gram_leg_a']
    p_b = row['close_per_gram_leg_b']
    
    # Notional per leg
    notional_a = p_a * u_a * lots_a
    notional_b = p_b * u_b * lots_b
    total_entry_turnover = notional_a + notional_b
    
    print(f"\nCandidate: {cid}")
    print(f"Type: {row['candidate_type']} | Symbols: {sym_a} ({lots_a} lots, {lots_a*u_a}g) vs {sym_b} ({lots_b} lots, {lots_b*u_b}g) | Matched: {grams}g")
    print(f"Prices: Close_A={p_a:.2f}, Close_B={p_b:.2f}")
    print(f"Notionals: Notional_A=Rs.{notional_a:,.2f}, Notional_B=Rs.{notional_b:,.2f} | Total Entry Turnover=Rs.{total_entry_turnover:,.2f}")
    
    for _, sc_row in c_rows.iterrows():
        sc = sc_row['scenario_name']
        cost_inr = sc_row['total_round_trip_cost_inr']
        cost_per_g = sc_row['modeled_round_trip_cost_per_gram']
        entry_cost = sc_row['total_entry_cost_inr']
        exit_cost = sc_row['total_exit_cost_inr']
        
        # Independent manual calculation for base scenario
        if sc == 'base':
            # Entry turnover: Leg A sell turnover = notional_a, Leg B buy turnover = notional_b
            # In base scenario:
            # Leg A entry (sell):
            brok_a_ent = min(20.0, 0.0003 * notional_a)
            exch_a_ent = 0.000021 * notional_a
            sebi_a_ent = 0.000001 * notional_a
            ctt_a_ent = 0.000100 * notional_a
            stamp_a_ent = 0.0
            gst_a_ent = 0.18 * (brok_a_ent + exch_a_ent + sebi_a_ent)
            leg_a_ent = brok_a_ent + exch_a_ent + sebi_a_ent + ctt_a_ent + stamp_a_ent + gst_a_ent
            
            # Leg B entry (buy):
            brok_b_ent = min(20.0, 0.0003 * notional_b)
            exch_b_ent = 0.000021 * notional_b
            sebi_b_ent = 0.000001 * notional_b
            ctt_b_ent = 0.0
            stamp_b_ent = 0.000020 * notional_b
            gst_b_ent = 0.18 * (brok_b_ent + exch_b_ent + sebi_b_ent)
            leg_b_ent = brok_b_ent + exch_b_ent + sebi_b_ent + ctt_b_ent + stamp_b_ent + gst_b_ent
            
            manual_entry_tot = leg_a_ent + leg_b_ent
            
            # Leg A exit (buy):
            brok_a_ext = min(20.0, 0.0003 * notional_a)
            exch_a_ext = 0.000021 * notional_a
            sebi_a_ext = 0.000001 * notional_a
            ctt_a_ext = 0.0
            stamp_a_ext = 0.000020 * notional_a
            gst_a_ext = 0.18 * (brok_a_ext + exch_a_ext + sebi_a_ext)
            leg_a_ext = brok_a_ext + exch_a_ext + sebi_a_ext + ctt_a_ext + stamp_a_ext + gst_a_ext
            
            # Leg B exit (sell):
            brok_b_ext = min(20.0, 0.0003 * notional_b)
            exch_b_ext = 0.000021 * notional_b
            sebi_b_ext = 0.000001 * notional_b
            ctt_b_ext = 0.000100 * notional_b
            stamp_b_ext = 0.0
            gst_b_ext = 0.18 * (brok_b_ext + exch_b_ext + sebi_b_ext)
            leg_b_ext = brok_b_ext + exch_b_ext + sebi_b_ext + ctt_b_ext + stamp_b_ext + gst_b_ext
            
            manual_exit_tot = leg_a_ext + leg_b_ext
            manual_round_trip = manual_entry_tot + manual_exit_tot
            manual_per_g = manual_round_trip / grams
            
            diff_rt = abs(manual_round_trip - cost_inr)
            diff_g = abs(manual_per_g - cost_per_g)
            print(f"  [{sc.upper()}] Modeled: Rs.{cost_inr:,.2f} ({cost_per_g:.4f}/g) | Manual: Rs.{manual_round_trip:,.2f} ({manual_per_g:.4f}/g) | Diff: {diff_rt:.6f}")
            print(f"    Entry Cost: Rs.{entry_cost:,.2f} (Manual: Rs.{manual_entry_tot:,.2f}) | Exit Cost: Rs.{exit_cost:,.2f} (Manual: Rs.{manual_exit_tot:,.2f})")
            assert diff_rt < 1e-4, f"Mismatch in round trip cost for {cid}: {manual_round_trip} vs {cost_inr}"
            assert diff_g < 1e-4, f"Mismatch in per gram cost for {cid}: {manual_per_g} vs {cost_per_g}"
        else:
            print(f"  [{sc.upper()}] Modeled: Rs.{cost_inr:,.2f} ({cost_per_g:.4f}/g)")
