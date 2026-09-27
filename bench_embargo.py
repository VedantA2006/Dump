import time
import pandas as pd
import numpy as np
from news_calendar import is_weekend_embargo, is_news_embargo

df = pd.read_csv('data copy/XAUUSD_M5.csv', index_col='timestamp', parse_dates=True).iloc[:247817]
times_pd = df.index

t0 = time.time()
times_str = [t.isoformat() for t in times_pd]
print(f"times_str comprehension: {time.time() - t0:.2f}s")

t0 = time.time()
is_embargo = np.zeros(len(times_pd), dtype=bool)
for i, t in enumerate(times_pd):
    is_embargo[i] = is_weekend_embargo(t) or is_news_embargo(t)
print(f"embargo loop: {time.time() - t0:.2f}s")
