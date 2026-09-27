import os

target_dir = r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137'
for root, dirs, files in os.walk(target_dir):
    for file in files:
        if file.endswith('.py') or file.endswith('.js') or file.endswith('.html'):
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                for i, line in enumerate(lines):
                    if 'omniroute' in line.lower():
                        print(f"[{file}] Line {i+1}: {line.strip()}")
            except Exception:
                pass
