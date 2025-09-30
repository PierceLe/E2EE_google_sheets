from fastapi import APIRouter, HTTPException, status, Depends
from dto.request.auth.create_pin_request import Create_Pin_Request
from dto.request.auth.restore_private_key_request import Restore_Private_Key_Request
from service.user_service import UserService
from dto.response.success_response import SuccessResponse
from utils.utils import get_current_user
user_router = APIRouter()

@user_router.get(
    "/by-id",
    summary="Get User by ID",
    description="""
    **Retrieve user information by user ID**
    
    Fetches detailed user information including profile data and encryption status.
    This endpoint is typically used for displaying user information in shared sheets
    or for administrative purposes.
    
    **Use Cases:**
    - Display user profiles in sheet member lists
    - Verify user existence before adding to sheets
    - Administrative user management
    """,
    response_description="User information including profile and encryption status",
    responses={
        200: {
            "description": "User found successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "successfully",
                        "result": {
                            "user_id": "user_123",
                            "email": "user@example.com",
                            "name": "John Doe",
                            "picture": "https://example.com/avatar.jpg",
                            "has_pin": True,
                            "public_key": "-----BEGIN PUBLIC KEY-----..."
                        }
                    }
                }
            }
        },
        404: {
            "description": "User not found"
        }
    }
)
async def get_user(user_id: str, user_service: UserService = Depends(UserService)):
    """
    Retrieve user information by user ID.
    
    Args:
        user_id: Unique identifier for the user
        user_service: Injected user service
        
    Returns:
        SuccessResponse containing user information
    """
    user = user_service.get_user(user_id)
    return SuccessResponse(result=user)

@user_router.post(
    "/me",
    summary="Get Current User Profile",
    description="""
    **Get authenticated user's profile information**
    
    Retrieves the complete profile of the currently authenticated user,
    including encryption setup status and account details.
    
    **Authentication Required:** Yes (JWT token)
    
    **Returns:**
    - User profile information
    - Encryption key status
    - PIN setup status
    - Account creation date
    """,
    response_description="Current user's complete profile information",
)
async def get_me(current_user=Depends(get_current_user), user_service: UserService = Depends(UserService)):
    """
    Get the authenticated user's profile information.
    
    Args:
        current_user: Currently authenticated user from JWT token
        user_service: Injected user service
        
    Returns:
        SuccessResponse containing current user's profile
    """  
    current_user = user_service.get_user_by_email(current_user.email)
    return SuccessResponse(result=current_user)

@user_router.post(
    "/set-pin",
    summary="Setup PIN and Encryption Keys",
    description="""
    **Initialize user's encryption setup with PIN and RSA keys**
    
    This is a critical security setup step that must be completed after initial login.
    The process involves:
    
    1. **Client-side key generation**: RSA key pair generated in browser
    2. **PIN encryption**: Private key encrypted with user's PIN
    3. **Secure storage**: Only encrypted private key stored on server
    
    **Security Features:**
    - PIN never transmitted in plain text
    - Private key never stored unencrypted
    - Public key used for sheet key encryption
    - PIN required for private key decryption
    
    **One-time Setup:** This endpoint can typically only be called once per user.
    """,
    response_description="Confirmation of successful PIN and key setup",
    responses={
        200: {
            "description": "PIN and keys setup successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "successfully",
                        "result": {
                            "user_id": "user_123",
                            "email": "user@example.com",
                            "has_pin": True
                        }
                    }
                }
            }
        },
        400: {
            "description": "Invalid PIN format or keys already set"
        },
        401: {
            "description": "Authentication required"
        }
    }
)
async def set_pin_and_key(
    request: Create_Pin_Request,
    current_user=Depends(get_current_user),
    user_service: UserService = Depends(UserService)
):
    """
    Setup user's PIN and RSA encryption keys.
    
    Args:
        request: PIN and key setup request
        current_user: Currently authenticated user
        user_service: Injected user service
        
    Returns:
        SuccessResponse with updated user information
    """
    print("hi")
    print(current_user.user_id)
    print(request.pin)
    user_service.create_pin(current_user.user_id, request.pin, request.public_key, request.encrypted_private_key)
    return SuccessResponse(result=current_user)

@user_router.post(
    "/restore-private-key",
    summary="Restore Private Key with PIN",
    description="""
    **Decrypt and retrieve user's private key using PIN**
    
    This endpoint allows users to recover their encrypted private key by providing
    their PIN. The private key is needed for decrypting sheet keys and accessing
    encrypted sheet data.
    
    **Security Process:**
    1. User provides PIN
    2. Server retrieves encrypted private key
    3. PIN is used to decrypt the private key
    4. Decrypted private key returned (use immediately, don't store)
    
    **Important Security Notes:**
    - Private key should be used immediately and not stored
    - Failed attempts should be limited to prevent brute force
    - PIN is validated server-side for security
    """,
    response_description="Decrypted private key for immediate use",
    responses={
        200: {
            "description": "Private key restored successfully",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "successfully",
                        "result": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC..."
                    }
                }
            }
        },
        400: {
            "description": "Invalid PIN or no private key found"
        },
        401: {
            "description": "Authentication required"
        },
        429: {
            "description": "Too many PIN attempts"
        }
    }
)
async def restore_private_key(
    request: Restore_Private_Key_Request,
    current_user=Depends(get_current_user),
    user_service: UserService = Depends(UserService)
):
    """
    Restore user's private key using their PIN.
    
    Args:
        request: PIN for private key decryption
        current_user: Currently authenticated user
        user_service: Injected user service
        
    Returns:
        SuccessResponse containing decrypted private key
    """
    return SuccessResponse(result=user_service.restore_priave_key(current_user.user_id, request.pin))

@user_router.get(
    "/by-email",
    summary="Find User by Email Address",
    description="""
    **Search for user by email address**
    
    This endpoint is primarily used for finding users to add to sheets.
    It helps verify that a user exists in the system before attempting
    to share encrypted sheets with them.
    
    **Common Use Cases:**
    - Adding users to sheets by email
    - Verifying user existence before sharing
    - User discovery in collaboration features
    
    **Privacy Note:** Only basic profile information is returned.
    """,
    response_description="User profile information if found",
    responses={
        200: {
            "description": "User found by email",
            "content": {
                "application/json": {
                    "example": {
                        "code": 0,
                        "message": "successfully",
                        "result": {
                            "user_id": "user_456",
                            "email": "collaborator@example.com",
                            "name": "Jane Smith",
                            "picture": "https://example.com/avatar2.jpg",
                            "has_pin": True,
                            "public_key": "-----BEGIN PUBLIC KEY-----..."
                        }
                    }
                }
            }
        },
        404: {
            "description": "No user found with this email address"
        }
    }
)
async def get_user_by_email(email: str, user_service: UserService = Depends(UserService)):
    """
    Find user by email address.
    
    Args:
        email: Email address to search for
        user_service: Injected user service
        
    Returns:
        SuccessResponse containing user information if found
    """
    user = user_service.get_user_by_email(email)
    return SuccessResponse(result=user)
