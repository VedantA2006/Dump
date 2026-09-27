import os
import sys
import collections

sys.stdout.reconfigure(encoding='utf-8')

log_file = r'C:\Users\vedan\.gemini\antigravity-ide\brain\3bf99679-48f9-4d36-8599-5bfefec38e07\.system_generated\tasks\task-2439.log'

if os.path.exists(log_file):
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = collections.deque(f, 30)
    print("".join(lines))
else:
    print(f"Log file does not exist.")
