import pandas as pd

idx = pd.date_range('2026-01-01', periods=10, freq='5min')
df = pd.DataFrame({'close': range(10)}, index=idx)
df['dt'] = df.index

# Test what pd.to_datetime returns
res = pd.to_datetime(df.get('dt'))
print(type(res))
try:
    print(res.dt.date)
except Exception as e:
    print("Error 1:", str(e))

# Test with just index
res2 = pd.to_datetime(df.index)
print(type(res2))
try:
    print(res2.dt.date)
except Exception as e:
    print("Error 2:", str(e))
