import os
import pandas as pd
import numpy as np

def audit_download_log():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_path = os.path.join(project_root, "data", "raw", "mcx_gold_raw_data", "download_log.csv")
    df = pd.read_csv(log_path)
    print("Download log shape:", df.shape)
    print("Columns:", list(df.columns))
    print("Phases:", df['Phase'].value_counts().to_dict())
    print("Download status:", df['Download status'].value_counts().to_dict())
    print("Symbols in log:", df['Requested symbol'].value_counts().to_dict())
    print("Failed attempts count:", (df['Download status'] == 'failed').sum())
    failed = df[df['Download status'] == 'failed']
    print("Sample failed attempts:")
    print(failed[['Phase', 'Requested symbol', 'Requested expiry', 'Download status', 'Error or limitation']].head(10))
    print("\nNon-null Error or limitation count:", df['Error or limitation'].dropna().count())
    print("Unique errors:", df['Error or limitation'].dropna().unique())

if __name__ == '__main__':
    audit_download_log()
