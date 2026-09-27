import os
path = r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\autonomous_research_loop.py'
with open(path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'exceeded safety limit' in line or 'timeout' in line.lower():
            print(f"Line {i+1}: {line.strip()}")
