from pydantic import BaseModel


class UnfriendRequest(BaseModel):
    friend_id: str

    class Config:
        from_attributes = True