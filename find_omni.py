import os
path = r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\static\app.js'
with open(path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if "cfg.provider !== 'omniroute'" in line:
            print(f"Line {i+1}: {line.strip()}")
