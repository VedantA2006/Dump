import sys
sys.stdout.reconfigure(encoding='utf-8')
from leaderboard import load_leaderboard

lb = load_leaderboard()
print(f"Total strategies in leaderboard: {len(lb)}")
for s in lb[:5]:
    stats = s.get('stats', {})
    print(f"\n#{s.get('rank')} - {s.get('name')}")
    print(f"   Return: {s.get('total_r')}R | WR: {stats.get('win_rate')}% | Trades: {stats.get('total_trades')} | PF: {stats.get('profit_factor')}")
    print(f"   Concept: {s.get('concept')[:100]}")
    code = s.get('code', '')
    print("   --- CODE SNIPPET ---")
    for line in code.split('\n')[:25]:
        print("   ", line)
