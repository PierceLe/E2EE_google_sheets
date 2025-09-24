from repository.user_repository import UserRepository
from repository.room_repository import RoomRepository
from repository.user_room_repository import UserRoomRepository
from dto.request.auth.user_create_request import UserCreateRequest
from dto.response.user_response import UserResponse
from dto.response.user_full_response import UserFullResponse
from fastapi import Depends
from exception.app_exception import AppException
from exception.error_code import ErrorCode
from passlib.context import CryptContext
from typing import Union

class UserRoomService():
    def __init__(self):
        self.user_repository = UserRepository()
        self.room_repository = RoomRepository()
        self.user_room_repository = UserRoomRepository()

    def get_all_room_of_user(self, user_id: str):
        return self.user_room_repository.get_room_of_user(user_id)

    

