from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import HTTPException, Request, status
from service.auth_service import AuthService
from exception.global_exception_handler import get_http_exception_response

class TokenMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.auth_service = AuthService()

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)
        # Ignore token check for specific APIs
        WHITE_LIST_API = ["/api/login", "/api/logout", "/api/signup", "/api/verify-email-signup", 
                "/api/forgot-password", "/api/reset-password", "/api/check-2fa", 
                "/api/login/google", "/test", "/docs", "/openapi.json"]

        if request.url.path in WHITE_LIST_API:
            response = await call_next(request)
            return response
        
        # Get the token from cookies
        token = request.cookies.get("access_token")
        if not token:
            return get_http_exception_response(HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing"))

        try:
            # Validate the token
            result = self.auth_service.check_token(token)
            # Store the decoded token in request state
            request.state.user = result
        except Exception as e:
            print("error: ", e)
            return get_http_exception_response(HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"))

        # Process the request further
        response = await call_next(request)
        return response
