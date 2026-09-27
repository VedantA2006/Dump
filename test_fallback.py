import sys
sys.path.append(r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137')
import pandas as pd
from strategy_executor import execute_strategy

code = """
def calculate_signals(df):
    sess = session_mask(df, 'london_ny')
    macro = htf_trend_filter(df, '1h')
    sw_highs, sw_lows = find_swings(df, swing_len=8)
    atr_val = atr(df, 20)
    ema_fast = ema(df['close'], 21)
    ema_slow = ema(df['close'], 55)
    vol_filter = rvol(df, 20) > 1.1
    
    ssl_sweep = (df['low'] < sw_lows) & (df['close'] > sw_lows)
    bsl_sweep = (df['high'] > sw_highs) & (df['close'] < sw_highs)
    trend_bull = (ema_fast > ema_slow) & (macro >= 0)
    trend_bear = (ema_fast < ema_slow) & (macro <= 0)
    
    raw_bull = ssl_sweep & trend_bull & vol_filter & sess
    raw_bear = bsl_sweep & trend_bear & vol_filter & sess
    
    df['bull_signal'] = raw_bull & (~raw_bull.shift(1).fillna(False))
    df['bear_signal'] = raw_bear & (~raw_bear.shift(1).fillna(False))
    
    risk_l = np.maximum(df['close'] - (sw_lows - (1.7 * atr_val)), 5.0)
    risk_s = np.maximum((sw_highs + (1.7 * atr_val)) - df['close'], 5.0)
    
    df['sl_long'] = df['close'] - risk_l
    df['sl_short'] = df['close'] + risk_s
    df['use_breakeven'] = True
    df['use_trailing'] = True
    df['tp1_long'] = df['close'] + (risk_l * 2.5)
    df['tp2_long'] = df['close'] + (risk_l * 6.2)
    df['tp1_short'] = df['close'] - (risk_s * 2.5)
    df['tp2_short'] = df['close'] - (risk_s * 6.2)
    return df
"""

idx = pd.date_range('2026-01-01', periods=100, freq='5min')
df = pd.DataFrame({
    'open': range(100),
    'high': range(1, 101),
    'low': range(-1, 99),
    'close': range(100),
    'volume': range(100)
}, index=idx)

res = execute_strategy(code, df)
print("Success:", res.get('success'))
if not res.get('success'):
    print("Traceback:", res.get('traceback'))
