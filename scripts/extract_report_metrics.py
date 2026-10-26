import pandas as pd

a = pd.read_csv('data/processed/mcx_gold_liquidity_filtered_candidates.csv')
b = pd.read_csv('data/processed/mcx_gold_transaction_cost_scenarios.csv')
c = pd.read_csv('data/processed/mcx_gold_eligible_candidates.csv')

print('--- FILTER SUMMARY ---')
print(f"Total screened: {len(a):,}")
print(f"Data eligible: {a['is_both_data_eligible'].sum():,} ({a['is_both_data_eligible'].mean():.2%})")
print(f"Passing expiry filter: {a['passes_expiry_filter'].sum():,} ({a['passes_expiry_filter'].mean():.2%})")
print(f"Passing volume filter: {a['passes_volume_filter'].sum():,} ({a['passes_volume_filter'].mean():.2%})")
print(f"Passing OI filter: {a['passes_open_interest_filter'].sum():,} ({a['passes_open_interest_filter'].mean():.2%})")
print(f"Passing all filters: {a['is_all_filters_eligible'].sum():,} ({a['is_all_filters_eligible'].mean():.2%})")

print('\n--- BY CANDIDATE TYPE ---')
for ct, grp in a.groupby('candidate_type'):
    print(f"{ct}: Total={len(grp):,}, DataElig={grp['is_both_data_eligible'].sum():,} ({grp['is_both_data_eligible'].mean():.1%}), ExpiryPass={grp['passes_expiry_filter'].sum():,} ({grp['passes_expiry_filter'].mean():.1%}), VolPass={grp['passes_volume_filter'].sum():,} ({grp['passes_volume_filter'].mean():.1%}), OIPass={grp['passes_open_interest_filter'].sum():,} ({grp['passes_open_interest_filter'].mean():.1%}), AllPass={grp['is_all_filters_eligible'].sum():,} ({grp['is_all_filters_eligible'].mean():.1%})")

print('\n--- CALENDAR SPREADS BY SYMBOL ---')
cal = a[a['candidate_type'] == 'same_symbol_calendar_spread']
for sym, grp in cal.groupby('symbol_leg_a'):
    print(f"{sym:12s}: Total={len(grp):,}, DataElig={grp['is_both_data_eligible'].sum():,}, ExpiryPass={grp['passes_expiry_filter'].sum():,}, LiqPass={grp['passes_liquidity_filter'].sum():,}, AllPass={grp['is_all_filters_eligible'].sum():,} ({grp['is_all_filters_eligible'].mean():.1%})")

print('\n--- CROSS-PRODUCT PAIRS ---')
rad = a[a['candidate_type'] == 'same_expiry_cross_product']
for (s_a, s_b), grp in rad.groupby(['symbol_leg_a', 'symbol_leg_b']):
    print(f"{s_a:10s} vs {s_b:10s}: Total={len(grp):,}, DataElig={grp['is_both_data_eligible'].sum():,}, ExpiryPass={grp['passes_expiry_filter'].sum():,}, LiqPass={grp['passes_liquidity_filter'].sum():,}, AllPass={grp['is_all_filters_eligible'].sum():,} ({grp['is_all_filters_eligible'].mean():.1%})")

print('\n--- EXCLUSION REASONS BREAKDOWN ---')
reasons = a['exclusion_reasons'].str.split(';').explode()
for reason, count in reasons.value_counts().items():
    pct = count / len(a) * 100
    print(f"{reason:38s}: {count:6,} ({pct:5.2f}%)")

print('\n--- SCENARIO SENSITIVITY (All Candidates) ---')
for sc, grp in b.groupby('scenario_name'):
    avail = grp[grp['cost_model_status'] == 'available']
    print(f"{sc:6s}: MeanCostINR={avail['total_round_trip_cost_inr'].mean():.2f}, MeanCostPerGram={avail['modeled_round_trip_cost_per_gram'].mean():.4f}, GrossExceeds={grp['gross_exceeds_modeled_costs'].sum():,} ({grp['gross_exceeds_modeled_costs'].mean():.1%})")

print('\n--- SCENARIO SENSITIVITY (Eligible subset only) ---')
b_elig = b[b['candidate_id'].isin(c['candidate_id'])]
for sc, grp in b_elig.groupby('scenario_name'):
    print(f"{sc:6s}: MeanCostINR={grp['total_round_trip_cost_inr'].mean():.2f}, MeanCostPerGram={grp['modeled_round_trip_cost_per_gram'].mean():.4f}, GrossExceeds={grp['gross_exceeds_modeled_costs'].sum():,} ({grp['gross_exceeds_modeled_costs'].mean():.1%})")
