import os

path = r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\leaderboard.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'open(' in line and ('w' in line or 'a' in line) and 'encoding' not in line:
        print(f"Line {i+1}: {line.strip()}")
