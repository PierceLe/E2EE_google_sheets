from pydantic import BaseModel
from model.user import User

# Get Full Info of user (include use_2fa_login and two_factor_secret)
class UserFullResponse(BaseModel):
    user_id: str

    email: str
    # password: str 
    first_name: str
    last_name: str
    avatar_url: str
    public_key: str | None
    encrypted_private_key: str | None

    @classmethod
    def fromUserModel(cls, user_model: User):
        return cls(user_id = user_model.user_id, 
                   email = user_model.email,
                   first_name = user_model.first_name,
                   last_name = user_model.last_name,
                   avatar_url = user_model.avatar_url,
                   public_key = user_model.public_key,
                   encrypted_private_key = user_model.encrypted_private_key
                   )

    class Config:
        from_attributes = True