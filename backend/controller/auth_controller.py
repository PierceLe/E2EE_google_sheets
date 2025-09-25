from fastapi import APIRouter, HTTPException, status, Depends, Response, Request, Query
from dto.response.success_response import SuccessResponse
from dto.request.auth.google_login_request import GoogleLoginRequest
from service.auth_service import AuthService

auth_router = APIRouter()


@auth_router.post(
    "/login/google",
    summary="Google OAuth Login",
    description="""
    **Authenticate user with Google OAuth2 token**
    
    This endpoint allows users to login or register using their Google account.
    The process:
    1. Client obtains Google OAuth2 token from Google's authorization server
    2. Server validates the token with Google
    3. Creates new user account if first login, or logs in existing user
    4. Returns JWT access token and sets secure HTTP-only cookie
    
    **Security Features:**
    - Validates Google token authenticity
    - Sets secure, HTTP-only cookies
    - Generates JWT tokens for API access
    - Automatic user creation for new Google accounts
    """,
    response_description="JWT access token for API authentication",
    responses={
        200: {
            "description": "Successful authentication",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "successfully",
                        "result": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                    }
                }
            }
        },
        400: {
            "description": "Invalid Google token",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid Google token"
                    }
                }
            }
        }
    },
    tags=["🔐 Authentication"],
)
def login_with_google(
    response: Response, 
    data: GoogleLoginRequest, 
    auth_service: AuthService = Depends(AuthService)
):
    """
    Authenticate user with Google OAuth2 token and return JWT access token.
    
    Args:
        response: FastAPI Response object for setting cookies
        data: Google login request containing OAuth2 token
        auth_service: Injected authentication service
        
    Returns:
        SuccessResponse containing JWT access token
        
    Raises:
        HTTPException: 400 if Google token is invalid
    """
    try:
        response.delete_cookie("access_token")
        print("1")
        user = auth_service.login_or_create_google_user(data.token)
        print("2")
        access_token = auth_service.create_token(data={"sub": user.email})
        print("3")
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


