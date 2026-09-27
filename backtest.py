import math
import numpy as np
import pandas as pd
from numba import njit
from stats_utils import compute_sharpe_sortino

# Global cache for embargo masks (Task 4 speedup)
_EMBARGO_CACHE = {}

def _get_embargo_mask(times_pd: pd.Series) -> np.ndarray:
    """Returns a boolean array where True means trading is blocked (weekends, roll, illiquid hours)."""
    try:
        key = (len(times_pd), str(times_pd.iloc[0]), str(times_pd.iloc[-1]))
    except Exception:
        key = id(times_pd)
    if key in _EMBARGO_CACHE:
        return _EMBARGO_CACHE[key]
    dt = times_pd if isinstance(times_pd, pd.DatetimeIndex) else times_pd.dt
    is_weekend = dt.weekday >= 5
    is_roll = (dt.hour == 21)
    is_asian_illiquid = (dt.hour == 22) | ((dt.hour == 23) & (dt.minute < 30))
    is_friday_close = (dt.weekday == 4) & (dt.hour >= 20)
    
    is_embargo = is_weekend | is_roll | is_asian_illiquid | is_friday_close
    is_embargo = getattr(is_embargo, 'values', is_embargo)
    
    if len(_EMBARGO_CACHE) >= 10:
        _EMBARGO_CACHE.clear()
    _EMBARGO_CACHE[key] = is_embargo
    return is_embargo

