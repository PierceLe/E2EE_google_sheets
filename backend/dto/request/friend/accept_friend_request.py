from pydantic import BaseModel


class AcceptFriendRequest(BaseModel):
    user_id: str
    is_accept: bool

    class Config:
        from_attributes = True