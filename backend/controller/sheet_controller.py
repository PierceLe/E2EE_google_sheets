from fastapi import APIRouter, HTTPException, status, Depends

from dto.request.sheet.create_sheet_request import CreateSheetRequest
from dto.request.sheet.filter_sheet_request import FilterSheetRequest
from dto.request.sheet.add_user_to_sheet_request import AddUserToSheetRequest
from dto.request.sheet.remove_user_from_sheet_request import RemoveUserFromSheetRequest
from dto.request.sheet.update_sheet_access_request import UpdateSheetAccessRequest
from dto.response.success_response import SuccessResponse
from model.user import User
from utils.utils import get_current_user
from service.sheet_service import SheetService

sheet_router = APIRouter()

@sheet_router.post("")
async def create_sheet(
    create_sheet_request: CreateSheetRequest, 
    sheet_service: SheetService = Depends(SheetService), 
    current_user: User = Depends(get_current_user)
):
    """Create a new sheet"""
    result = sheet_service.create_sheet(
        link=create_sheet_request.link,
        creator_id=current_user.user_id,
        member_ids=create_sheet_request.member_ids,
        encrypted_sheet_keys=create_sheet_request.encrypted_sheet_keys,
        encrypted_sheet_key=create_sheet_request.encrypted_sheet_key
    )
    return SuccessResponse(result=result)

@sheet_router.get("")
async def get_sheet_by_id(
    sheet_id: str, 
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """Get sheet details by ID"""
    result = sheet_service.get_sheet_by_id(sheet_id, current_user.user_id)
    return SuccessResponse(result=result)

@sheet_router.post("/filter")
async def get_sheets_filter(
    request: FilterSheetRequest,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """Get filtered list of sheets for current user"""
    request.user_id = current_user.user_id
    result = sheet_service.get_sheets_by_filter(request)
    return SuccessResponse(result=result)

@sheet_router.post("/add-users")
async def add_users_to_sheet(
    sheet_id: str,
    request: AddUserToSheetRequest,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """Add users to a sheet"""
    result = sheet_service.add_users_to_sheet(current_user.user_id, sheet_id, request)
    return SuccessResponse(result=result)

@sheet_router.post("/remove-users")
async def remove_users_from_sheet(
    sheet_id: str,
    request: RemoveUserFromSheetRequest,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """Remove users from a sheet"""
    result = sheet_service.remove_users_from_sheet(current_user.user_id, sheet_id, request)
    return SuccessResponse(result=result)

@sheet_router.post("/leave")
async def leave_sheet(
    sheet_id: str,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """Leave a sheet"""
    result = sheet_service.leave_sheet(current_user.user_id, sheet_id)
    return SuccessResponse(result=result)

@sheet_router.delete("")
async def delete_sheet(
    sheet_id: str,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """Delete a sheet (owner only)"""
    result = sheet_service.delete_sheet(current_user.user_id, sheet_id)
    return SuccessResponse(result=result)

@sheet_router.put("/access")
async def update_sheet_access(
    sheet_id: str,
    target_user_id: str,
    request: UpdateSheetAccessRequest,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """Update user's access to a sheet (role, favorite, encrypted key)"""
    result = sheet_service.update_user_sheet_access(
        current_user.user_id, 
        target_user_id, 
        sheet_id, 
        request
    )
    return SuccessResponse(result=result)

@sheet_router.put("/favorite")
async def toggle_favorite(
    sheet_id: str,
    is_favorite: bool,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """Toggle favorite status for a sheet"""
    request = UpdateSheetAccessRequest(is_favorite=is_favorite)
    result = sheet_service.update_user_sheet_access(
        current_user.user_id, 
        current_user.user_id, 
        sheet_id, 
        request
    )
    return SuccessResponse(result=result)

@sheet_router.get("/users")
async def get_users_in_sheet(
    sheet_id: str,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """Get all users who have access to a sheet"""
    result = sheet_service.get_users_in_sheet(current_user.user_id, sheet_id)
    return SuccessResponse(result=result)

@sheet_router.get("/sheet-key")
async def get_encrypted_sheet_key(
    sheet_id: str,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """Get user's encrypted sheet key"""
    result = sheet_service.get_encrypted_sheet_key(current_user.user_id, sheet_id)
    return SuccessResponse(result=result)

@sheet_router.get("/role")
async def get_user_role(
    sheet_id: str,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """Get user's role in a sheet"""
    result = sheet_service.get_user_role_in_sheet(current_user.user_id, sheet_id)
    return SuccessResponse(result=result)

@sheet_router.get("/permission")
async def check_permission(
    sheet_id: str,
    required_role: str = "viewer",
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """Check if user has required permission level"""
    result = sheet_service.check_user_permission(current_user.user_id, sheet_id, required_role)
    return SuccessResponse(result=result)

@sheet_router.put("/access-time")
async def update_last_accessed(
    sheet_id: str,
    sheet_service: SheetService = Depends(SheetService),
    current_user: User = Depends(get_current_user)
):
    """Update user's last accessed time for a sheet"""
    result = sheet_service.update_last_accessed(current_user.user_id, sheet_id)
    return SuccessResponse(result=result)