@njit
def _run_backtest_njit(
    opens, highs, lows, closes, 
    bull_signals, bear_signals,
    sl_longs, sl_shorts, 
    tp1_longs, tp1_shorts,
    tp2_longs, tp2_shorts,
    be_triggers,
    risk_pcts, use_bes, use_trails,
    is_embargo, eval_start_idx,
    initial_capital, lot_size,
    cost_per_oz, fallback_sl_dist, min_stop_dist, min_tp_dist, be_threshold
):
    N = len(opens)
    max_trades = N * 2 # Account for partial scale-outs
    
    t_id = np.zeros(max_trades, dtype=np.int64)
    t_dir = np.zeros(max_trades, dtype=np.int64) # 1 long, -1 short
    t_entry_idx = np.zeros(max_trades, dtype=np.int64)
    t_exit_idx = np.zeros(max_trades, dtype=np.int64)
    t_entry_price = np.zeros(max_trades, dtype=np.float64)
    t_exit_price = np.zeros(max_trades, dtype=np.float64)
    t_pnl = np.zeros(max_trades, dtype=np.float64)
    t_reason = np.zeros(max_trades, dtype=np.int64) 
    # 1: Embargo, 2: TP, 3: SL, 4: BE, 5: Signal, 6: End, 7: Partial TP1
    t_sl = np.zeros(max_trades, dtype=np.float64)
    t_tp = np.zeros(max_trades, dtype=np.float64)
    t_init_size = np.zeros(max_trades, dtype=np.float64)
    t_risk_usd = np.zeros(max_trades, dtype=np.float64)
    
    pos_dir = 0
    pos_entry = 0.0
    pos_sl = 0.0
    pos_init_sl = 0.0
    pos_tp = 0.0
    pos_tp2 = 0.0
    pos_size = 0.0
    pos_pnl = 0.0
    pos_entry_idx = 0
    pos_peak = 0.0
    pos_trough = 0.0
    pos_be_active = False
    pos_tp1_hit = False
    pos_use_be = False
    pos_use_trail = False
    pos_risk_usd = 0.0
    
    trade_count = 0
    cumulative_pnl = 0.0
    
    eq_curve = np.zeros(N, dtype=np.float64)
    eq_pnl = np.zeros(N, dtype=np.float64)
    
    peak_equity = initial_capital
    max_drawdown = 0.0
    
    for i in range(1, N):
        closed = False
        
        # EXITS
        if pos_dir != 0:
            risk_dist = abs(pos_entry - pos_sl) if pos_sl > 0 else fallback_sl_dist
            
            if is_embargo[i]:
                exit_price = opens[i] - cost_per_oz if pos_dir == 1 else opens[i] + cost_per_oz
                pnl = (exit_price - pos_entry) * pos_size if pos_dir == 1 else (pos_entry - exit_price) * pos_size
                cumulative_pnl += pnl
                pos_pnl += pnl
                t_id[trade_count] = trade_count + 1
                t_dir[trade_count] = pos_dir
                t_entry_idx[trade_count] = pos_entry_idx
                t_exit_idx[trade_count] = i
                t_entry_price[trade_count] = pos_entry
                t_exit_price[trade_count] = exit_price
                t_pnl[trade_count] = pos_pnl
                t_reason[trade_count] = 1
                t_sl[trade_count] = pos_init_sl
                t_tp[trade_count] = pos_tp
                t_init_size[trade_count] = pos_size
                t_risk_usd[trade_count] = pos_risk_usd
                trade_count += 1
                pos_dir = 0
                closed = True
                
            elif pos_dir == 1:
                # Dynamic Breakeven Logic (no longer hardcoded to 1.8)
                if pos_use_be and not pos_be_active and (highs[i] >= pos_entry + (be_triggers[i] * risk_dist)):
                    be_level = pos_entry + cost_per_oz
                    if pos_sl == 0.0 or pos_sl < be_level:
                        pos_sl = be_level
                        pos_be_active = True
                
                # Slippage/Spread aware triggers
                sl_hit = (pos_sl > 0.0 and (lows[i] - cost_per_oz) <= pos_sl)
                tp_hit = (pos_tp > 0.0 and (highs[i] - cost_per_oz) >= pos_tp)
                tp2_hit = (pos_tp2 > 0.0 and (highs[i] - cost_per_oz) >= pos_tp2)
                
                take_tp = False
                take_tp2 = False
                take_sl = False
                
                if tp_hit and not sl_hit: 
                    take_tp = True
                    if tp2_hit: take_tp2 = True
                elif sl_hit and not tp_hit: 
                    take_sl = True
                elif tp_hit and sl_hit:
                    # Intra-candle heuristic: bearish candle (close < open) implies high came before low -> TP hit first
                    if closes[i] <= opens[i]: 
                        take_tp = True
                        if tp2_hit: take_tp2 = True
                    else: 
                        take_sl = True
                        
                if take_sl:
                    exit_price = pos_sl - cost_per_oz
                    pnl = (exit_price - pos_entry) * pos_size
                    cumulative_pnl += pnl
                    pos_pnl += pnl
                    t_id[trade_count] = trade_count + 1
                    t_dir[trade_count] = pos_dir
                    t_entry_idx[trade_count] = pos_entry_idx
                    t_exit_idx[trade_count] = i
                    t_entry_price[trade_count] = pos_entry
                    t_exit_price[trade_count] = exit_price
                    t_pnl[trade_count] = pos_pnl
                    t_reason[trade_count] = 4 if (pos_be_active and abs(pnl) < be_threshold) else 3
                    t_sl[trade_count] = pos_init_sl
                    t_tp[trade_count] = pos_tp
                    t_init_size[trade_count] = pos_size
                    t_risk_usd[trade_count] = pos_risk_usd
                    trade_count += 1
                    pos_dir = 0
                    closed = True
                elif take_tp:
                    if take_tp2 or pos_tp2 == 0.0:
                        # Full close
                        fill_price = pos_tp2 - cost_per_oz if take_tp2 else pos_tp - cost_per_oz
                        pnl = (fill_price - pos_entry) * pos_size
                        cumulative_pnl += pnl
                        pos_pnl += pnl
                        t_id[trade_count] = trade_count + 1
                        t_dir[trade_count] = pos_dir
                        t_entry_idx[trade_count] = pos_entry_idx
                        t_exit_idx[trade_count] = i
                        t_entry_price[trade_count] = pos_entry
                        t_exit_price[trade_count] = fill_price
                        t_pnl[trade_count] = pos_pnl
                        t_reason[trade_count] = 2
                        t_sl[trade_count] = pos_init_sl
                        t_tp[trade_count] = pos_tp
                        t_init_size[trade_count] = pos_size
                        t_risk_usd[trade_count] = pos_risk_usd
                        trade_count += 1
                        pos_dir = 0
                        closed = True
                    else:
                        # Partial close (TP1 hit, TP2 remaining)
                        fill_price = pos_tp - cost_per_oz
                        partial_size = pos_size / 2.0
                        pnl = (fill_price - pos_entry) * partial_size
                        cumulative_pnl += pnl
                        pos_pnl += pnl
                        # Record partial scale-out trade
                        t_id[trade_count] = trade_count + 1
                        t_dir[trade_count] = pos_dir
                        t_entry_idx[trade_count] = pos_entry_idx
                        t_exit_idx[trade_count] = i
                        t_entry_price[trade_count] = pos_entry
                        t_exit_price[trade_count] = fill_price
                        t_pnl[trade_count] = pnl
                        t_reason[trade_count] = 7 # Partial TP
                        t_sl[trade_count] = pos_init_sl
                        t_tp[trade_count] = pos_tp
                        t_init_size[trade_count] = partial_size
                        t_risk_usd[trade_count] = pos_risk_usd / 2.0
                        trade_count += 1
                        
                        # Update remaining position
                        pos_size -= partial_size
                        pos_tp = pos_tp2
                        pos_tp2 = 0.0
                        pos_tp1_hit = True
                        
            elif pos_dir == -1:
                # Dynamic Breakeven Logic (no longer hardcoded to 1.8)
                if pos_use_be and not pos_be_active and (lows[i] <= pos_entry - (be_triggers[i] * risk_dist)):
                    be_level = pos_entry - cost_per_oz
                    if pos_sl == 0.0 or pos_sl > be_level:
                        pos_sl = be_level
                        pos_be_active = True
                        
                # Short SL hit is when ASK crosses SL (high + spread)
                sl_hit = (pos_sl > 0.0 and (highs[i] + cost_per_oz) >= pos_sl)
                tp_hit = (pos_tp > 0.0 and (lows[i] + cost_per_oz) <= pos_tp)
                tp2_hit = (pos_tp2 > 0.0 and (lows[i] + cost_per_oz) <= pos_tp2)
                
                take_tp = False
                take_tp2 = False
                take_sl = False
                
                if tp_hit and not sl_hit: 
                    take_tp = True
                    if tp2_hit: take_tp2 = True
                elif sl_hit and not tp_hit: 
                    take_sl = True
                elif tp_hit and sl_hit:
                    # Intra-candle heuristic: bullish candle (close > open) implies low came before high -> TP hit first
                    if closes[i] >= opens[i]: 
                        take_tp = True
                        if tp2_hit: take_tp2 = True
                    else: 
                        take_sl = True
                        
                if take_sl:
                    exit_price = pos_sl + cost_per_oz
                    pnl = (pos_entry - exit_price) * pos_size
                    cumulative_pnl += pnl
                    pos_pnl += pnl
                    t_id[trade_count] = trade_count + 1
                    t_dir[trade_count] = pos_dir
                    t_entry_idx[trade_count] = pos_entry_idx
                    t_exit_idx[trade_count] = i
                    t_entry_price[trade_count] = pos_entry
                    t_exit_price[trade_count] = exit_price
                    t_pnl[trade_count] = pos_pnl
                    t_reason[trade_count] = 4 if (pos_be_active and abs(pnl) < be_threshold) else 3
                    t_sl[trade_count] = pos_init_sl
                    t_tp[trade_count] = pos_tp
                    t_init_size[trade_count] = pos_size
                    t_risk_usd[trade_count] = pos_risk_usd
                    trade_count += 1
                    pos_dir = 0
                    closed = True
                elif take_tp:
                    if take_tp2 or pos_tp2 == 0.0:
                        # Full close
                        fill_price = pos_tp2 + cost_per_oz if take_tp2 else pos_tp + cost_per_oz
                        pnl = (pos_entry - fill_price) * pos_size
                        cumulative_pnl += pnl
                        pos_pnl += pnl
                        t_id[trade_count] = trade_count + 1
                        t_dir[trade_count] = pos_dir
                        t_entry_idx[trade_count] = pos_entry_idx
                        t_exit_idx[trade_count] = i
                        t_entry_price[trade_count] = pos_entry
                        t_exit_price[trade_count] = fill_price
                        t_pnl[trade_count] = pos_pnl
                        t_reason[trade_count] = 2
                        t_sl[trade_count] = pos_init_sl
                        t_tp[trade_count] = pos_tp
                        t_init_size[trade_count] = pos_size
                        t_risk_usd[trade_count] = pos_risk_usd
                        trade_count += 1
                        pos_dir = 0
                        closed = True
                    else:
                        # Partial close (TP1 hit, TP2 remaining)
                        fill_price = pos_tp + cost_per_oz
                        partial_size = pos_size / 2.0
                        pnl = (pos_entry - fill_price) * partial_size
                        cumulative_pnl += pnl
                        pos_pnl += pnl
                        # Record partial scale-out trade
                        t_id[trade_count] = trade_count + 1
                        t_dir[trade_count] = pos_dir
                        t_entry_idx[trade_count] = pos_entry_idx
                        t_exit_idx[trade_count] = i
                        t_entry_price[trade_count] = pos_entry
                        t_exit_price[trade_count] = fill_price
                        t_pnl[trade_count] = pnl
                        t_reason[trade_count] = 7 # Partial TP
                        t_sl[trade_count] = pos_init_sl
                        t_tp[trade_count] = pos_tp
                        t_init_size[trade_count] = partial_size
                        t_risk_usd[trade_count] = pos_risk_usd / 2.0
                        trade_count += 1
                        
                        # Update remaining position
                        pos_size -= partial_size
                        pos_tp = pos_tp2
                        pos_tp2 = 0.0
                        pos_tp1_hit = True

            # Close on opposite signal
            if not closed and pos_dir != 0:
                opp_signal = (pos_dir == 1 and bear_signals[i]) or (pos_dir == -1 and bull_signals[i])
                if opp_signal:
                    unrealized_r = 0.0
                    if pos_dir == 1:
                        unrealized_r = (closes[i] - pos_entry) / risk_dist if risk_dist > 0 else 0.0
                    else:
                        unrealized_r = (pos_entry - closes[i]) / risk_dist if risk_dist > 0 else 0.0
                        
                    is_protected = (unrealized_r >= 1.2 and pos_be_active)
                    if not is_protected:
                        if pos_dir == 1:
                            exit_price = closes[i] - cost_per_oz
                            pnl = (exit_price - pos_entry) * pos_size
                        else:
                            exit_price = closes[i] + cost_per_oz
                            pnl = (pos_entry - exit_price) * pos_size
                        cumulative_pnl += pnl
                        pos_pnl += pnl
                        t_id[trade_count] = trade_count + 1
                        t_dir[trade_count] = pos_dir
                        t_entry_idx[trade_count] = pos_entry_idx
                        t_exit_idx[trade_count] = i
                        t_entry_price[trade_count] = pos_entry
                        t_exit_price[trade_count] = exit_price
                        t_pnl[trade_count] = pos_pnl
                        t_reason[trade_count] = 5
                        t_sl[trade_count] = pos_init_sl
                        t_tp[trade_count] = pos_tp
                        t_init_size[trade_count] = pos_size
                        t_risk_usd[trade_count] = pos_risk_usd
                        trade_count += 1
                        pos_dir = 0
                        closed = True
                        
            # Trailing stop
            if not closed and pos_dir != 0:
                if pos_dir == 1:
                    pos_peak = max(pos_peak, highs[i])
                    if pos_use_trail:
                        # More aggressive trailing once TP1 is hit
                        trail_mult = 1.0 if pos_tp1_hit else 1.6
                        trail_stop = pos_peak - (trail_mult * risk_dist)
                        if pos_sl == 0.0 or trail_stop > pos_sl:
                            pos_sl = trail_stop
                else:
                    pos_trough = min(pos_trough, lows[i])
                    if pos_use_trail:
                        trail_mult = 1.0 if pos_tp1_hit else 1.6
                        trail_stop = pos_trough + (trail_mult * risk_dist)
                        if pos_sl == 0.0 or trail_stop < pos_sl:
                            pos_sl = trail_stop
                            
        # ENTRIES
        in_warmup = (i < eval_start_idx)
        if pos_dir == 0 and not in_warmup:
            bull = bull_signals[i]
            bear = bear_signals[i]
            if is_embargo[i]:
                bull = False
                bear = False
                
            if bull and not bear:
                entry_price = closes[i] + cost_per_oz
                sl = sl_longs[i] if not math.isnan(sl_longs[i]) else 0.0
                if sl == 0.0 or sl >= entry_price:
                    sl = entry_price - fallback_sl_dist
                elif (entry_price - sl) < min_stop_dist:
                    sl = entry_price - min_stop_dist
                    
                risk_dist = abs(entry_price - sl)
                tp = tp1_longs[i] if not math.isnan(tp1_longs[i]) else 0.0
                if tp <= entry_price:
                    tp = entry_price + max(min_tp_dist, 1.5 * risk_dist)
                else:
                    min_tp = entry_price + (1.5 * risk_dist)
                    if tp < min_tp: tp = min_tp
                    
                tp2 = tp2_longs[i] if not math.isnan(tp2_longs[i]) else 0.0
                if tp2 > 0.0 and tp2 <= tp:
                    tp2 = 0.0
                    
                risk_pct = risk_pcts[i] if not math.isnan(risk_pcts[i]) else 0.01
                risk_per_trade_usd = initial_capital * risk_pct
                calc_size = round(risk_per_trade_usd / risk_dist, 2) if risk_dist > 0 else lot_size
                
                pos_dir = 1
                pos_entry = entry_price
                pos_peak = entry_price
                pos_entry_idx = i
                pos_sl = sl
                pos_init_sl = sl
                pos_tp = tp
                pos_tp2 = tp2
                pos_size = calc_size
                pos_risk_usd = risk_per_trade_usd
                pos_use_be = use_bes[i]
                pos_use_trail = use_trails[i]
                pos_be_active = False
                pos_tp1_hit = False
                pos_pnl = 0.0
                
            elif bear and not bull:
                entry_price = closes[i] - cost_per_oz
                sl = sl_shorts[i] if not math.isnan(sl_shorts[i]) else 0.0
                if sl == 0.0 or sl <= entry_price:
                    sl = entry_price + fallback_sl_dist
                elif (sl - entry_price) < min_stop_dist:
                    sl = entry_price + min_stop_dist
                    
                risk_dist = abs(sl - entry_price)
                tp = tp1_shorts[i] if not math.isnan(tp1_shorts[i]) else 0.0
                if tp >= entry_price or tp == 0.0:
                    tp = entry_price - max(min_tp_dist, 1.5 * risk_dist)
                else:
                    min_tp = entry_price - (1.5 * risk_dist)
                    if tp > min_tp: tp = min_tp
                    
                tp2 = tp2_shorts[i] if not math.isnan(tp2_shorts[i]) else 0.0
                if tp2 > 0.0 and tp2 >= tp:
                    tp2 = 0.0
                    
                risk_pct = risk_pcts[i] if not math.isnan(risk_pcts[i]) else 0.01
                risk_per_trade_usd = initial_capital * risk_pct
                calc_size = round(risk_per_trade_usd / risk_dist, 2) if risk_dist > 0 else lot_size
                
                pos_dir = -1
                pos_entry = entry_price
                pos_trough = entry_price
                pos_entry_idx = i
                pos_sl = sl
                pos_init_sl = sl
                pos_tp = tp
                pos_tp2 = tp2
                pos_size = calc_size
                pos_risk_usd = risk_per_trade_usd
                pos_use_be = use_bes[i]
                pos_use_trail = use_trails[i]
                pos_be_active = False
                pos_tp1_hit = False
                pos_pnl = 0.0

        # EQUITY & DD
        unrealized = 0.0
        worst_unrealized = 0.0
        if pos_dir == 1:
            unrealized = (closes[i] - pos_entry) * pos_size
            worst_unrealized = (lows[i] - pos_entry) * pos_size
        elif pos_dir == -1:
            unrealized = (pos_entry - closes[i]) * pos_size
            worst_unrealized = (pos_entry - highs[i]) * pos_size
            
        current_eq = initial_capital + cumulative_pnl + unrealized
        peak_equity = max(peak_equity, current_eq)
        worst_eq = initial_capital + cumulative_pnl + worst_unrealized
        intra_dd = peak_equity - worst_eq
        if intra_dd > max_drawdown:
            max_drawdown = intra_dd
            
        eq_curve[i] = current_eq
        eq_pnl[i] = cumulative_pnl + unrealized
        
    # CLOSE AT END
    if pos_dir != 0:
        if pos_dir == 1:
            exit_price = closes[N-1] - cost_per_oz
            pnl = (exit_price - pos_entry) * pos_size
        else:
            exit_price = closes[N-1] + cost_per_oz
            pnl = (pos_entry - exit_price) * pos_size
        cumulative_pnl += pnl
        pos_pnl += pnl
        t_id[trade_count] = trade_count + 1
        t_dir[trade_count] = pos_dir
        t_entry_idx[trade_count] = pos_entry_idx
        t_exit_idx[trade_count] = N-1
        t_entry_price[trade_count] = pos_entry
        t_exit_price[trade_count] = exit_price
        t_pnl[trade_count] = pos_pnl
        t_reason[trade_count] = 6 # End
        t_sl[trade_count] = pos_init_sl
        t_tp[trade_count] = pos_tp
        t_init_size[trade_count] = pos_size
        t_risk_usd[trade_count] = pos_risk_usd
        trade_count += 1

    max_dd_pct = (max_drawdown / peak_equity) * 100 if peak_equity > 0 else 0.0
    return (
        trade_count, t_id, t_dir, t_entry_idx, t_exit_idx, t_entry_price, t_exit_price, t_pnl, t_reason, t_sl, t_tp, t_init_size, t_risk_usd,
        eq_curve, eq_pnl, max_drawdown, max_dd_pct, cumulative_pnl
    )


