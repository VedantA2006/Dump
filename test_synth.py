import sys
import json
sys.path.append(r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137')
from ai_research_agents import synthesize_archetype_code

with open(r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\data\archetypes.json', 'r') as f:
    archs = json.load(f)

for i, a in enumerate(archs):
    if "Linear Regression Slope" in a['name']:
        print("Found at idx", i)
        code = synthesize_archetype_code(i)
        print(code)
        break
