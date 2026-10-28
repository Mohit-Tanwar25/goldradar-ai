import os
import re
import pandas as pd
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "mcx_gold_raw_data")

def check_dates_and_calendar():
    contract_files = [os.path.join(r, f) for r, d, fs in os.walk(RAW_DIR) for f in fs if f.endswith('.csv') and f != 'download_log.csv']
    
    date_strings = set()
    non_standard_dates = []
    weekend_records = []
    
    for f in contract_files:
        rel = os.path.relpath(f, RAW_DIR)
        df = pd.read_csv(f, dtype=str)
        for idx, row in df.iterrows():
            d_str = row['Date']
            date_strings.add(d_str)
            # Check format DD Mon YYYY
            # e.g. "05 Jan 2024"
            m = re.match(r'^\s*(\d{2})\s+([A-Za-z]{3})\s+(\d{4})\s*$', d_str)
            if not m:
                non_standard_dates.append((rel, idx+2, d_str))
            else:
                day, mon, yr = m.groups()
                try:
                    dt = datetime.strptime(f"{day} {mon} {yr}", "%d %b %Y")
                    # Check day of week (Monday is 0, Sunday is 6)
                    if dt.weekday() >= 5: # Saturday or Sunday
                        weekend_records.append((rel, idx+2, d_str, dt.strftime('%A'), row['Symbol'].strip(), row['Expiry Date'].strip()))
                except Exception as e:
                    non_standard_dates.append((rel, idx+2, d_str, str(e)))

    print(f"Total unique date strings found in contract CSVs: {len(date_strings)}")
    print(f"Non-standard date strings: {len(non_standard_dates)}")
    if non_standard_dates:
        print("Sample non-standard:", non_standard_dates[:5])
        
    print(f"Weekend trading records (Sat/Sun): {len(weekend_records)}")
    if weekend_records:
        weekend_df = pd.DataFrame(weekend_records, columns=['file', 'row', 'date_str', 'day_name', 'symbol', 'expiry'])
        print("Weekend trading unique dates and day names:")
        print(weekend_df[['date_str', 'day_name']].drop_duplicates())
        print("Weekend records count by date:\n", weekend_df['date_str'].value_counts())

if __name__ == '__main__':
    check_dates_and_calendar()
