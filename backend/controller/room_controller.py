from fastapi import APIRouter, HTTPException, status, Depends

from dto.request.room.add_user_to_room_request import AddUserToRoomRequest
from dto.request.room.filter_room_one_request import FilterRoomOneRequest
from dto.request.room.filter_room_request import FilterRoomRequest
from dto.request.room.remove_user_from_room_request import RemoveUserFromRoom
from dto.request.room.update_room_request import UpdateRoomRequest
from dto.response.success_response import SuccessResponse
from model.user import User
from utils.utils import get_current_user
from dto.request.room.create_room_request import CreateRoomRequest
from service.room_service import RoomService

room_router = APIRouter()

@room_router.post("")
async def creat_room(create_room_request: CreateRoomRequest, room_service: RoomService = Depends(RoomService), current_user :User = Depends(get_current_user)):
    result = room_service.create_room(
        room_name= create_room_request.room_name,
        creator_id= current_user.user_id,
        room_type= create_room_request.room_type,
        avatar_url= create_room_request.avatar_url,
        description= create_room_request.description,
        member_ids= create_room_request.member_ids,
        encrypted_group_keys = create_room_request.encrypted_group_keys,
        encrypted_group_key = create_room_request.encrypted_group_key
        )
    return SuccessResponse(result=result)

@room_router.get("")
async def get_room_by_id(room_id: str, room_service: RoomService = Depends(RoomService)):
    result = room_service.get_room_by_room_id(room_id)
    return SuccessResponse(result = result)

@room_router.put("")
async def update_room_by_id(
    room_id: str,
    update_room_request: UpdateRoomRequest,
    room_service: RoomService = Depends(RoomService),
    ):
    result = room_service.update_room(update_room_request, room_id)
    return SuccessResponse(result = result)

@room_router.put("/meta")
async def update_room_meta(
    room_id: str,
    update_room_request: UpdateRoomRequest,
    room_service: RoomService = Depends(RoomService),
    current_user: User = Depends(get_current_user)
    ):
    result = room_service.update_room_meta(room_id, update_room_request, current_user.user_id)
    return SuccessResponse(result = result)

@room_router.post("/filter")
async def get_room_filter(request: FilterRoomRequest,
    room_service: RoomService = Depends(RoomService),
    current_user: User = Depends(get_current_user)
    ):
    request.user_id = current_user.user_id
    result = room_service.get_room_by_filter(request)
    return SuccessResponse(result = result)

@room_router.post("/add")
async def addUserToRoom(request: AddUserToRoomRequest,
    room_service: RoomService = Depends(RoomService),
    current_user: User = Depends(get_current_user)
    ):
    room_service.add_user_to_room(current_user.user_id, request.list_user_id, request.room_id, request.list_encrypted_group_key)
    return SuccessResponse()

@room_router.post("/remove")
async def removeUserFromRoom(request: RemoveUserFromRoom,
    room_service: RoomService = Depends(RoomService),
    current_user: User = Depends(get_current_user)
    ):
    room_service.remove_user_from_room(current_user.user_id, request.list_user_id, request.room_id)
    return SuccessResponse()

@room_router.post("/leave")
async def leaveFromRoom(room_id: str,
    room_service: RoomService = Depends(RoomService),
    current_user: User = Depends(get_current_user)
    ):
    room_service.leave_room(current_user.user_id, room_id)
    return SuccessResponse()

@room_router.get("/user")
async def getUserFromRoom(room_id: str,
    room_service: RoomService = Depends(RoomService),
    ):
    result = room_service.get_user_in_room(room_id)
    return SuccessResponse(result = result)

@room_router.delete("")
async def deleteRoom(room_id: str,
                     room_service: RoomService = Depends(RoomService),
                     current_user: User = Depends(get_current_user)
                     ):
    result = room_service.delete_room(current_user.user_id, room_id)
    return SuccessResponse(result = result)

@room_router.post("/one/filter")
async def get_room_chat_one_filter(request: FilterRoomOneRequest,
    room_service: RoomService = Depends(RoomService),
    current_user: User = Depends(get_current_user)
    ):
    request.user_id = current_user.user_id
    result = room_service.get_room_chat_one_filter(request)
    return SuccessResponse(result = result)

@room_router.get("/group-key")
async def get_encrypted_group_key(room_id: str,
    room_service: RoomService = Depends(RoomService),
    current_user: User = Depends(get_current_user)
    ):
    result = room_service.get_encrypted_group_key_by_room_id(current_user.user_id, room_id)
    return SuccessResponse(result = result)


@room_router.get("/find-room-with-user")
async def get_room(user_id: str,
                   room_service: RoomService = Depends(RoomService),
                   current_user: User = Depends(get_current_user),

                   ):
    result = room_service.get_room_with_friend_id(current_user.user_id, user_id)
    return SuccessResponse(result = result)