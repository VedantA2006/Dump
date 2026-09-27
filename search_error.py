import os

target_dir = r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137'
for file in os.listdir(target_dir):
    if file.endswith('.py'):
        path = os.path.join(target_dir, file)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            for i, line in enumerate(lines):
                if 'open(' in line and ('w' in line or 'a' in line) and 'encoding' not in line:
                    print(f"[{file}] Line {i+1}: {line.strip()}")
        except Exception:
            pass
