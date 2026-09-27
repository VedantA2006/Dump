import json
import os

log_file = r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\omniroute-request-logs-1h-2026-09-26.json'
try:
    with open(log_file, 'r', encoding='utf-8') as f:
        logs = json.load(f)
    if logs:
        last_log = logs[-1]
        print(f"Timestamp: {last_log.get('timestamp')}")
        print(f"Archetype: {last_log.get('archetype')}")
        print("-" * 40)
        print("Generated Code:")
        print(last_log.get('response', '')[:1000] + "\n... [TRUNCATED]")
    else:
        print("Log file is empty.")
except Exception as e:
    print(f"Error reading logs: {e}")
