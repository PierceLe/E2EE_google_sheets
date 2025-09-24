from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from enums.enum_room_type import E_Room_Type

class CreateRoomRequest(BaseModel):
    room_name: str
    room_type: E_Room_Type
    avatar_url: Optional[str] = None
    description: Optional[str] = None
    member_ids: list[str] = []
    encrypted_group_keys: list[str] = []
    encrypted_group_key: str

    class Config:
        from_attributes = True