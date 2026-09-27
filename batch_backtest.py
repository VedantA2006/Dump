"""
Full 5-Year Batch Backtester — Top 20 strategies with complete month-wise returns.
No year filter. Full percentage returns and drawdown.
"""
import os, sys, json, time
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(line_buffering=True)

from strategy_executor import execute_strategy
from backtest import run_backtest

def compute_monthly_pct(trades, initial_capital=100000.0):
    """Compute month-wise PnL% with NO year filter."""
    if not trades:
        return {}
    records = []
    for t in trades:
        en_time = t.get('entry_time')
        if not en_time:
            continue
        try:
            dt = pd.to_datetime(en_time)
            month_key = dt.strftime('%b %Y')
            month_sort = dt.strftime('%Y-%m')
        except:
            continue
        pnl = t.get('pnl', 0.0)
        pnl_pct = (pnl / initial_capital) * 100
        records.append({'month': month_key, 'month_sort': month_sort, 'pnl': pnl, 'pnl_pct': pnl_pct})
    
    if not records:
        return {}
    
    df_t = pd.DataFrame(records)
    monthly = df_t.groupby(['month_sort', 'month']).agg(
        pnl=('pnl', 'sum'),
        pnl_pct=('pnl_pct', 'sum'),
        trades=('pnl', 'count')
    ).reset_index()
    monthly = monthly.sort_values('month_sort')
    
    result = {}
    for _, row in monthly.iterrows():
        result[row['month']] = {
            'pnl': round(float(row['pnl']), 2),
            'pnl_pct': round(float(row['pnl_pct']), 2),
            'trades': int(row['trades'])
        }
    return result

def run_batch():
    t0 = time.time()
    INITIAL_CAPITAL = 100000.0
    
    print(f"[1/4] Loading 5-year M5 data...", flush=True)
    df = pd.read_csv(r'data copy\XAUUSD_M5.csv')
    df['datetime'] = pd.to_datetime(df['timestamp'])
    df.set_index('datetime', inplace=True)
    print(f"  -> {len(df):,} bars ({df.index[0]} to {df.index[-1]})", flush=True)
    
    print(f"[2/4] Loading top 20 strategies...", flush=True)
    with open(r'data\leaderboard.json', 'r', encoding='utf-8') as f:
        strategies = json.load(f)
    strategies.sort(key=lambda x: x.get('rank_score', 0.0), reverse=True)
    strategies = strategies[:20]
    print(f"  -> Top 20 selected", flush=True)
    
    print(f"[3/4] Backtesting with FULL 5-year returns...", flush=True)
    
    results = []
    
    for i, strat in enumerate(strategies):
        code = strat.get('code')
        if not code or not code.strip():
            continue
        
        name = strat.get('name', f'Strategy_{i}')
        
        try:
            res = execute_strategy(code, df)
            if not res.get('success'):
                print(f"  [{i+1}/20] X {name[:50]} -- failed", flush=True)
                continue
                
            stats = res.get('stats', {})
            trades = res.get('trades', [])
            
            total_pnl = float(stats.get('total_pnl', 0.0))
            total_return_pct = round((total_pnl / INITIAL_CAPITAL) * 100, 2)
            max_dd_pct = round(float(stats.get('max_drawdown_pct', 0.0)), 2)
            
            # Full 5-year month-wise breakdown (NO 2026 filter)
            monthly = compute_monthly_pct(trades, INITIAL_CAPITAL)
            
            # Yearly breakdown
            yearly = {}
            for month_label, mdata in monthly.items():
                year = month_label.split()[-1]
                if year not in yearly:
                    yearly[year] = {'pnl': 0.0, 'pnl_pct': 0.0, 'trades': 0}
                yearly[year]['pnl'] += mdata['pnl']
                yearly[year]['pnl_pct'] += mdata['pnl_pct']
                yearly[year]['trades'] += mdata['trades']
            for y in yearly:
                yearly[y]['pnl'] = round(yearly[y]['pnl'], 2)
                yearly[y]['pnl_pct'] = round(yearly[y]['pnl_pct'], 2)
            
            entry = {
                'rank': 0,
                'name': name,
                'total_return_pct': total_return_pct,
                'total_pnl': round(total_pnl, 2),
                'max_drawdown_pct': max_dd_pct,
                'profit_factor': float(stats.get('profit_factor', 0.0)),
                'win_rate': float(stats.get('win_rate', 0.0)),
                'total_trades': int(stats.get('total_trades', len(trades))),
                'sharpe': float(stats.get('sharpe_ratio', 0.0)),
                'monthly': monthly,
                'yearly': yearly,
            }
            results.append(entry)
            
            elapsed = time.time() - t0
            avg_per = elapsed / (i + 1)
            remaining = avg_per * (20 - i - 1)
            
            print(f"  [{i+1}/20] OK {name[:45]:<45} | {total_return_pct:>+8.1f}% | DD={max_dd_pct:.1f}% | PF={stats.get('profit_factor',0):.2f} | {stats.get('total_trades',0)} trades | ETA: {remaining/60:.1f}m", flush=True)
            
        except Exception as e:
            print(f"  [{i+1}/20] X {name[:50]} -- {str(e)[:60]}", flush=True)
    
    # Sort by return %
    results.sort(key=lambda x: x['total_return_pct'], reverse=True)
    for idx, item in enumerate(results):
        item['rank'] = idx + 1
    
    # Save full JSON
    out_path = r'data copy\leaderboard_5year.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    elapsed = time.time() - t0
    print(f"\n{'='*90}", flush=True)
    print(f"  COMPLETE in {elapsed/60:.1f} min | {len(results)} strategies", flush=True)
    print(f"  Saved: {out_path}", flush=True)
    print(f"{'='*90}", flush=True)
    
    # Print leaderboard
    print(f"\n  {'Rank':<5} {'Strategy':<45} {'5Y Return%':>10} {'MaxDD%':>8} {'PF':>6} {'WR':>6} {'Trades':>7}", flush=True)
    print(f"  {'-'*5} {'-'*45} {'-'*10} {'-'*8} {'-'*6} {'-'*6} {'-'*7}", flush=True)
    for r in results:
        print(f"  {r['rank']:<5} {r['name'][:45]:<45} {r['total_return_pct']:>+9.1f}% {r['max_drawdown_pct']:>7.1f}% {r['profit_factor']:>6.2f} {r['win_rate']:>5.1f}% {r['total_trades']:>7}", flush=True)
    
    # Print yearly breakdown for top 5
    print(f"\n  YEARLY BREAKDOWN (Top 5):", flush=True)
    for r in results[:5]:
        print(f"\n  {r['rank']}. {r['name'][:50]}", flush=True)
        for year in sorted(r['yearly'].keys()):
            yd = r['yearly'][year]
            print(f"     {year}: {yd['pnl_pct']:>+8.2f}%  (${yd['pnl']:>+10,.2f})  [{yd['trades']} trades]", flush=True)

if __name__ == '__main__':
    run_batch()
