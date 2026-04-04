import urllib.request
import json

data = json.dumps({
    "email": "test2@spendwise.com",
    "password": "admin",
    "name": "Test User",
    "role": "Admin"
}).encode('utf-8')

req = urllib.request.Request(
    "http://15.206.178.181:8000/auth/register", 
    data=data,
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req) as response:
        print("SUCCESS:", response.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTP ERROR {e.code}:", e.read().decode())
except Exception as e:
    print("FATAL ERROR:", getattr(e, 'read', lambda: str(e))())
