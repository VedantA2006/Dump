import pandas as pd

try:
    raw_df = pd.read_csv(r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\XAUUSD_News_FOMC_NFP_CPI_PPI_PMI_2Y.csv', encoding='utf-16', sep='\t', parse_dates=['time'], index_col='time')
except:
    raw_df = pd.read_csv(r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\XAUUSD_News_FOMC_NFP_CPI_PPI_PMI_2Y.csv', parse_dates=['time'], index_col='time')
print(f"Total rows: {len(raw_df)}")
print(f"Unique indices: {len(raw_df.index.unique())}")
print(f"Number of duplicates: {raw_df.index.duplicated().sum()}")
