import time
import pandas as pd
from strategy_executor import execute_strategy

code = """
def calculate_signals(df):
    sess = session_mask(df, 'london_ny')
    macro = htf_trend_filter(df, '1h')
    er = efficiency_ratio(df['close'], 20)
    adx_val, _, _ = adx(df, 14)
    st_line, st_dir = supertrend(df, 10, 3.0)
    atr_val = atr(df, 14)
    
    st_bull_cross = (st_dir == 1) & (st_dir.shift(1) <= 0)
    st_bear_cross = (st_dir == -1) & (st_dir.shift(1) >= 0)
    
    regime_ok = (er > 0.28) & (adx_val > 22) & sess
    
    raw_bull = st_bull_cross & regime_ok & (macro >= 0)
    raw_bear = st_bear_cross & regime_ok & (macro <= 0)
    
    df['bull_signal'] = raw_bull & (~raw_bull.shift(1).fillna(False))
    df['bear_signal'] = raw_bear & (~raw_bear.shift(1).fillna(False))
    
    risk_l = np.maximum(df['close'] - st_line, 4.00)
    risk_s = np.maximum(st_line - df['close'], 4.00)
    risk_l = np.maximum(risk_l, 1.8 * atr_val)
    risk_s = np.maximum(risk_s, 1.8 * atr_val)
    
    df['sl_long'] = df['close'] - risk_l
    df['sl_short'] = df['close'] + risk_s
    df['use_breakeven'] = True
    df['use_trailing'] = True
    df['tp1_long'] = df['close'] + (risk_l * 3.8)
    df['tp1_short'] = df['close'] - (risk_s * 3.8)
    return df
"""

df = pd.read_csv('data copy/XAUUSD_M5.csv', index_col='timestamp', parse_dates=True).iloc[:247817]
t0 = time.time()
res = execute_strategy(code, df)
dt = time.time() - t0
print(f"execute_strategy time: {dt:.3f}s")
print(f"Success: {res.get('success')}, Trades: {len(res.get('trades', []))}, Net PnL: ${res.get('stats', {}).get('total_pnl', 0):,.2f}")
