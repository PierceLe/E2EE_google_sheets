import datetime
from dto.request.friend.filter_friend_request import FilterFriendRequest
from dto.response.base_page_response import BasePageResponse
from dto.response.contact.contact_response import ContactResponse
from dto.response.user_response import UserResponse
from enums.enum_message import E_Message
from exception.app_exception import AppException
from exception.error_code import ErrorCode
from model.friend import Friend
from model.friend_draft import FriendDraft
from repository.friend_draft_repository import FriendDraftRepository
from repository.friend_repository import FriendRepository
from repository.user_repository import UserRepository


class FriendService():
    def __init__(self):
        self.friend_reposiotry = FriendRepository()
        self.friend_draft_repository = FriendDraftRepository()
        self.user_repository = UserRepository()

    def add_friend(self, user_id: str, friend_email: str) -> str:
        friend_user = self.user_repository.get_user_by_email(email=friend_email)
        
        if friend_user is None:
            raise AppException(ErrorCode.USER_NOT_FOUND)
        
        if self.friend_reposiotry.is_friend(user_id, friend_user.user_id):
            return E_Message.FRIEND

        friend_draft_db = self.friend_draft_repository.find_by_user_id_and_friend_id(user_id, friend_user.user_id)
        if friend_draft_db is None:
            friend_draft_db = FriendDraft()
            friend_draft_db.user_id = user_id
            friend_draft_db.friend_id = friend_user.user_id
        friend_draft_db.updated_at = datetime.datetime.utcnow()
        self.friend_draft_repository.save(friend_draft_db)

        return E_Message.SUCCESS
    
    def accept_unaccept_add_friend(self, user_id: str, friend_id: str, is_accept: bool):

        if self.friend_draft_repository.find_by_user_id_and_friend_id(user_id = user_id, friend_id= friend_id) is None \
            and self.friend_draft_repository.find_by_user_id_and_friend_id(user_id = friend_id, friend_id= user_id) is None:
            return

        if is_accept:
            friend_1 = Friend()
            friend_1.user_id = user_id
            friend_1.friend_id = friend_id

            friend_2 = Friend()
            friend_2.user_id = friend_id
            friend_2.friend_id = user_id

            self.friend_reposiotry.save_all([friend_1, friend_2])

            self.friend_draft_repository.delete_by_user_id_and_friend_id(user_id, friend_id)
            self.friend_draft_repository.delete_by_user_id_and_friend_id(friend_id, user_id)
        else:
            self.friend_draft_repository.delete_by_user_id_and_friend_id(user_id, friend_id)

    def un_friend(self, user_id: str, friend_id: str):
        self.friend_reposiotry.delete_by_2_user_id(user_id, friend_id)

    def get_user_send_request_add_friend_to_user_id(self, user_id: str) -> list[UserResponse]:
        users = self.friend_draft_repository.get_user_send_request_add_friend(user_id)
        return [UserResponse.fromUserModel(user) for user in users]
    
    def get_user_send_request_add_friend_pagging(self, user_id: str, page: int, page_size: int) -> BasePageResponse:
        result = self.friend_draft_repository.get_user_send_request_add_friend_pagging(user_id, page, page_size)
        return BasePageResponse(
            items=[UserResponse.fromUserModel(item) for item in result["items"]],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"]
        )
    
    def get_all_friends(self, user_id: str) -> list[UserResponse]:
        users = self.friend_reposiotry.get_all_friends(user_id)
        return [UserResponse.fromUserModel(user) for user in users]
    
    def get_friend_by_filter(self, request: FilterFriendRequest):
        result = self.friend_reposiotry.get_friend_pagging_and_filter(
            user_id = request.user_id,
            name= request.name,
            page= request.page,
            page_size= request.page_size,
            sorts_by= request.sorts_by,
            sorts_dir= request.sorts_dir
        )
        return BasePageResponse(
            items=[UserResponse.fromUserModel(item) for item in result["items"]],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"]
        )

    def get_user_received_request_add_friend_from_user_id(self, user_id: str) -> list[UserResponse]:
        users = self.friend_draft_repository.get_user_received_request_add_friend_from_user_id(user_id)
        return [UserResponse.fromUserModel(user) for user in users]

    def get_all_contact(self, user_id: str):
        friend = self.get_all_friends(user_id)
        received_friend = self.get_user_send_request_add_friend_to_user_id(user_id)
        send_friend = self.get_user_received_request_add_friend_from_user_id(user_id)
        return ContactResponse(
            friend=friend,
            received_friend=received_friend,
            send_friend=send_friend
        )

    def is_friend(self, current_user_id: str, friend_id: str) -> bool:
        friends = self.get_all_friends(current_user_id)
        return any(friend.user_id == friend_id for friend in friends)
        