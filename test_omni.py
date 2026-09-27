import requests
import json

try:
    url = "http://localhost:20128/v1/chat/completions"
    payload = {
        "model": "auto",
        "messages": [{"role": "user", "content": "Ping."}],
        "max_tokens": 10
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    print("STATUS:", response.status_code)
    print("BODY:", response.text)
    print("HEADERS:", dict(response.headers))
except Exception as e:
    print("ERROR:", e)
