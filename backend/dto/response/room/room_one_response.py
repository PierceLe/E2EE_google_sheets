from pydantic import BaseModel
from datetime import datetime
from dto.response.room.room_response import RoomResponse
from enums.enum_room_type import E_Room_Type
from typing import Optional

class RoomChatOneResponse(RoomResponse):
    friend_id: str
    friend_email: str
    friend_frist_name: str
    friend_last_name: str
    friend_avatar_url: str
    class Config:
        from_attributes = True