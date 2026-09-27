import json

with open('omniroute-request-logs-1h-2026-09-26.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for log in data.get('logs', []):
    if log.get('status') == 200 and log.get('responseBody'):
        # Extract response text
        content = log['responseBody'].get('choices', [{}])[0].get('message', {}).get('content', '')
        if content and 'calculate_signals' in content:
            print("--- CODE FOUND ---")
            print(content)
            print("------------------")
            break
