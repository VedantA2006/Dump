import os

path = r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\templates\index.html'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if '<select' in line.lower() or 'provider' in line.lower():
        print(f"Line {i+1}: {line.strip()}")
