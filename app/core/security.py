import os
import firebase_admin
from firebase_admin import auth, credentials
from fastapi import HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Bypass Firebase initialization for local development if SKIP_AUTH is true
if os.environ.get("SKIP_AUTH") != "true":
    try:
        if not firebase_admin._apps:
            # Check environment variable first, then fallback to standard mount path
            cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/etc/secrets/firebase-service-account.json")
            
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
            else:
                # Local development fallback
                cred = credentials.ApplicationDefault()
                
            firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Warning: Firebase Admin not initialized: {e}")
else:
    print("Local setup: SKIP_AUTH is true, bypassing Firebase initialization.")

security = HTTPBearer()

async def verify_token(request: Request, token: HTTPAuthorizationCredentials = Security(security)):
    """Verifies Firebase ID token and returns user info."""
    if os.environ.get("SKIP_AUTH") == "true":
        return {"uid": "test_user", "email": "test@example.com", "name": "Test User"}

    try:
        decoded_token = auth.verify_id_token(token.credentials)
        request.state.user_id = decoded_token.get("uid")
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication credentials: {e}")
