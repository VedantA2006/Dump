import os

target_dir = r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137'
files_to_check = ['ai_generator.py', 'ai_research_agents.py', 'app.py', 'autonomous_research_loop.py']
for file in files_to_check:
    path = os.path.join(target_dir, file)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            for i, line in enumerate(lines):
                if 'omniroute' in line.lower() or 'groq' in line.lower() or 'openai' in line.lower():
                    print(f"[{file}] Line {i+1}: {line.strip()}")
        except Exception:
            pass
