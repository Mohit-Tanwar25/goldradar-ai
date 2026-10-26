import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

norm = pd.read_csv('data/processed/mcx_gold_normalized.csv', usecols=['date'])
dates = sorted(norm['date'].unique())
min_date = pd.to_datetime(dates[0])
max_date = pd.to_datetime(dates[-1])

print(f"Start date: {min_date.strftime('%Y-%m-%d')}, End date: {max_date.strftime('%Y-%m-%d')}")

train_m = 6
test_m = 3
step_m = 3

folds = []
cur_start = min_date
fold_idx = 1

while True:
    train_end = cur_start + relativedelta(months=train_m) - relativedelta(days=1)
    test_start = cur_start + relativedelta(months=train_m)
    test_end = test_start + relativedelta(months=test_m) - relativedelta(days=1)
    
    if test_start > max_date:
        break
    if test_end > max_date:
        test_end = max_date
        
    tr_dates = [d for d in dates if cur_start.strftime('%Y-%m-%d') <= d <= train_end.strftime('%Y-%m-%d')]
    te_dates = [d for d in dates if test_start.strftime('%Y-%m-%d') <= d <= test_end.strftime('%Y-%m-%d')]
    
    if len(tr_dates) >= 20 and len(te_dates) >= 10:
        folds.append({
            'fold_id': f'FOLD_{fold_idx:02d}',
            'train_start': tr_dates[0],
            'train_end': tr_dates[-1],
            'train_days': len(tr_dates),
            'test_start': te_dates[0],
            'test_end': te_dates[-1],
            'test_days': len(te_dates)
        })
        fold_idx += 1
        
    cur_start = cur_start + relativedelta(months=step_m)

for f in folds:
    fid = f['fold_id']
    ts, te, td = f['train_start'], f['train_end'], f['train_days']
    vs, ve, vd = f['test_start'], f['test_end'], f['test_days']
    print(f"{fid}: Train [{ts} to {te} ({td} sessions)] -> Test [{vs} to {ve} ({vd} sessions)]")
