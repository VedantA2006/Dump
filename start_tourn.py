import urllib.request
import json

req = urllib.request.Request(
    'http://127.0.0.1:5000/api/research/start',
    data=json.dumps({
        'rounds': 10000,
        'provider': 'omniroute',
        'model': 'mistral/codestral-latest',
        'endpoint': 'http://localhost:20128/v1',
        'force_restart': True
    }).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

try:
    res = urllib.request.urlopen(req)
    print("Start response:", res.read().decode('utf-8'))
except Exception as e:
    print("Start error:", e)
