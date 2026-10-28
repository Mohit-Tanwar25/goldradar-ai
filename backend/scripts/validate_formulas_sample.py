import pandas as pd
import json

with open('config/contract_specs.json') as f:
    specs = json.load(f)['contracts']

norm = pd.read_csv('data/processed/mcx_gold_normalized.csv')
sample_date = '2025-06-05'

df_date = norm[norm['date'] == sample_date]
print(f"=== RAW VS NORMALIZED CHECK ON {sample_date} ===")
for sym in ['GOLDM', 'GOLDTEN', 'GOLDGUINEA', 'GOLDPETAL']:
    rows = df_date[df_date['symbol'] == sym]
    if len(rows) > 0:
        row = rows.iloc[0]
        q_close = row['close']
        d_s = specs[sym]['quotation_divisor_grams']
        f_s = specs[sym]['fine_gold_factor']
        calc_fine = q_close / (d_s * f_s)
        reported_fine = row['close_fine_per_gram']
        diff = abs(calc_fine - reported_fine)
        print(f"{sym:<12}: Quoted={q_close:>8.1f}, Divisor={d_s:>4.1f}, FineFactor={f_s:>6.4f} | Calc Fine={calc_fine:>9.4f}, Reported={reported_fine:>9.4f}, Diff={diff:.2e}")

radar = pd.read_csv('data/processed/mcx_gold_relative_price_radar.csv')
radar_date = radar[radar['date'] == sample_date]
print(f"\n=== RADAR SPREAD CHECK ON {sample_date} ===")
for _, r in radar_date.head(4).iterrows():
    p_a = r['close_fine_per_gram_a']
    p_b = r['close_fine_per_gram_b']
    calc_diff = p_a - p_b
    calc_pct = (calc_diff / p_b) * 100
    rep_diff = r['fine_price_difference_per_gram']
    rep_pct = r['fine_relative_difference_pct']
    diff_err = abs(calc_diff - rep_diff)
    pct_err = abs(calc_pct - rep_pct)
    print(f"Pair {r['symbol_a']}-{r['symbol_b']}: P_A={p_a:.4f}, P_B={p_b:.4f} | Calc Diff={calc_diff:>8.4f}, Rep Diff={rep_diff:>8.4f} (Err={diff_err:.1e}) | Calc Pct={calc_pct:>7.4f}%, Rep Pct={rep_pct:>7.4f}% (Err={pct_err:.1e})")

term = pd.read_csv('data/processed/mcx_gold_term_structure.csv')
term_date = term[term['date'] == sample_date]
print(f"\n=== TERM STRUCTURE CARRY CHECK ON {sample_date} ===")
for _, t in term_date.head(4).iterrows():
    p_near = t['nearer_close_fine_per_gram']
    p_def = t['deferred_close_fine_per_gram']
    gap = t['calendar_days_between_expiries']
    calc_carry = ((p_def - p_near) / p_near) * (365.0 / gap) * 100.0
    rep_carry = t['fine_annualized_spread_pct']
    carry_err = abs(calc_carry - rep_carry)
    print(f"Symbol {t['symbol']}: Near={p_near:.2f}, Far={p_def:.2f}, Gap={gap} days | Calc Carry={calc_carry:>8.4f}%, Rep Carry={rep_carry:>8.4f}% (Err={carry_err:.1e})")
