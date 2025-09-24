from fastapi import APIRouter, HTTPException, status, Depends
from dto.request.auth.create_pin_request import Create_Pin_Request
from dto.request.auth.restore_private_key_request import Restore_Private_Key_Request
from dto.response.user_response import UserResponse
from dto.request.auth.user_create_request import UserCreateRequest
from service.user_service import UserService
from exception.app_exception import AppException
from exception.error_code import ErrorCode
from dto.response.success_response import SuccessResponse
from utils.utils import get_current_user
from dto.request.auth.user_update_request import UserUpdateRequest
from dto.request.auth.user_bio_update_request import UserBioUpdateRequest

user_router = APIRouter()

@user_router.get("/by-id")
async def get_user(user_id: str, user_service: UserService = Depends(UserService)):
    
    user = user_service.get_user(user_id)

    return SuccessResponse(result=user)

@user_router.post("/me")
async def get_me(current_user=Depends(get_current_user), user_service: UserService = Depends(UserService)):
    current_user = user_service.get_user_by_email(current_user.email, get_use_2fa_login=True)
    return SuccessResponse(result=current_user)

@user_router.put("/update-me")
async def update_me(user_update: UserUpdateRequest,
                current_user=Depends(get_current_user),
                user_service: UserService = Depends(UserService)):

    current_user = user_service.get_user_by_email(current_user.email, get_use_2fa_login=True)
    updated = user_service.update_user_info(user_id=current_user.user_id, user_update=user_update)

    return SuccessResponse(result=updated)

@user_router.put("/update-me-bio")
async def update_me_bio(user_update: UserBioUpdateRequest,
                current_user=Depends(get_current_user),
                user_service: UserService = Depends(UserService)):

    current_user = user_service.get_user_by_email(current_user.email, get_use_2fa_login=True)
    updated = user_service.update_user_bio(user_id=current_user.user_id, user_update=user_update)

    return SuccessResponse(result=updated)

@user_router.post("/set-pin")
async def set_pin_and_key(request: Create_Pin_Request,
                current_user=Depends(get_current_user),
                user_service: UserService = Depends(UserService)):
    user_service.create_pin(current_user.user_id, request.pin, request.public_key, request.encrypted_private_key)
    return SuccessResponse(result=current_user)

@user_router.post("/restore-private-key")
async def restore_private_key(request: Restore_Private_Key_Request,
                current_user=Depends(get_current_user),
                user_service: UserService = Depends(UserService)):
    return SuccessResponse(result = user_service.restore_priave_key(current_user.user_id, request.pin))

@user_router.get("/by-email")
async def get_user_by_email(email: str, user_service: UserService = Depends(UserService)):
    user = user_service.get_user_by_email(email)
    return SuccessResponse(result=user)

@user_router.get("/query-email")
async def get_user_by_email(email: str, current_user=Depends(get_current_user), user_service: UserService = Depends(UserService)):
    users = user_service.get_user_query_email_and_not_in_list(current_user.user_id, email)
    return SuccessResponse(result=users)