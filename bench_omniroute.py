import time
import requests
import json

url = "http://localhost:20128/v1/chat/completions"
headers = {
    "Authorization": "Bearer any",
    "Content-Type": "application/json"
}

payload = {
    "model": "mistral/codestral-latest",
    "messages": [
        {"role": "system", "content": "You are a quantitative trading developer."},
        {"role": "user", "content": "Write a python function calculate_signals(df) using EMA 20 and ATR 14 for Gold 5m."}
    ],
    "max_tokens": 800,
    "temperature": 0.5
}

t0 = time.time()
try:
    res = requests.post(url, headers=headers, json=payload, timeout=30)
    dt = time.time() - t0
    print(f"Status: {res.status_code} in {dt:.2f}s")
    data = res.json()
    content = data['choices'][0]['message']['content']
    print(f"Content length: {len(content)} chars")
    print("Content preview:", content[:150])
except Exception as e:
    print(f"Error after {time.time() - t0:.2f}s: {e}")
