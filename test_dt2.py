import pandas as pd
idx = pd.date_range('2026-01-01', periods=10)
s = pd.Series(idx)
print(pd.Series(idx).dt.date)
print(pd.Series(s).dt.date)
