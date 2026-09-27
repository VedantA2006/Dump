import requests
import json

payload = {
    'model': 'qwen2.5-coder:3b',
    'messages': [
        {'role': 'system', 'content': 'You are a bot.'},
        {'role': 'user', 'content': 'Say hi'}
    ],
    'temperature': 0.7,
    'max_tokens': 50
}

try:
    r = requests.post('http://localhost:11434/v1/chat/completions', json=payload)
    print("Status:", r.status_code)
    print("Response:", r.text[:200])
except Exception as e:
    print(e)
