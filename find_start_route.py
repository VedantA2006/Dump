import os

with open(r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\app.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if '/start' in line or 'research_loop.start' in line:
            print(f"Line {i+1}: {line.strip()}")
