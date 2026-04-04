import urllib.request
import urllib.parse
import json

data = urllib.parse.urlencode({'username': 'test2@spendwise.com', 'password': 'admin'}).encode('ascii')
req = urllib.request.Request("http://15.206.178.181:8000/auth/login", data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
#/http://15.206.178.181:8000/docs#/auth/register_user_auth_register_post
try:
    with urllib.request.urlopen(req) as response:
        print("SUCCESS:", response.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTP ERROR {e.code}:", e.read().decode())
except Exception as e:
    print("FATAL ERROR:", getattr(e, 'read', lambda: str(e))())
