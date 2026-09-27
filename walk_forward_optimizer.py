"""
5-Year Walk-Forward Optimizer — Tick and Volume Confluence #117.
Smaller focused grid for faster execution.
Train: 2021-2024 | Test: 2025-2026 | Monte Carlo: 1000 paths.
"""
import sys, json, time, itertools
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(line_buffering=True)

from strategy_executor import execute_strategy
from monte_carlo import run_monte_carlo

STRATEGY_TEMPLATE = """
def calculate_signals(df):
    times = df.index if isinstance(df.index, pd.DatetimeIndex) else pd.to_datetime(df.get('dt', df.get('datetime', df.index)))
    mins = times.hour * 60 + times.minute
    sess = (6 * 60 <= mins) & (mins < 18 * 60)

    sw_highs, sw_lows = find_swings(df, swing_len={swing_len})
    levels = daily_levels(df)
    vwap_line = vwap(df)

    ssl_sweep = (df['low'] < sw_lows) & (df['close'] > sw_lows)
    bsl_sweep = (df['high'] > sw_highs) & (df['close'] < sw_highs)

    armed_long = ssl_sweep.rolling({arm_window}, min_periods=1).max() == 1
    armed_short = bsl_sweep.rolling({arm_window}, min_periods=1).max() == 1

    raw_bull = (armed_long & (df['close'] > vwap_line) & (df['close'] > levels['s1']) & sess)
    df['bull_signal'] = raw_bull & (~raw_bull.shift(1).fillna(False))

    raw_bear = (armed_short & (df['close'] < vwap_line) & (df['close'] < levels['r1']) & sess)
    df['bear_signal'] = raw_bear & (~raw_bear.shift(1).fillna(False))

    atr_val = atr(df, 14)
    df['sl_long'] = np.minimum(df['low'], sw_lows) - ({atr_mult} * atr_val)
    df['sl_short'] = np.maximum(df['high'], sw_highs) + ({atr_mult} * atr_val)

    risk_long = np.maximum(df['close'] - df['sl_long'], {min_risk})
    risk_short = np.maximum(df['sl_short'] - df['close'], {min_risk})

    df['tp1_long'] = df['close'] + (risk_long * {rr1})
    df['tp1_short'] = df['close'] - (risk_short * {rr1})

    return df
"""

