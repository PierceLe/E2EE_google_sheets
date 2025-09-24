from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyCookie
from controller.auth_controller import auth_router
from controller.user_controller import user_router
from controller.sheet_controller import sheet_router
from exception.app_exception import AppException
from exception.global_exception_handler import app_exception_handler, http_exception_handler
from middleware.token_middleware import TokenMiddleware
from utils.token import verify_token
from fastapi.middleware.cors import CORSMiddleware

if not os.path.exists("bucket"):
    os.makedirs("bucket")

app = FastAPI(
    title="E2EE Google Sheets API",
    description="""
    ## End-to-End Encrypted Google Sheets API

    This API provides secure, end-to-end encrypted access to Google Sheets with advanced user management and access control.

    ### Features:
    * 🔐 **End-to-End Encryption**: All sheet data is encrypted before storage
    * 🔑 **RSA Key Management**: Secure key generation and management
    * 👥 **User Access Control**: Fine-grained permissions (owner, editor, viewer)
    * 🔒 **PIN Protection**: Additional security layer with PIN-based access
    * 📊 **Sheet Management**: Create, share, and collaborate on encrypted sheets
    * 🔍 **Advanced Filtering**: Search and filter sheets by various criteria

    ### Security Model:
    - User authentication via Google OAuth2
    - Client-side RSA key pair generation
    - AES sheet encryption with RSA-encrypted keys
    - JWT-based session management
    - PIN-based private key protection

    ### API Workflow:
    1. **Authentication**: Login with Google OAuth2 token
    2. **Key Setup**: Generate RSA keys and set PIN
    3. **Sheet Creation**: Create encrypted sheets with member access
    4. **Collaboration**: Add/remove users with specific roles
    5. **Data Access**: Decrypt and access sheet data securely

    ### 🔑 Authentication Methods:
    - **Cookie Authentication**: Use access_token cookie (preferred for browser)
    - **Bearer Token**: Use Authorization header with JWT token
    - **Testing**: Use the 🔒 buttons in Swagger UI to authenticate
    """,
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:9990",
            "description": "Development server"
        }
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Define Security Schemes for Swagger UI
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "CookieAuth": {
            "type": "apiKey",
            "in": "cookie",
            "name": "access_token",
            "description": "JWT token stored in HTTP-only cookie. Get this token from /api/login/google endpoint."
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token in Authorization header. Format: 'Bearer <token>'"
        }
    }

    # Add global security requirement (optional - can be overridden per endpoint)
    openapi_schema["security"] = [
        {"CookieAuth": []},
        {"BearerAuth": []}
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Add Exception Handler
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# Add Middleware
app.add_middleware(TokenMiddleware,)


# Add cors
origins = [
    "http://localhost",
    "http://localhost:3000",
    "*"
]
app.add_middleware(CORSMiddleware,
                   allow_origins=origins,
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"])

# Add Router
app.include_router(
    auth_router,
    prefix="/api",
    tags=["🔐 Authentication"],
    responses={
        401: {"description": "Authentication failed"},
        400: {"description": "Invalid request data"}
    }
)
app.include_router(
    user_router,
    prefix="/api/user",
    tags=["👤 User Management"],
    responses={
        401: {"description": "Unauthorized access"},
        404: {"description": "User not found"}
    }
)
app.include_router(
    sheet_router,
    prefix="/api/sheet",
    tags=["📊 Sheet Management"],
    responses={
        401: {"description": "Unauthorized access"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Sheet not found"}
    }
)

app.mount("/api/bucket", StaticFiles(directory="bucket"), name="bucket")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9990)