def run_backtest(df, initial_capital=100000.0, lot_size=100.0, partial_tp=False, spread=0.20, slippage=0.05):
    """Numba-accelerated Backtester Engine."""
    cost_per_oz = (spread / 2.0) + slippage
    
    median_price = float(df['close'].median()) if len(df) > 0 else 1.0
    fallback_sl_dist = median_price * 0.0025
    min_stop_dist = median_price * 0.001
    min_tp_dist = median_price * 0.001
    be_threshold = median_price * 0.025
    eval_start_time = df.attrs.get('eval_start_time') if hasattr(df, 'attrs') else None

    # Pre-extract numpy arrays
    N = len(df)
    opens = df['open'].values
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    
    bull_signals = df['bull_signal'].values if 'bull_signal' in df.columns else np.zeros(N, dtype=bool)
    bear_signals = df['bear_signal'].values if 'bear_signal' in df.columns else np.zeros(N, dtype=bool)
    
    sl_longs = df['sl_long'].values if 'sl_long' in df.columns else np.full(N, np.nan)
    sl_shorts = df['sl_short'].values if 'sl_short' in df.columns else np.full(N, np.nan)
    
    tp1_longs = df['tp1_long'].values if 'tp1_long' in df.columns else (df['tp_long'].values if 'tp_long' in df.columns else np.full(N, np.nan))
    tp1_shorts = df['tp1_short'].values if 'tp1_short' in df.columns else (df['tp_short'].values if 'tp_short' in df.columns else np.full(N, np.nan))
    
    tp2_longs = df['tp2_long'].values if 'tp2_long' in df.columns else np.full(N, np.nan)
    tp2_shorts = df['tp2_short'].values if 'tp2_short' in df.columns else np.full(N, np.nan)
    be_triggers = df['be_trigger'].values if 'be_trigger' in df.columns else np.full(N, 1.8)
    
    risk_pcts = df['risk_pct'].values if 'risk_pct' in df.columns else np.full(N, np.nan)
    use_bes = df['use_breakeven'].values if 'use_breakeven' in df.columns else np.zeros(N, dtype=bool)
    use_trails = df['use_trailing'].values if 'use_trailing' in df.columns else np.zeros(N, dtype=bool)

    # High-speed vectorized embargo check (cached across evaluations for 100x speedup)
    times_pd = pd.to_datetime(df.index) if isinstance(df.index, pd.DatetimeIndex) else pd.to_datetime(df['datetime'] if 'datetime' in df.columns else (df['time'] if 'time' in df.columns else df['dt']))
    is_embargo = _get_embargo_mask(times_pd)

    eval_start_idx = 0
    if eval_start_time is not None:
        eval_start_idx = np.searchsorted(times_pd, pd.to_datetime(eval_start_time))

    # RUN NUMBA ENGINE
    (tc, t_id, t_dir, t_entry_idx, t_exit_idx, t_entry_price, t_exit_price, t_pnl, t_reason, t_sl, t_tp, t_init_size, t_risk_usd,
     eq_curve, eq_pnl, max_drawdown, max_drawdown_pct, cum_pnl) = _run_backtest_njit(
        opens, highs, lows, closes, 
        bull_signals, bear_signals,
        sl_longs, sl_shorts, 
        tp1_longs, tp1_shorts,
        tp2_longs, tp2_shorts,
        be_triggers,
        risk_pcts, use_bes, use_trails,
        is_embargo, eval_start_idx,
        initial_capital, lot_size,
        cost_per_oz, fallback_sl_dist, min_stop_dist, min_tp_dist, be_threshold
    )

    # Map back to dictionaries with on-demand timestamp formatting (no full-array string conversions)
    reason_map = {1: 'Embargo', 2: 'TP', 3: 'SL', 4: 'BE', 5: 'Signal', 6: 'End', 7: 'Partial TP'}
    trades = []

    for i in range(tc):
        dir_str = 'long' if t_dir[i] == 1 else 'short'
        r_usd = t_risk_usd[i] if t_risk_usd[i] > 0 else 1000.0
        r_ret = round(t_pnl[i] / r_usd, 2)
        en_idx = int(t_entry_idx[i])
        ex_idx = int(t_exit_idx[i])
        en_t = times_pd[en_idx]
        ex_t = times_pd[ex_idx]
        trades.append({
            'id': int(t_id[i]),
            'direction': dir_str,
            'entry_price': round(t_entry_price[i], 2),
            'entry_time': str(en_t),
            'entry_time_ts': int(en_t.timestamp()),
            'exit_price': round(t_exit_price[i], 2),
            'exit_time': str(ex_t),
            'exit_time_ts': int(ex_t.timestamp()),
            'exit_reason': reason_map.get(t_reason[i], 'Unknown'),
            'sl': round(t_sl[i], 2) if t_sl[i] > 0 else None,
            'tps': [round(t_tp[i], 2)] if t_tp[i] > 0 else [],
            'initial_size': t_init_size[i],
            'pnl': round(t_pnl[i], 2),
            'pnl_percent': round((t_pnl[i] / (t_entry_price[i] * t_init_size[i])) * 100, 2) if t_entry_price[i] > 0 else 0.0,
            'cumulative_pnl': 0.0,
            'tp_hits': [1] if t_reason[i] in (2, 7) else [],
            'r_return': r_ret,
        })

    equity_curve = []
    step = 20
    for i in range(0, N, step):
        t_pt = times_pd[i]
        equity_curve.append({
            'time': str(t_pt),
            'equity': round(eq_curve[i], 2),
            'pnl': round(eq_pnl[i], 2),
        })
    if (N - 1) % step != 0:
        t_end = times_pd[N - 1]
        equity_curve.append({
            'time': str(t_end),
            'equity': round(eq_curve[N - 1], 2),
            'pnl': round(eq_pnl[N - 1], 2),
        })

    stats = _compute_stats(trades, equity_curve, initial_capital, max_drawdown, max_drawdown_pct)
    return trades, equity_curve, stats

