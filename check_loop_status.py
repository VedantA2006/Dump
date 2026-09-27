import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

try:
    res = urllib.request.urlopen('http://127.0.0.1:5000/api/research/status')
    data = json.loads(res.read().decode('utf-8'))
    print(f"Status: {data.get('status')}")
    print(f"Current Round: {data.get('current_round')} / {data.get('max_rounds')}")
    print(f"Active Agent: {data.get('active_agent')}")
    print(f"Current Hypothesis: {data.get('current_hypothesis')}")
    print(f"Total Candidates: {data.get('total_candidates')}")
    print(f"Engine: {data.get('engine')}")
    print("\n--- RECENT 25 LOGS ---")
    for log in data.get('recent_logs', [])[-25:]:
        print(f"[{log.get('timestamp')}] [{log.get('agent')}] ({log.get('level')}): {log.get('message')}")
except Exception as e:
    print("Error:", e)
