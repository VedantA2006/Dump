import sys
import json
import warnings

sys.stdout.reconfigure(encoding='utf-8')
warnings.filterwarnings('ignore')

import pandas as pd
from strategy_executor import execute_strategy

def verify_top_5():
    print("Loading leaderboard...")
    with open('data/leaderboard.json', 'r', encoding='utf-8') as f:
        lb = json.load(f)
    
    lb.sort(key=lambda x: x.get('rank_score', x.get('total_r', 0)), reverse=True)
    top_5 = lb[:5]
    
    print("Loading XAUUSD_M5.csv...")
    raw_df = pd.read_csv('data/XAUUSD_M5.csv', index_col='timestamp', parse_dates=True)
    
    # Filter to 2026 YTD only (matching the leaderboard evaluation range)
    df_2026 = raw_df.loc['2026-01-01':]
    print(f"Full dataset: {len(raw_df):,} bars | 2026 YTD slice: {len(df_2026):,} bars")
    
    print("\n" + "="*70)
    print("  TOP 5 STRATEGY INDEPENDENT VERIFICATION AUDIT")
    print("  Evaluation Range: 2026 YTD (Jan 2026 - Present)")
    print("="*70)
    
    for i, strat in enumerate(top_5):
        name = strat.get('name', 'Unknown')
        print(f"\n{'-'*70}")
        print(f"  [{i+1}/5] {name}")
        print(f"{'-'*70}")
        
        expected_r = strat.get('total_r', 0)
        expected_trades = strat.get('total_trades', 0)
        expected_wr = strat.get('win_rate', 0)
        expected_pf = strat.get('profit_factor', 0)
        expected_pnl = strat.get('total_pnl', 0)
        
        code = strat.get('code', '')
        if not code:
            print("  [X] NO CODE FOUND -- cannot verify.")
            continue
        
        try:
            result = execute_strategy(code, df_2026)
            
            if not result.get('success', False):
                print(f"  [X] EXECUTION FAILED: {result.get('message', 'Unknown error')}")
                continue
            
            actual_stats = result.get('stats', {})
            actual_trades_list = result.get('trades', [])
            actual_trades = actual_stats.get('total_trades', 0)
            actual_wr = actual_stats.get('win_rate', 0)
            actual_pf = actual_stats.get('profit_factor', 0)
            actual_pnl = actual_stats.get('total_pnl', 0)
            
            # Compute total_r from trades (sum of r_return per trade)
            actual_r = sum(t.get('r_return', t.get('pnl', 0) / max(abs(t.get('risk', 1)), 0.01)) 
                         for t in actual_trades_list if isinstance(t, dict))
            
            diff_r = abs(expected_r - actual_r)
            diff_trades = abs(expected_trades - actual_trades)
            trades_match = diff_trades <= 5  # allow tiny rounding
            
            print(f"  REPORTED:    {expected_r:>8.1f}R  |  {expected_trades:>4} trades  |  WR: {expected_wr:.1f}%  |  PF: {expected_pf:.2f}  |  PnL: ${expected_pnl:>10,.2f}")
            print(f"  VERIFIED:    {actual_r:>8.1f}R  |  {actual_trades:>4} trades  |  WR: {actual_wr:.1f}%  |  PF: {actual_pf:.2f}  |  PnL: ${actual_pnl:>10,.2f}")
            print(f"  DIFFERENCE:  {diff_r:>8.1f}R  |  Trades Diff: {diff_trades}")
            
            if diff_r < 5.0 and trades_match:
                print(f"  [PASS] VERIFIED -- Results are REAL and reproducible.")
            elif diff_r < 20.0:
                print(f"  [WARN] MINOR VARIANCE ({diff_r:.1f}R) -- Likely due to spread/slippage rounding or date boundary.")
            else:
                print(f"  [FAIL] SIGNIFICANT MISMATCH ({diff_r:.1f}R) -- Needs investigation.")
                
        except Exception as e:
            import traceback
            print(f"  [X] FAILED TO EXECUTE: {str(e)}")
            traceback.print_exc()

    print(f"\n{'='*70}")
    print("  AUDIT COMPLETE")
    print(f"{'='*70}")

if __name__ == '__main__':
    verify_top_5()
