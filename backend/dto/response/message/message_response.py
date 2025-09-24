from datetime import datetime
from pydantic import BaseModel

from dto.response.user_response import UserResponse
from enums.enum_message_type import E_Message_Type


class MessageResponse(BaseModel):
    id: str
    room_id: str
    message_type: E_Message_Type
    content: str | None
    file_url: str | None
    created_at: datetime
    updated_at: datetime
    sender: UserResponse
