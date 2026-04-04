import jwt
from datetime import datetime, timedelta

def test():
    try:
        expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode = {"sub": "test", "exp": expire}
        token = jwt.encode(to_encode, "secret", algorithm="HS256")
        print("TOKEN CREATED:", token)
        
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])
        print("DECODED:", decoded)
    except Exception as e:
        print("CRASH:", type(e), str(e))

test()
