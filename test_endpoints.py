import requests

print("Attempting to hit API via Nginx Proxy on port 80/3000...")
res_login = requests.post(
    "http://15.206.178.181:3000/api/auth/login",
    data={"username": "superadmin@spendwise.com", "password": "superadmin"}
)

print("LOGIN STATUS:", res_login.status_code)
if res_login.status_code == 200:
    token = res_login.json()["access_token"]
    print("TOKEN RECEIVED")
    
    res_me = requests.get(
        "http://15.206.178.181:3000/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    print("ME STATUS:", res_me.status_code)
    print("ME RESPONSE:", res_me.text)
else:
    print("LOGIN FAIL:", res_login.text)
