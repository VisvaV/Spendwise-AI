import sys
import os
sys.path.insert(0, os.path.abspath('backend'))

from app.services.auth import create_access_token, SECRET_KEY, ALGORITHM
from app.api.deps import get_current_user
import jwt

try:
    print("Testing token creation...")
    token = create_access_token(data={"sub": "superadmin@spendwise.com"})
    print("TOKEN =", token)
    
    print("Testing token decode...")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    print("PAYLOAD =", payload)
except Exception as e:
    print("CRASH:", type(e), e)