def _compute_stats(trades, equity_curve, initial_capital, max_drawdown, max_drawdown_pct):
    if not trades:
        return {
            'total_trades': 0, 'winning_trades': 0, 'losing_trades': 0,
            'win_rate': 0.0, 'total_pnl': 0.0, 'net_profit_pct': 0.0,
            'gross_profit': 0.0, 'gross_loss': 0.0, 'profit_factor': 0.0,
            'max_drawdown': 0.0, 'max_drawdown_pct': 0.0,
            'avg_pnl': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0,
            'ratio_win_loss': 0.0, 'best_trade': 0.0, 'worst_trade': 0.0,
            'sharpe_ratio': 0.0, 'sortino_ratio': 0.0,
            'max_consecutive_wins': 0, 'max_consecutive_losses': 0,
            'long_trades': 0, 'short_trades': 0,
        }

    pnls = [t['pnl'] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    longs = [t for t in trades if t['direction'] == 'long']
    shorts = [t for t in trades if t['direction'] == 'short']

    gross_profit = sum(wins) if wins else 0.0
    gross_loss = abs(sum(losses)) if losses else 0.0
    total_pnl = sum(pnls)

    cur_w = max_w = cur_l = max_l = 0
    for p in pnls:
        if p > 0:
            cur_w += 1
            cur_l = 0
            max_w = max(max_w, cur_w)
        else:
            cur_l += 1
            cur_w = 0
            max_l = max(max_l, cur_l)

    # Compute real Sharpe/Sortino
    sharpe, sortino = compute_sharpe_sortino(trades, equity_curve, initial_capital)

    avg_win = float(np.mean(wins)) if wins else 0.0
    avg_loss = float(abs(np.mean(losses))) if losses else 0.0
    win_loss_ratio = round(avg_win / avg_loss, 2) if avg_loss > 0 else 0.0

    return {
        'total_trades': len(trades),
        'winning_trades': len(wins),
        'losing_trades': len(losses),
        'win_rate': round(len(wins) / len(trades) * 100, 1),
        'total_pnl': round(total_pnl, 2),
        'net_profit_pct': round((total_pnl / initial_capital) * 100, 2),
        'gross_profit': round(gross_profit, 2),
        'gross_loss': round(gross_loss, 2),
        'profit_factor': round(gross_profit / gross_loss, 2) if gross_loss > 0 else 999.0,
        'max_drawdown': round(max_drawdown, 2),
        'max_drawdown_pct': round(max_drawdown_pct, 2),
        'avg_pnl': round(float(np.mean(pnls)), 2),
        'avg_win': round(avg_win, 2),
        'avg_loss': round(avg_loss, 2),
        'ratio_win_loss': win_loss_ratio,
        'best_trade': round(max(pnls), 2),
        'worst_trade': round(min(pnls), 2),
        'sharpe_ratio': sharpe,
        'sortino_ratio': sortino,
        'max_consecutive_wins': max_w,
        'max_consecutive_losses': max_l,
        'long_trades': len(longs),
        'short_trades': len(shorts),
    }
