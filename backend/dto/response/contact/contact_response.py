

from pydantic import BaseModel
from dto.response.user_response import UserResponse


class ContactResponse(BaseModel):
    friend: list[UserResponse] = []
    send_friend: list[UserResponse] = []
    received_friend: list[UserResponse] = []

    class Config:
        from_attributes = True