import os

target = r'c:\Users\vedan\Downloads\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\Terminal-Elvaris-9166cf3d97042f397526453b967f54dbf1dc1137\templates\index.html'

with open(target, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('>mistral/codestral-latest<', '>auto<')
content = content.replace('OmniRoute LLM (mistral/codestral-latest)', 'OmniRoute LLM (auto)')
content = content.replace('placeholder="mistral/codestral-latest"', 'placeholder="auto"')
content = content.replace("value='mistral/codestral-latest'", "value='auto'")

with open(target, 'w', encoding='utf-8') as f:
    f.write(content)

print("Replaced in index.html")
