from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from enums.enum_room_type import E_Room_Type

class UpdateRoomRequest(BaseModel):
    room_name: Optional[str] = None
    last_mess: Optional[str] = None
    avatar_url: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True