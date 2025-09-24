from fastapi import FastAPI, HTTPException, Depends, Request
from service.auth_service import AuthService

def verify_token(request: Request):
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Token missing in cookies")

    auth_service = AuthService()
    try:
        result = auth_service.check_token(token)
    
        email = result["sub"] 
        return email 
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token missing in cookies")