def run_optimizer():
    t0 = time.time()
    IC = 100000.0
    
    print("=" * 80, flush=True)
    print("  5-YEAR WALK-FORWARD OPTIMIZER", flush=True)
    print("  Strategy: 15-Minute Opening Range Breakout (ORB) (Rank #1)", flush=True)
    print("=" * 80, flush=True)
    
    print("\n[1/5] Loading 5-year M5 data...", flush=True)
    df = pd.read_csv(r'data copy\XAUUSD_M5.csv')
    df['datetime'] = pd.to_datetime(df['timestamp'])
    df.set_index('datetime', inplace=True)
    print(f"  -> {len(df):,} bars ({df.index[0]} to {df.index[-1]})", flush=True)
    
    train_df = df[df.index < '2025-01-01'].copy()
    test_df = df[df.index >= '2025-01-01'].copy()
    print(f"  -> Train: {len(train_df):,} bars (2021-2024)", flush=True)
    print(f"  -> Test:  {len(test_df):,} bars (2025-2026) [OUT-OF-SAMPLE]", flush=True)
    
    # Focused grid for ORB
    param_grid = {
        'swing_len': [5, 7, 9],
        'arm_window': [8, 10, 12],
        'atr_mult': [1.5, 1.8, 2.0],
        'min_risk': [4.0],
        'rr1': [3.5, 3.8, 4.2]
    }
    
    keys = list(param_grid.keys())
    combos = list(itertools.product(*[param_grid[k] for k in keys]))
    total = len(combos)
    
    print(f"\n[2/5] Parameter Grid: {total} combinations", flush=True)
    for k, v in param_grid.items():
        print(f"  {k}: {v}", flush=True)
    
    print(f"\n[3/5] Sweeping on TRAINING data (2021-2024)...", flush=True)
    
    results = []
    
    for i, combo in enumerate(combos):
        params = dict(zip(keys, combo))
        code = STRATEGY_TEMPLATE.format(**params)
        
        try:
            res = execute_strategy(code, train_df)
            if not res.get('success'):
                continue
            stats = res.get('stats', {})
            trades = res.get('trades', [])
            tt = int(stats.get('total_trades', 0))
            if tt < 15:
                continue
            pnl = float(stats.get('total_pnl', 0.0))
            pf = float(stats.get('profit_factor', 0.0))
            wr = float(stats.get('win_rate', 0.0))
            dd = float(stats.get('max_drawdown_pct', 0.0))
            ret = round((pnl / IC) * 100, 2)
            score = ret - (dd * 0.5) + (pf * 10) + (wr * 0.3)
            
            results.append({
                'params': params, 'code': code,
                'train_ret': ret, 'train_pf': round(pf,2), 'train_wr': round(wr,1),
                'train_dd': round(dd,1), 'train_trades': tt, 'score': round(score,2),
            })
        except:
            continue
        
        if (i+1) % 10 == 0 or i == 0:
            elapsed = time.time() - t0
            avg = elapsed / (i+1)
            eta = avg * (total - i - 1)
            best_so_far = max([r['train_ret'] for r in results]) if results else 0
            print(f"  [{i+1}/{total}] {len(results)} viable | best={best_so_far:+.1f}% | ETA: {eta/60:.1f}min", flush=True)
    
    if not results:
        print("  NO viable combos found!", flush=True)
        return
    
    results.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"\n  Top 10 Training Results:", flush=True)
    print(f"  {'#':<3} {'Ret%':>8} {'PF':>6} {'WR%':>6} {'DD%':>7} {'Trd':>5} | Key Params", flush=True)
    print(f"  {'-'*3} {'-'*8} {'-'*6} {'-'*6} {'-'*7} {'-'*5} | {'-'*50}", flush=True)
    for j, r in enumerate(results[:10]):
        p = r['params']
        print(f"  {j+1:<3} {r['train_ret']:>+7.1f}% {r['train_pf']:>6.2f} {r['train_wr']:>5.1f}% {r['train_dd']:>6.1f}% {r['train_trades']:>5} | sw={p['swing_len']} arm={p['arm_window']} atr_m={p['atr_mult']} rr={p['rr1']}", flush=True)
    
    # PHASE 2: Validate top 10 on OOS
    print(f"\n[4/5] Validating top 10 on OUT-OF-SAMPLE (2025-2026)...", flush=True)
    
    validated = []
    for j, r in enumerate(results[:10]):
        try:
            res = execute_strategy(r['code'], test_df)
            if not res.get('success'):
                continue
            stats = res.get('stats', {})
            trades = res.get('trades', [])
            pnl = float(stats.get('total_pnl', 0.0))
            ret = round((pnl / IC) * 100, 2)
            pf = round(float(stats.get('profit_factor', 0.0)), 2)
            wr = round(float(stats.get('win_rate', 0.0)), 1)
            dd = round(float(stats.get('max_drawdown_pct', 0.0)), 1)
            tt = int(stats.get('total_trades', 0))
            r['test_ret'] = ret; r['test_pf'] = pf; r['test_wr'] = wr
            r['test_dd'] = dd; r['test_trades'] = tt
            validated.append(r)
            tag = "PASS" if ret > 0 and pf > 1.0 else "FAIL"
            print(f"  #{j+1} [{tag}] Train: {r['train_ret']:>+7.1f}% (PF {r['train_pf']}) | Test: {ret:>+7.1f}% (PF {pf}) | DD={dd:.1f}%", flush=True)
        except Exception as e:
            print(f"  #{j+1} [ERR] {str(e)[:50]}", flush=True)
    
    passed = [v for v in validated if v.get('test_ret', 0) > 0 and v.get('test_pf', 0) > 1.0]
    if not passed:
        print("  WARNING: No combo passed OOS. Using best training result.", flush=True)
        passed = validated[:1] if validated else results[:1]
    
    # PHASE 3: Monte Carlo on best (full 5Y)
    best = passed[0]
    print(f"\n[5/5] Full 5-year backtest + Monte Carlo (1000 paths) on best combo...", flush=True)
    
    full_res = execute_strategy(best['code'], df)
    fs = full_res.get('stats', {})
    ft = full_res.get('trades', [])
    full_pnl = float(fs.get('total_pnl', 0.0))
    full_ret = round((full_pnl / IC) * 100, 2)
    full_dd = round(float(fs.get('max_drawdown_pct', 0.0)), 2)
    
    mc = run_monte_carlo(ft, num_simulations=1000)
    
    # Yearly + monthly breakdown
    monthly = {}
    for t in ft:
        try:
            dt = pd.to_datetime(t.get('entry_time'))
            sk = dt.strftime('%Y-%m')
            lbl = dt.strftime('%b %Y')
            if sk not in monthly:
                monthly[sk] = {'label': lbl, 'pnl': 0.0, 'trades': 0}
            monthly[sk]['pnl'] += t.get('pnl', 0.0)
            monthly[sk]['trades'] += 1
        except:
            pass
    
    yearly = {}
    for sk in sorted(monthly.keys()):
        y = sk.split('-')[0]
        if y not in yearly:
            yearly[y] = {'pnl': 0.0, 'trades': 0}
        yearly[y]['pnl'] += monthly[sk]['pnl']
        yearly[y]['trades'] += monthly[sk]['trades']
    
    elapsed = time.time() - t0
    
    print(f"\n{'='*80}", flush=True)
    print(f"  OPTIMIZATION COMPLETE ({elapsed/60:.1f} min)", flush=True)
    print(f"{'='*80}", flush=True)
    
    p = best['params']
    print(f"\n  OPTIMAL PARAMETERS:", flush=True)
    for k, v in p.items():
        print(f"    {k:15} = {v}", flush=True)
    
    print(f"\n  ORIGINAL vs OPTIMIZED:", flush=True)
    print(f"    {'':30} {'ORIGINAL':>12} {'OPTIMIZED':>12}", flush=True)
    print(f"    {'5Y Return%':30} {'    N/A':>12} {full_ret:>+11.1f}%", flush=True)
    print(f"    {'5Y Max DD%':30} {'    N/A':>12} {full_dd:>11.1f}%", flush=True)
    print(f"    {'Train (2021-2024)':30} {'N/A':>12} {best['train_ret']:>+11.1f}%", flush=True)
    print(f"    {'Test (2025-2026)':30} {'N/A':>12} {best.get('test_ret',0):>+11.1f}%", flush=True)
    print(f"    {'Profit Factor':30} {'   1.48':>12} {fs.get('profit_factor',0):>11.2f}", flush=True)
    print(f"    {'Win Rate':30} {'  27.9%':>12} {fs.get('win_rate',0):>10.1f}%", flush=True)
    print(f"    {'Total Trades':30} {'    394':>12} {fs.get('total_trades',0):>12}", flush=True)
    
    print(f"\n  MONTE CARLO (1000 paths):", flush=True)
    for k in ['median_final_r','expected_max_dd_r','var_95_max_dd_r','risk_of_ruin_10r','risk_of_ruin_20r','probability_of_profit']:
        print(f"    {k:30} {mc.get(k, 'N/A')}", flush=True)
    
    print(f"\n  YEARLY BREAKDOWN:", flush=True)
    for y in sorted(yearly.keys()):
        yd = yearly[y]
        pct = round((yd['pnl'] / IC) * 100, 2)
        print(f"    {y}: {pct:>+8.2f}%  (${yd['pnl']:>+12,.2f})  [{yd['trades']} trades]", flush=True)
    
    print(f"\n  MONTHLY BREAKDOWN:", flush=True)
    for sk in sorted(monthly.keys()):
        md = monthly[sk]
        pct = round((md['pnl'] / IC) * 100, 2)
        print(f"    {md['label']:>10}: {pct:>+7.2f}%  (${md['pnl']:>+10,.2f})  [{md['trades']} trades]", flush=True)
    
    # Save
    save = {
        'name': '15-Minute ORB #1 (5Y Walk-Forward Optimized)',
        'original_params': {'swing_len':7,'arm_window':10,'atr_mult':1.8,'min_risk':4.0,'rr1':3.8},
        'optimized_params': p,
        'train_ret_pct': best['train_ret'], 'test_ret_pct': best.get('test_ret',0),
        'full_5y_ret_pct': full_ret, 'full_5y_dd_pct': full_dd,
        'full_5y_pf': round(float(fs.get('profit_factor',0)),2),
        'full_5y_trades': int(fs.get('total_trades',0)),
        'monte_carlo': mc,
        'yearly': {y: {'pnl_pct': round((d['pnl']/IC)*100,2), 'trades': d['trades']} for y,d in yearly.items()},
        'code': best['code'],
    }
    with open(r'data copy\orb_1_optimized_5y.json', 'w', encoding='utf-8') as f:
        json.dump(save, f, indent=2)
    print(f"\n  Saved: data copy/orb_1_optimized_5y.json", flush=True)

if __name__ == '__main__':
    run_optimizer()
