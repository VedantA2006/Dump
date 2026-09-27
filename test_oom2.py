import pandas as pd
import numpy as np
import traceback
from strategy_executor import execute_strategy

code = """
def calculate_signals(df):
    sw_highs, sw_lows = find_swings(df, swing_len = 5)
    ssl_sweep = (df['low'] < sw_lows) & (df['close'] > sw_lows)
    armed_long = ssl_sweep.rolling(8, min_periods=1).max() == 1
    
    df['bull_signal'] = armed_long & (~armed_long.shift(1).fillna(False))
    df['bear_signal'] = False
    return df
"""

try:
    df = pd.read_csv(r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\data copy\XAUUSD_M5.csv', parse_dates=True, index_col='timestamp')
    df = df.iloc[:5000].copy()
    print("Testing with 5000 rows...")
    res = execute_strategy(code, df)
    print(res.get("success"), res.get("error"))
except Exception as e:
    traceback.print_exc()
