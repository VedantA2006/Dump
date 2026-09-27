import time
import numpy as np
import pandas as pd
from strategy_executor import supertrend, find_swings, efficiency_ratio, adx

df = pd.read_csv('data copy/XAUUSD_M5.csv', index_col='timestamp', parse_dates=True).iloc[:247817]
print(f"Data length: {len(df):,} bars")

t0 = time.time()
st, d = supertrend(df, 10, 3.0)
print(f"supertrend: {time.time() - t0:.3f}s")

t0 = time.time()
sh, sl = find_swings(df, 7)
print(f"find_swings: {time.time() - t0:.3f}s")

t0 = time.time()
er = efficiency_ratio(df['close'], 20)
print(f"efficiency_ratio: {time.time() - t0:.3f}s")

t0 = time.time()
adx_v, _, _ = adx(df, 14)
print(f"adx: {time.time() - t0:.3f}s")
