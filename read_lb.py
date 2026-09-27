import json

try:
    with open(r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\data\leaderboard.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    lb_list = data if isinstance(data, list) else data.get('leaderboard', [])
        
    print(f"Total strategies in leaderboard: {len(lb_list)}")
    print("\nLast 3 Generated Strategies:")
    
    recent = lb_list[-3:]
    for strat in recent:
        print(f"Name: {strat.get('archetype_name')}")
        print(f"Total R: {strat.get('val_total_r')} (Train R: {strat.get('total_r')})")
        print(f"Profit Factor: {strat.get('val_profit_factor')}")
        print("-" * 20)
        code = strat.get('code', '')
        print(code[:300] + "\n... [TRUNCATED]")
        print("=" * 40)
except Exception as e:
    print(f"Error reading leaderboard: {e}")
