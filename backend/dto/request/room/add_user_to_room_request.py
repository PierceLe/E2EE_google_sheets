from pydantic import BaseModel


class AddUserToRoomRequest(BaseModel):
    room_id: str
    list_user_id: list[str] = []
    list_encrypted_group_key: list[str] = []

    class Config:
        from_attributes = True