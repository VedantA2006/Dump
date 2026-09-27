path = r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\autonomous_research_loop.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
in_func = False
for i, line in enumerate(lines):
    if 'def _execute_single_round' in line:
        in_func = True
    if in_func:
        if 'open(' in line or 'print(' in line or '.to_csv' in line or '.to_json' in line or 'write(' in line:
            print(f"Line {i+1}: {line.strip()}")
        if 'def _' in line and i > 530:
            break
