import pandas as pd
import numpy as np
import traceback
from strategy_executor import execute_strategy

code = """
def calculate_signals(df):
    sess = session_mask(df, 'london_ny')
    macro = htf_trend_filter(df, '1h')
    sw_highs, sw_lows = find_swings(df, swing_len = 5)
    bull_fvg_top, bull_fvg_bot, bear_fvg_top, bear_fvg_bot = find_fvgs(df)
    vwap_line = vwap(df)

    ssl_sweep = (df['low'] < sw_lows) & (df['close'] > sw_lows)
    bsl_sweep = (df['high'] > sw_highs) & (df['close'] < sw_highs)

    armed_long = ssl_sweep.rolling(8, min_periods=1).max() == 1
    armed_short = bsl_sweep.rolling(8, min_periods=1).max() == 1

    fvg_touch_long = (df['low'] <= bull_fvg_top) & (df['close'] > bull_fvg_bot)
    fvg_touch_short = (df['high'] >= bear_fvg_bot) & (df['close'] < bear_fvg_top)

    raw_bull = armed_long & fvg_touch_long & (df['close'] > vwap_line) & (macro >= 0) & sess
    raw_bear = armed_short & fvg_touch_short & (df['close'] < vwap_line) & (macro <= 0) & sess

    df['bull_signal'] = raw_bull & (~raw_bull.shift(1).fillna(False))
    df['bear_signal'] = raw_bear & (~raw_bear.shift(1).fillna(False))

    atr_val = atr(df, 20)
    sl_long = np.minimum(df['low'], sw_lows) - (1.2 * atr_val)
    sl_short = np.maximum(df['high'], sw_highs) + (1.2 * atr_val)

    risk_l = np.maximum(df['close'] - sl_long, 3.5)
    risk_s = np.maximum(sl_short - df['close'], 3.5)

    df['sl_long'] = df['close'] - risk_l
    df['sl_short'] = df['close'] + risk_s
    df['use_breakeven'] = True
    df['use_trailing'] = True
    df['tp1_long'] = df['close'] + (risk_l * 2.0)
    df['tp2_long'] = df['close'] + (risk_l * 4.5)
    df['tp1_short'] = df['close'] - (risk_s * 2.0)
    df['tp2_short'] = df['close'] - (risk_s * 4.5)
    return df
"""

try:
    df = pd.read_csv(r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\data copy\XAUUSD_M5.csv', parse_dates=True, index_col='timestamp')
    df = df.iloc[:247817].copy()
    print(f"Testing with {len(df)} rows...")
    res = execute_strategy(code, df)
    print("Success:", res.get("success"))
    if not res.get("success"):
        print("Error:", res.get("message"))
        print("Traceback:")
        print(res.get("traceback"))
except Exception as e:
    traceback.print_exc()
