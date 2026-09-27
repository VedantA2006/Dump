import pandas as pd
import numpy as np
from strategy_executor import execute_strategy

df = pd.read_csv('data/XAUUSD_5min.csv')
if 'time' in df.columns:
    df.set_index('time', inplace=True)
elif 'datetime' in df.columns:
    df.set_index('datetime', inplace=True)

df = df.iloc[:1000]

code = """
import numpy as np

def calculate_signals(df):
    slope = linear_regression_slope(df['close'], period=30)
    rvol = rvol(df, period=30)
    atr_value = atr(df, 14)
    sess = session_mask(df, 'london_ny')
    raw_bull = (slope > 0.7) & (rvol > 1.5) & sess
    raw_bear = (slope < -0.7) & (rvol > 1.5) & sess
    df['bull_signal'] = raw_bull & (~raw_bull.shift(1).fillna(False))
    df['bear_signal'] = raw_bear & (~raw_bear.shift(1).fillna(False))
    df['sl_long'] = df['close'] - (1.5 * atr_value)
    df['sl_short'] = df['close'] + (1.5 * atr_value)
    risk_long = np.maximum(df['close'] - df['sl_long'], 4.00)
    risk_short = np.maximum(df['sl_short'] - df['close'], 4.00)
    df['tp1_long'] = df['close'] + (risk_long * 3.8)
    df['tp1_short'] = df['close'] - (risk_short * 3.8)
    return df
"""

try:
    res = execute_strategy(code, df)
    if res.get('success'):
        print("SUCCESS! Trades:", len(res.get('trades', [])))
    else:
        print("FAILED!")
        print("Message:", res.get('message'))
except Exception as e:
    import traceback
    traceback.print_exc()
