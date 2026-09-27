import os
path = r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\autonomous_research_loop.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i in range(740, 755):
        print(f"Line {i+1}: {lines[i].strip('\n')}")
