from pydantic import BaseModel
from model.user import User

class UserResponse(BaseModel):
    user_id: str

    email: str
    # password: str 
    first_name: str
    last_name: str
    avatar_url: str

    @classmethod
    def fromUserModel(cls, user_model: User):
        return cls(user_id = user_model.user_id, 
                   email = user_model.email,
                   first_name = user_model.first_name,
                   last_name = user_model.last_name,
                   avatar_url = user_model.avatar_url,
                   )

    class Config:
        from_attributes = True