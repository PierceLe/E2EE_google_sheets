from pydantic import BaseModel, validator, EmailStr
from exception.app_exception import AppException
from exception.error_code import ErrorCode
import re

class UserCreateRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    avatar_url: str

    @validator('password')
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

    @validator('email')
    def validate_email(cls, value):
        # Check if the email format is valid
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', value):
            raise AppException(ErrorCode.EMAIL_INVALID)
        
        return value  

    class Config:
        from_attributes = True
