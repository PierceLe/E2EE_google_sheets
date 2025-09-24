from fastapi import APIRouter, HTTPException, status, Depends

from dto.request.base_page_request import BasePageRequest
from dto.request.friend.accept_friend_request import AcceptFriendRequest
from dto.request.friend.add_friend_request import AddFriendRequest
from dto.request.friend.filter_friend_request import FilterFriendRequest
from dto.request.friend.unfriend_request import UnfriendRequest
from dto.response.success_response import SuccessResponse
from enums.enum_message import E_Message
from model.user import User
from service.friend_service import FriendService
from utils.utils import get_current_user
from service.room_service import RoomService

friend_router = APIRouter()


@friend_router.post("/add-friend")
async def add_friend(request: AddFriendRequest, 
                    friend_service: FriendService = Depends(FriendService), 
                    current_user :User = Depends(get_current_user)):
    if current_user.email != request.friend_email:
        result = friend_service.add_friend(current_user.user_id, request.friend_email)
    else:
        result = E_Message.UNSECCESS
    return SuccessResponse(result=result)


@friend_router.post("/accept-friend")
async def accept_friend(request: AcceptFriendRequest,
                    friend_service: FriendService = Depends(FriendService), 
                    current_user :User = Depends(get_current_user)):
    result = friend_service.accept_unaccept_add_friend(user_id=request.user_id, friend_id= current_user.user_id, is_accept=request.is_accept)
    return SuccessResponse(result=result)


@friend_router.post("/unfriend")
async def unfriend(request: UnfriendRequest,
                friend_service: FriendService = Depends(FriendService), 
                current_user :User = Depends(get_current_user)):
    result = friend_service.un_friend(current_user.user_id, request.friend_id)
    return SuccessResponse(result=result)


@friend_router.get("/friend-draft")
async def get_user_send_request_add_friend(friend_service: FriendService = Depends(FriendService), 
                                            current_user :User = Depends(get_current_user)):
    result = friend_service.get_user_send_request_add_friend_to_user_id(current_user.user_id)
    return SuccessResponse(result=result)

@friend_router.post("/friend-draft/pagging")
async def get_user_send_request_add_friend_pagging(request: BasePageRequest,
                                                friend_service: FriendService = Depends(FriendService), 
                                                current_user :User = Depends(get_current_user)):
    result = friend_service.get_user_send_request_add_friend_pagging(current_user.user_id, request.page, request.page_size)
    return SuccessResponse(result=result)

@friend_router.get("/all")
async def get_all_friends(friend_service: FriendService = Depends(FriendService), 
                        current_user :User = Depends(get_current_user)):
    result = friend_service.get_all_friends(current_user.user_id)
    return SuccessResponse(result=result)

@friend_router.post("/filter")
async def get_friend_by_filter(request: FilterFriendRequest,
                            friend_service: FriendService = Depends(FriendService), 
                            current_user :User = Depends(get_current_user)):
    request.user_id = current_user.user_id
    result = friend_service.get_friend_by_filter(request)
    return SuccessResponse(result=result)

@friend_router.get("/all-contact")
async def get_all_contact(friend_service: FriendService = Depends(FriendService), 
                        current_user :User = Depends(get_current_user)):
    result = friend_service.get_all_contact(current_user.user_id)
    return SuccessResponse(result=result)