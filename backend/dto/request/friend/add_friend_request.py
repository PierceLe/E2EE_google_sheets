from pydantic import BaseModel


class AddFriendRequest(BaseModel):
    friend_email: str

    class Config:
        from_attributes = True