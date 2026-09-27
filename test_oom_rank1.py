import pandas as pd
import numpy as np
import traceback
import json
from strategy_executor import execute_strategy

try:
    with open('c:\\Users\\vedan\\Downloads\\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\\data\\leaderboard.json', 'r') as f:
        rank1_code = json.load(f)[0]['code']

    df = pd.read_csv(r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\data copy\XAUUSD_M5.csv', parse_dates=True, index_col='timestamp')
    df = df.iloc[:247817].copy()
    print(f"Testing rank1 code with {len(df)} rows...")
    res = execute_strategy(rank1_code, df)
    print("Success:", res.get("success"))
    if not res.get("success"):
        print("Error:", res.get("message"))
        print("Traceback:")
        print(res.get("traceback"))
except Exception as e:
    traceback.print_exc()
