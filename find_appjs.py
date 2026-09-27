import os

path = r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\static\app.js'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'cfgProvider' in line or 'provider' in line.lower() or 'ollama' in line.lower() or 'omniroute' in line.lower():
        print(f"Line {i+1}: {line.strip()}")
        if i > 1100 and i < 1120:
             print(f"Line {i+1}: {line.strip()}")
