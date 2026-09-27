import os

target_dir = r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137'
files_to_check = ['static/app.js', 'templates/index.html']

for file in files_to_check:
    path = os.path.join(target_dir, file)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if 'mistral/codestral-latest' in line:
                print(f"[{file}] Line {i+1}: {line.strip()}")
