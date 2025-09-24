from repository.user_repository import UserRepository
from dto.response.user_response import UserResponse
from dto.response.user_full_response import UserFullResponse
from exception.app_exception import AppException
from exception.error_code import ErrorCode
from passlib.context import CryptContext
from typing import Union

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService():
    def __init__(self):
        self.user_repository = UserRepository()

    def check_user_exist_by_email(self, email: str, only_verified=True):
        return self.user_repository.check_user_exist_by_email(
            email=email)

    
    def create_user_google(self, email, first_name, last_name, avatar_url) -> UserResponse:
        user = self.user_repository.create_user_google(
            email=email,
            first_name=first_name,
            last_name=last_name,
            avatar_url=avatar_url)

        return UserResponse(
            user_id=user.user_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            avatar_url=user.avatar_url,
            public_key=user.public_key
        )

    def get_user(self, user_id: str) -> UserFullResponse:
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            return None
        return UserFullResponse.fromUserModel(user)


    def get_user_by_email(
            self,
            email: str) -> UserFullResponse:
        user = self.user_repository.get_user_by_email(
            email=email)
        if not user:
            return None
        return UserFullResponse.fromUserModel(user)

    def create_pin(self, user_id: str, pin: str, public_key: str, encrypted_private_key: str):
        pin_hashed = pwd_context.hash(pin)
        return self.user_repository.create_pin(user_id, pin_hashed, public_key, encrypted_private_key)
    
    def restore_priave_key(self, user_id: str, pin: str):
        user_db = self.user_repository.get_user_by_id(user_id)
        if user_db.pin is not None and pwd_context.verify(pin, user_db.pin):
            return {
                "public_key": user_db.public_key,
                "encrypted_private_key": user_db.encrypted_private_key
            }
        else:
            raise AppException(ErrorCode.PIN_INVALID)