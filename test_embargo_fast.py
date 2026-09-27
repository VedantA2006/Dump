import time
import numpy as np
import pandas as pd
from news_calendar import get_news_events

df = pd.read_csv('data copy/XAUUSD_M5.csv', index_col='timestamp', parse_dates=True).iloc[:247817]
times_pd = df.index

t0 = time.time()
# Vectorized weekend embargo
weekday = times_pd.weekday.values
hour = times_pd.hour.values
minute = times_pd.minute.values

fri = (weekday == 4) & ((hour > 21) | ((hour == 21) & (minute >= 45)))
sat = (weekday == 5)
sun = (weekday == 6) & (hour < 22)
is_embargo = fri | sat | sun

events = get_news_events()
if not events.empty:
    events_sec = events.values.astype('datetime64[s]').astype(np.int64)
    times_sec = times_pd.values.astype('datetime64[s]').astype(np.int64)
    events_sec = np.sort(events_sec)

    idx = np.searchsorted(events_sec, times_sec)
    idx_left = np.maximum(0, idx - 1)
    idx_right = np.minimum(len(events_sec) - 1, idx)

    diff_left = np.abs(times_sec - events_sec[idx_left])
    diff_right = np.abs(times_sec - events_sec[idx_right])
    min_diff = np.minimum(diff_left, diff_right)

    is_news = (min_diff <= 15 * 60)
    is_embargo = is_embargo | is_news

dt = time.time() - t0
print(f"Vectorized embargo mask for {len(times_pd):,} bars computed in: {dt*1000:.2f} ms")
print(f"Total embargoed bars: {np.sum(is_embargo):,} / {len(is_embargo):,}")
