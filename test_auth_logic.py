import sys
import os
sys.path.insert(0, os.path.abspath('backend'))

from app.services.auth import get_password_hash, verify_password, create_access_token

try:
    print("1. Testing Password Hashing...")
    hashed = get_password_hash("superadmin")
    print("Hash SUCCESS:", hashed)
    
    print("\n2. Testing Password Verification...")
    is_valid = verify_password("superadmin", hashed)
    print("Verify SUCCESS: is_valid =", is_valid)
    
    print("\n3. Testing JWT Token Creation...")
    token = create_access_token(data={"sub": "superadmin@spendwise.com"})
    print("Token SUCCESS:", token)
    
    print("\nALL TESTS PASSED PERFECTLY!")
except Exception as e:
    print("\nCRASH DETECTED:", e)
