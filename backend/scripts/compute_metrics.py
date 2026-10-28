import os
import glob
import pandas as pd
import numpy as np

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(WORKSPACE_DIR, "data", "raw", "mcx_gold_raw_data")

def compute_all_metrics():
    contract_files = [os.path.join(r, f) for r, d, fs in os.walk(RAW_DIR) for f in fs if f.endswith('.csv') and f != 'download_log.csv']
    
    dfs = []
    for f in contract_files:
        rel = os.path.relpath(f, RAW_DIR).replace('\\', '/')
        df = pd.read_csv(f)
        df['_file'] = rel
        dfs.append(df)
        
    full = pd.concat(dfs, ignore_index=True)
    full['Clean_Symbol'] = full['Symbol'].str.strip()
    full['Clean_Date'] = pd.to_datetime(full['Date'].str.strip(), format='%d %b %Y')
    full['Clean_Expiry'] = full['Expiry Date'].str.strip()
    
    print("=== SUMMARY BY SYMBOL ===")
    sym_stats = []
    for sym, grp in full.groupby('Clean_Symbol'):
        files_count = grp['_file'].nunique()
        rows_count = len(grp)
        exp_count = grp['Clean_Expiry'].nunique()
        dates_count = grp['Clean_Date'].nunique()
        min_date = grp['Clean_Date'].min().strftime('%Y-%m-%d')
        max_date = grp['Clean_Date'].max().strftime('%Y-%m-%d')
        zero_vol = (grp['Volume(Lots)'] == 0).sum()
        zero_oi = (grp['Open Interest(Lots)'] == 0).sum()
        missing_ohl = grp['Open'].isna().sum()
        min_close = grp['Close'].min()
        max_close = grp['Close'].max()
        tot_vol = grp['Volume(Lots)'].sum()
        
        sym_stats.append({
            'Symbol': sym,
            'Files': files_count,
            'Rows': rows_count,
            'Expiries': exp_count,
            'Trading Days': dates_count,
            'Date Range': f"{min_date} to {max_date}",
            'Traded Rows': rows_count - zero_vol,
            'Zero Vol Rows': zero_vol,
            'Zero OI Rows': zero_oi,
            'Missing OHLC': missing_ohl,
            'Min Close': min_close,
            'Max Close': max_close,
            'Total Volume (Lots)': tot_vol
        })
    df_sym = pd.DataFrame(sym_stats)
    print(df_sym.to_string(index=False))
    
    print("\n=== VOLUME & OI QUANTILES FOR TRADED ROWS ===")
    for sym, grp in full[full['Volume(Lots)'] > 0].groupby('Clean_Symbol'):
        print(f"Symbol {sym}:")
        print("  Volume:", grp['Volume(Lots)'].quantile([0.25, 0.5, 0.75, 0.95, 1.0]).to_dict())
        print("  OI:", grp['Open Interest(Lots)'].quantile([0.25, 0.5, 0.75, 0.95, 1.0]).to_dict())

    print("\n=== CONTRACT LIFECYCLE (DAYS TRADED PER CONTRACT) ===")
    exp_summary = full.groupby(['Clean_Symbol', 'Clean_Expiry']).agg(
        obs_count=('Clean_Date', 'count'),
        min_date=('Clean_Date', lambda x: x.min().strftime('%Y-%m-%d')),
        max_date=('Clean_Date', lambda x: x.max().strftime('%Y-%m-%d')),
        total_vol=('Volume(Lots)', 'sum'),
        max_oi=('Open Interest(Lots)', 'max'),
        zero_vol_days=('Volume(Lots)', lambda x: (x == 0).sum())
    ).reset_index()
    print("Contract obs count stats per symbol:")
    for sym, grp in exp_summary.groupby('Clean_Symbol'):
        print(f"Symbol {sym}: min obs={grp['obs_count'].min()}, median={grp['obs_count'].median()}, max={grp['obs_count'].max()}")

if __name__ == '__main__':
    compute_all_metrics()
