from fastapi import APIRouter, HTTPException, status, Depends, Response, Request, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from dto.response.success_response import SuccessResponse
from dto.response.login_response import LoginResponse
from dto.request.auth.check_2fa_request import Check2FARequest
from dto.request.auth.user_create_request import UserCreateRequest
from dto.request.auth.reset_password_request import ResetPasswordRequest
from dto.request.auth.login_request import LoginRequest
from dto.request.auth.change_password_request import ChangePasswordRequest
from dto.request.auth.google_login_request import GoogleLoginRequest
from service.auth_service import AuthService
from exception.app_exception import AppException
from exception.error_code import ErrorCode
from utils.utils import get_current_user
from model.user import User
from enums.login import E_Login
from fastapi.responses import JSONResponse

auth_router = APIRouter()


@auth_router.post("/signup")
async def signup(response: Response, user_create: UserCreateRequest,
                 auth_service: AuthService = Depends(AuthService)):

    # Save user
    new_user = auth_service.signup(user_create)

    response.delete_cookie("access_token")

    return {
        "code": 0,
        "message": "Signup is Pending. Please check your email to verify your account."}


@auth_router.get("/verify-email-signup",
                 summary="Send verification link via email for first registration")
async def verify_email_signup(
        response: Response,
        token: str = Query(..., description="The token for email verification"),
        auth_service: AuthService = Depends(AuthService)):
    response.delete_cookie("access_token")
    # check that the email is correct or not
    user = auth_service.check_email_verification_token(token)
    if user:
        # Update is_verified of User to True
        auth_service.update_user_verified(user.email, is_verified=True)

        # Return Email Verified Successfully
        return SuccessResponse()

    else:

        raise HTTPException(
            status_code=400,
            detail="Invalid or expired token.")


@auth_router.post("/change-password",
                  summary="Change password in case you are logged in and remember the old password")
async def change_password(
        change_password_data: ChangePasswordRequest,
        auth_service: AuthService = Depends(AuthService),
        current_user: User = Depends(get_current_user)):

    # Check email and password
    user = auth_service.authenticate_user(
        email=current_user.email,
        password=change_password_data.old_password)
    if not user:
        raise AppException(ErrorCode.PASSWORD_INCORRECT)

    # If new_password and confirm_new_password are different
    if change_password_data.new_password != change_password_data.confirm_new_password:
        raise AppException(ErrorCode.CONFIRM_PASSWORD_DIFFER_NEW_PASSWORD)

    # Call function save New Password
    return auth_service.update_password(
        user.user_id, change_password_data.new_password)


@auth_router.post("/forgot-password",
                  summary="Confirm reset password by email in case you forgot the password")
async def forgot_password(
        email: str,
        auth_service: AuthService = Depends(AuthService)):
    user = auth_service.forgot_password(email=email)

    return {
        "code": 0,
        "message": "Please check your email to confirm reset password"}


@auth_router.post("/reset-password",
                  summary="Reset to new password after confirming via email")
async def reset_password(
        response: Response,
        reset_password_data: ResetPasswordRequest,
        auth_service: AuthService = Depends(AuthService)):
    
    response.delete_cookie("access_token")

    # Check whether or not token is validate
    user = auth_service.check_email_verification_token(
        token=reset_password_data.token)
    if not user:
        raise AppException(ErrorCode.UNCATEGORIZED_EXCEPTION)

    # If new_password and confirm_new_password are different
    if reset_password_data.new_password != reset_password_data.confirm_new_password:
        raise AppException(ErrorCode.CONFIRM_PASSWORD_DIFFER_NEW_PASSWORD)

    # Call function save New Password
    return auth_service.update_password(
        user.user_id, reset_password_data.new_password)


@auth_router.post("/login")
async def login(response: Response, login_data: LoginRequest,
                auth_service: AuthService = Depends(AuthService)):

    # Check email and password
    user = auth_service.authenticate_user(
        email=login_data.email,
        password=login_data.password,
        get_full_info=True)

    if not user:
        raise AppException(ErrorCode.ACCOUNT_INCORRECT)    
    
    response.delete_cookie("access_token")

    # If the user does not use 2fa, allow the user to access the system immediately
    if not user.use_2fa_login:
        access_token = auth_service.create_token(data={"sub": user.email})

        # Set cookie
        response.set_cookie(
            key="access_token",
            value=f"{access_token}",
            httponly=True,
            secure=True,
            samesite='Lax')
        return LoginResponse(login_type=E_Login.NOT_USE_2FA, token=access_token)

    else: # If use 2fa then return a token to check 2fa code
        
        check_2fa_token = auth_service.create_2fa_verification_token(data={"sub": user.email})

        return LoginResponse(login_type=E_Login.USE_2FA, token=check_2fa_token)

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

@auth_router.post("/check-2fa")
async def check_2fa(response: Response, check_2fa_data: Check2FARequest,
                auth_service: AuthService = Depends(AuthService)):

    # Check whether or not token is validate
    user = auth_service.check_2fa_verification_token(token=check_2fa_data.token, code=check_2fa_data.code)
    if not user:
        raise AppException(ErrorCode.UNCATEGORIZED_EXCEPTION)
    
    access_token = auth_service.create_token(data={"sub": user.email})

    # Set cookie
    response.set_cookie(
        key="access_token",
        value=f"{access_token}",
        httponly=True,
        secure=True,
        samesite='none')
    return {
        "code": 0,
        "message": "Check 2FA done. Login successfully !"}

@auth_router.post("/logout")
async def logout(response: Response):
    # remove cookie when user logout
    response.delete_cookie("access_token", secure=True, samesite='none')
    return {"message": "Logout successful"}


@auth_router.post("/enable-2fa", summary="Enable to use 2fa for login")
async def enable_2fa(
    auth_service: AuthService = Depends(AuthService),
    current_user: User = Depends(get_current_user)
):
    try:
        qr_base64 = auth_service.enable_2fa(user_id=current_user.user_id)
        return JSONResponse(content={"qr_code": qr_base64})
    except:
        try:
            auth_service.disable_2fa(current_user.user_id)
            raise AppException(ErrorCode.SIGUP_USING_2FA_FAILED)
        except Exception as e:
            raise AppException(ErrorCode.UNCATEGORIZED_EXCEPTION)


