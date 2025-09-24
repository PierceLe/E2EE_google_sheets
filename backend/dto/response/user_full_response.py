from pydantic import BaseModel
from enums.enum_login_method import E_Login_Method
from model.user import User

# Get Full Info of user (include use_2fa_login and two_factor_secret)
class UserFullResponse(BaseModel):
    user_id: str

    email: str
    # password: str 
    first_name: str
    last_name: str
    avatar_url: str
    is_verified: bool
    use_2fa_login: bool
    two_factor_secret: str | None
    method: E_Login_Method
    salt: str | None
    pin: str | None
    public_key: str | None
    encrypted_private_key: str | None
    biography: str | None

    @classmethod
    def fromUserModel(cls, user_model: User):
        return cls(user_id = user_model.user_id, 
                   email = user_model.email,
                   first_name = user_model.first_name,
                   last_name = user_model.last_name,
                   avatar_url = user_model.avatar_url,
                   is_verified = user_model.is_verified,
                   use_2fa_login = user_model.use_2fa_login,
                   two_factor_secret = user_model.two_factor_secret,
                   method = user_model.method,
                   salt = user_model.salt,
                   pin = "1" if user_model.pin is not None else None,
                   public_key = user_model.public_key,
                   encrypted_private_key = user_model.encrypted_private_key,
                   biography = user_model.biography
                   )

    class Config:
        from_attributes = True