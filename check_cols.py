import pandas as pd

raw_df = pd.read_csv(r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\data copy\XAUUSD_M5.csv', parse_dates=True, index_col='timestamp')
print("Columns:", raw_df.columns)
