from pydantic import BaseModel, validator, EmailStr
from exception.app_exception import AppException
from exception.error_code import ErrorCode
import re

class UserUpdateRequest(BaseModel):
    first_name: str
    last_name: str
    avatar_url: str

    class Config:
        from_attributes = True
