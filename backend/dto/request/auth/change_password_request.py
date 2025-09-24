from pydantic import BaseModel, constr, validator
from exception.app_exception import AppException
from exception.error_code import ErrorCode
import re

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_new_password: str

    class Config:
        from_attributes = True
    
    @validator('new_password')
    def password_strength(cls, value):
        # Ensure password is at least 8 characters long
        if len(value) < 8:
            raise AppException(ErrorCode.PASSWORD_INVALID)

        # Check if password contains at least one uppercase letter
        if not re.search(r'[A-Z]', value):
            raise AppException(ErrorCode.PASSWORD_INVALID)

        # Check if password contains at least one lowercase letter
        if not re.search(r'[a-z]', value):
            raise AppException(ErrorCode.PASSWORD_INVALID)

        # Check if password contains at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise AppException(ErrorCode.PASSWORD_INVALID)

        return value  # Return the valid password