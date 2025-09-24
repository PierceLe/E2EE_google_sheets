from fastapi import APIRouter, HTTPException, status, Depends, Response, Request, Query
from dto.response.success_response import SuccessResponse
from dto.request.auth.google_login_request import GoogleLoginRequest
from service.auth_service import AuthService

auth_router = APIRouter()


@auth_router.post("/login/google")
def login_with_google(response: Response, data: GoogleLoginRequest, 
                    auth_service: AuthService = Depends(AuthService)):
    try:
        response.delete_cookie("access_token")
        user = auth_service.login_or_create_google_user(data.token)

        access_token = auth_service.create_token(data={"sub": user.email})
        # Set cookie
        response.set_cookie(
            key="access_token",
            value=f"{access_token}",
            httponly=True,
            secure=True,
            samesite='Lax')

        return SuccessResponse(result=access_token)

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Google token")


