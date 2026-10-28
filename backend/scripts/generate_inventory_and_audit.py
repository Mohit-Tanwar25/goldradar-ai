import os
import glob
import re
import csv
from datetime import datetime
import pandas as pd
import numpy as np

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(WORKSPACE_DIR, "data", "raw")
REPORTS_DIR = os.path.join(WORKSPACE_DIR, "reports")

def generate_inventory_and_data():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    # 1. Discover all files
    all_files = []
    for root, dirs, files in os.walk(RAW_DIR):
        for f in files:
            all_files.append(os.path.join(root, f))
    all_files = sorted(all_files)
    
    print(f"Total discovered files: {len(all_files)}")
    
    inventory_rows = []
    duplicate_rows = []
    
    all_contract_dfs = []
    
    for f in all_files:
        rel_path = os.path.relpath(f, WORKSPACE_DIR).replace('\\', '/')
        file_size = os.path.getsize(f)
        basename = os.path.basename(f)
        
        if basename == "extraction_summary.md":
            with open(f, 'r', encoding='utf-8') as fp:
                lines = fp.readlines()
            inventory_rows.append({
                'filename': rel_path,
                'file_size_bytes': file_size,
                'row_count': len(lines),
                'column_count': 0,
                'column_names': 'N/A (Markdown text document)',
                'detected_date_range': '2024-01-01 to 2026-10-22',
                'symbols_found': 'GOLD; GOLDM; GOLDTEN; GOLDGUINEA; GOLDPETAL',
                'parsing_status': 'SUCCESS (Non-tabular document)',
                'error_details': 'Documentation file describing download procedure and calendar omissions'
            })
            continue
            
        if basename == "download_log.csv":
            try:
                df_log = pd.read_csv(f)
                inventory_rows.append({
                    'filename': rel_path,
                    'file_size_bytes': file_size,
                    'row_count': len(df_log),
                    'column_count': len(df_log.columns),
                    'column_names': ' | '.join(list(df_log.columns)),
                    'detected_date_range': '2024-01-01 to 2026-10-22',
                    'symbols_found': '; '.join(sorted(df_log['Requested symbol'].dropna().unique())),
                    'parsing_status': 'SUCCESS (Metadata audit log)',
                    'error_details': 'Download event log tracking 452 collection attempts and retries'
                })
            except Exception as e:
                inventory_rows.append({
                    'filename': rel_path,
                    'file_size_bytes': file_size,
                    'row_count': 0,
                    'column_count': 0,
                    'column_names': 'N/A',
                    'detected_date_range': 'N/A',
                    'symbols_found': 'N/A',
                    'parsing_status': 'FAILED',
                    'error_details': str(e)
                })
            continue
            
        # Contract CSV
        try:
            df = pd.read_csv(f, dtype=str)
            row_count, col_count = df.shape
            cols = list(df.columns)
            
            # Dates
            parsed_dates = []
            for d in df['Date']:
                try:
                    parsed_dates.append(datetime.strptime(d.strip(), "%d %b %Y"))
                except:
                    pass
            
            if parsed_dates:
                min_d = min(parsed_dates).strftime('%Y-%m-%d')
                max_d = max(parsed_dates).strftime('%Y-%m-%d')
                detected_range = f"{min_d} to {max_d}"
            else:
                detected_range = "None parsed"
                
            symbols = list(df['Symbol'].str.strip().unique())
            symbols_str = '; '.join(symbols)
            
            inventory_rows.append({
                'filename': rel_path,
                'file_size_bytes': file_size,
                'row_count': row_count,
                'column_count': col_count,
                'column_names': ' | '.join(cols),
                'detected_date_range': detected_range,
                'symbols_found': symbols_str,
                'parsing_status': 'SUCCESS',
                'error_details': 'None'
            })
            
            # Check for intra-file duplicates
            dups = df[df.duplicated(subset=['Date', 'Symbol', 'Expiry Date'], keep=False)]
            if len(dups) > 0:
                for idx, r in dups.iterrows():
                    duplicate_rows.append({
                        'duplicate_candidate_id': f"DUP_{len(duplicate_rows)+1}",
                        'source_file': rel_path,
                        'source_row_index': idx + 2,
                        'date': r.get('Date', ''),
                        'symbol': r.get('Symbol', ''),
                        'expiry_date': r.get('Expiry Date', ''),
                        'instrument_type': r.get('Instrument Name', ''),
                        'reason_flagged': 'Intra-file duplicate on (Date, Symbol, Expiry Date)'
                    })
                    
            df['_source_file'] = rel_path
            df['_source_row_index'] = df.index + 2
            all_contract_dfs.append(df)
            
        except Exception as e:
            inventory_rows.append({
                'filename': rel_path,
                'file_size_bytes': file_size,
                'row_count': 0,
                'column_count': 0,
                'column_names': 'N/A',
                'detected_date_range': 'N/A',
                'symbols_found': 'N/A',
                'parsing_status': 'FAILED',
                'error_details': str(e)
            })

    # Save file_inventory.csv
    inv_df = pd.DataFrame(inventory_rows)
    inv_path = os.path.join(REPORTS_DIR, "file_inventory.csv")
    inv_df.to_csv(inv_path, index=False)
    print(f"Saved file inventory to {inv_path} ({len(inv_df)} records)")
    
    # Check cross-file duplicates across combined data
    if all_contract_dfs:
        combined = pd.concat(all_contract_dfs, ignore_index=True)
        # normalize
        combined['clean_sym'] = combined['Symbol'].str.strip()
        combined['clean_exp'] = combined['Expiry Date'].str.strip()
        combined['clean_date'] = combined['Date'].str.strip()
        
        cross_dups = combined[combined.duplicated(subset=['clean_date', 'clean_sym', 'clean_exp'], keep=False)]
        if len(cross_dups) > 0:
            for idx, r in cross_dups.iterrows():
                duplicate_rows.append({
                    'duplicate_candidate_id': f"CROSS_DUP_{len(duplicate_rows)+1}",
                    'source_file': r['_source_file'],
                    'source_row_index': r['_source_row_index'],
                    'date': r['Date'],
                    'symbol': r['Symbol'],
                    'expiry_date': r['Expiry Date'],
                    'instrument_type': r['Instrument Name'],
                    'reason_flagged': 'Cross-file duplicate on (Date, Symbol, Expiry Date)'
                })
                
    # Save duplicate_candidates.csv
    dup_path = os.path.join(REPORTS_DIR, "duplicate_candidates.csv")
    dup_df = pd.DataFrame(duplicate_rows, columns=[
        'duplicate_candidate_id', 'source_file', 'source_row_index', 
        'date', 'symbol', 'expiry_date', 'instrument_type', 'reason_flagged'
    ])
    dup_df.to_csv(dup_path, index=False)
    print(f"Saved duplicate candidates to {dup_path} ({len(dup_df)} candidates found)")

if __name__ == '__main__':
    generate_inventory_and_data()
