from pydantic import BaseModel
from enums.enum_login_method import E_Login_Method
from model.user import User

class UserResponse(BaseModel):
    user_id: str

    email: str
    # password: str 
    first_name: str
    last_name: str
    avatar_url: str
    is_verified: bool
    method: E_Login_Method
    public_key: str | None
    biography: str | None

    @classmethod
    def fromUserModel(cls, user_model: User):
        return cls(user_id = user_model.user_id, 
                   email = user_model.email,
                   first_name = user_model.first_name,
                   last_name = user_model.last_name,
                   avatar_url = user_model.avatar_url,
                   is_verified = user_model.is_verified,
                   method = user_model.method,
                   public_key = user_model.public_key,
                   biography = user_model.biography
                   )

    class Config:
        from_attributes = True