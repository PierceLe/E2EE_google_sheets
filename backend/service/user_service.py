from repository.user_repository import UserRepository
from dto.request.auth.user_create_request import UserCreateRequest
from dto.request.auth.user_update_request import UserUpdateRequest
from dto.request.auth.user_bio_update_request import UserBioUpdateRequest
from dto.response.user_response import UserResponse
from dto.response.user_full_response import UserFullResponse
from fastapi import Depends
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
            email=email, only_verified=only_verified)

    def create_user(self, user_request: UserCreateRequest) -> UserResponse:
        # Encrypt password
        user_request.password = pwd_context.hash(user_request.password)

        user = self.user_repository.create_user(
            email=user_request.email,
            password=user_request.password,
            first_name=user_request.first_name,
            last_name=user_request.last_name,
            avatar_url=user_request.avatar_url,
            use_2fa_login=False,
            two_factor_secret="")

        return UserResponse(
            user_id=user.user_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            avatar_url=user.avatar_url,
            is_verified=user.is_verified,
            method=user.method,
            public_key=user.public_key,
            biography=user.biography
        )
    
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
            is_verified=user.is_verified,
            method=user.method,
            public_key=user.public_key,
            biography=user.biography
        )

    def get_user(self, user_id: str, get_full_info: bool = False) -> Union[UserResponse, UserFullResponse]:
        user = self.user_repository.get_user_by_id(user_id)

        if not user:
            return None
        
        if get_full_info:
            return UserFullResponse.fromUserModel(user)
        else:
            return UserResponse.fromUserModel(user)

    def get_user_by_email(
            self,
            email: str,
            only_verified: bool = True,
            get_full_info: bool = False,
            get_use_2fa_login: bool = False) -> Union[UserResponse, UserFullResponse]:

        user = self.user_repository.get_user_by_email(
            email=email, only_verified=only_verified)

        if not user:
            return None

        if get_full_info:
            return UserFullResponse.fromUserModel(user)
        else:
            if get_use_2fa_login :
                return UserFullResponse.fromUserModel(user)
            return UserResponse.fromUserModel(user)

    def get_password(self, user_id: str):
        user = self.user_repository.get_user_by_id(user_id)

        return user.password

    def delete_user_by_email(self, email: str):
        return self.user_repository.delete_user_by_email(email)

    def update_user_verified_by_email(self, email: str, is_verified=True):
        return self.user_repository.update_user_verified_by_email(
            email, is_verified=is_verified)

    def update_password(self, user_id: str, new_password: str):
        # Encrypt password
        new_password_hased = pwd_context.hash(new_password)

        return self.user_repository.update_password(
            user_id, new_password_hased)
    
    def update_two_factor_secret(self, user_id: str, two_factor_secret: str):
        return self.user_repository.update_two_factor_secret(
            user_id, two_factor_secret)
    
    def update_user_info(self, user_id: str, user_update: UserUpdateRequest):
        return self.user_repository.update_user_info(
            user_id, user_update)

    def update_user_bio(self, user_id: str, user_update: UserBioUpdateRequest):
        return self.user_repository.update_user_bio(
            user_id, user_update)
    
    def disable_2fa(self, user_id: str):
        return self.user_repository.disable_2fa(user_id)
    
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

    def get_user_query_email_and_not_in_list(
            self,
            user_id: str,
            email: str
            ) -> list[UserResponse]:
        friend = self.friend_repository.get_all_friends(user_id)
        received_friend = self.friend_draft_repository.get_user_send_request_add_friend(user_id)
        send_friend = self.friend_draft_repository.get_user_received_request_add_friend_from_user_id(user_id)

        list_user_id_non_query = [friend_user.user_id for friend_user in friend]
        for user in received_friend:
            list_user_id_non_query.append(user.user_id)
        for user in send_friend:
            list_user_id_non_query.append(user.user_id)

        list_user_id_non_query.append(user_id)
        users = self.user_repository.query_by_email_not_in_list(list_user_id_non_query, email)
        return [UserResponse.fromUserModel(user) for user in users]