from pydantic import BaseModel, validator, EmailStr
from exception.app_exception import AppException
from exception.error_code import ErrorCode
import re

class UserBioUpdateRequest(BaseModel):
    biography: str

    class Config:
        from_attributes = True
