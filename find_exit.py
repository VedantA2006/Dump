import os
import glob
import re

repo = r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137'
for py_file in glob.glob(f"{repo}/*.py"):
    with open(py_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if re.search(r'sys\.exit\(', line):
                print(f"Found in {os.path.basename(py_file)}: Line {i+1}: {line.strip()}")
