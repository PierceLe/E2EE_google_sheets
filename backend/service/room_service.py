from dto.request.room.filter_room_one_request import FilterRoomOneRequest
from dto.request.room.filter_room_request import FilterRoomRequest
from dto.request.room.update_room_request import UpdateRoomRequest
from dto.response.base_page_response import BasePageResponse
from dto.response.room.room_one_response import RoomChatOneResponse
from dto.response.user_response import UserResponse
from enums.enum_login_method import E_Login_Method
from enums.enum_message import E_Message
from model.room import Room
from model.user_room import UserRoom
from repository.room_repository import RoomRepository
from dto.response.room.room_response import RoomResponse
from enums.enum_room_type import E_Room_Type
from exception.app_exception import AppException
from exception.error_code import ErrorCode
from repository.user_room_repository import UserRoomRepository


class RoomService():
    def __init__(self):
        self.room_repository = RoomRepository()
        self.user_room_repository = UserRoomRepository()

    def create_room(self,
                    room_name: str,
                    creator_id: str,
                    room_type: E_Room_Type,
                    avatar_url: str,
                    description: str,
                    member_ids: list[str],
                    encrypted_group_keys: list[str],
                    encrypted_group_key: str
                    ) -> RoomResponse:
        room_id = None
        if room_type == E_Room_Type.ONE:
            room_id = self.create_room_one(
                room_name,
                creator_id,
                room_type,
                avatar_url,
                description,
                member_ids,
                encrypted_group_keys,
                encrypted_group_key
            )
        else:
            room_id = self.create_room_many(
                room_name,
                creator_id,
                room_type,
                avatar_url,
                description,
                member_ids,
                encrypted_group_keys,
                encrypted_group_key
            )

        return room_id

    def get_room_by_room_id(self, room_id: str) -> RoomResponse:
        room = self.room_repository.get_room_by_room_id(room_id)
        if not room:
            raise AppException(ErrorCode.SHEET_NOT_FOUND)
        return RoomResponse(
            room_id=room.room_id,
            room_name=room.room_name,
            creator_id=room.creator_id,
            last_mess=room.last_mess,
            room_type=room.room_type,
            avatar_url=room.avatar_url,
            description=room.description,
            created_at=room.created_at,
            updated_at=room.updated_at
        )

    def update_room(self, request: UpdateRoomRequest, room_id: str) -> RoomResponse:
        room: Room = self.room_repository.get_room_by_room_id(room_id)
        if not room:
            raise AppException(ErrorCode.SHEET_NOT_FOUND)
        if request.room_name is not None:
            room.room_name = request.room_name
        if request.last_mess is not None:
            room.last_mess = request.last_mess
        if request.avatar_url is not None:
            room.avatar_url = request.avatar_url
        if request.description is not None:
            room.description = request.description
        room = self.room_repository.save(room=room)
        return RoomResponse(
            room_id=room.room_id,
            room_name=room.room_name,
            creator_id=room.creator_id,
            last_mess=room.last_mess,
            room_type=room.room_type,
            avatar_url=room.avatar_url,
            description=room.description,
            created_at=room.created_at,
            updated_at=room.updated_at
        )

    def update_room_meta(self, room_id: str, update_room_request: UpdateRoomRequest, user_id: str):
        room = self.room_repository.get_room_by_room_id(room_id)
        if not room:
            raise AppException(ErrorCode.SHEET_NOT_FOUND)
        if room.creator_id != user_id:
            raise AppException(ErrorCode.EDIT_ROOM_NOT_PERMISSION)
        room.room_name = update_room_request.room_name
        room.avatar_url = update_room_request.avatar_url
        room.description = update_room_request.description

        room = self.room_repository.save(room=room)
        return RoomResponse(
            room_id=room.room_id,
            room_name=room.room_name,
            creator_id=room.creator_id,
            last_mess=room.last_mess,
            room_type=room.room_type,
            avatar_url=room.avatar_url,
            description=room.description,
            created_at=room.created_at,
            updated_at=room.updated_at
        )

    def get_room_by_filter(self, request: FilterRoomRequest):
        result = self.room_repository.get_rooms_filter(
            room_name = request.room_name,
            room_type= request.room_type,
            user_id = request.user_id,
            page = request.page,
            page_size = request.page_size,
            sorts_by = request.sorts_by,
            sorts_dir = request.sorts_dir
        )
        items = [] 
        for item in result["items"]:
            items.append(
                RoomResponse(
                    room_id = item.Room.room_id,
                    room_name = item.Room.room_name,
                    creator_id = item.Room.creator_id,
                    last_mess = item.Room.last_mess,
                    room_type = item.Room.room_type,
                    avatar_url = item.Room.avatar_url,
                    description = item.Room.description,
                    created_at = item.Room.created_at,
                    updated_at = item.Room.updated_at,
                    last_sender = UserResponse.fromUserModel(item.User) if item.User is not None else UserResponse(
                        user_id = "",
                        email = "",
                        first_name = "",
                        last_name = "",
                        avatar_url = "",
                        is_verified = True,
                        method = E_Login_Method.NORMAL,
                        public_key = None,
                        biography = None
                    ),
                    encrypted_group_key= item.encrypted_group_key
                )
            )
        return BasePageResponse(
            items=items,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"]
        )

    def add_user_to_room(self, current_user_id: str, list_friend_user_id: list[str], room_id: str, list_friend_encrypted_group_key: list[str]):
        room = self.room_repository.get_room_by_room_id(room_id)
        if room is None:
            raise AppException(ErrorCode.SHEET_NOT_FOUND)
        if not self.user_room_repository.check_exist_by_user_id_and_room_id(current_user_id, room_id):
            raise AppException(ErrorCode.EDIT_ROOM_NOT_PERMISSION)
        
        if room.room_type == E_Room_Type.ONE:
            list_friend_user_id = list_friend_user_id[:1]

        for friend_user_id, friend_encrypted_group_key in zip(list_friend_user_id, list_friend_encrypted_group_key) :
            if not self.user_room_repository.check_exist_by_user_id_and_room_id(friend_user_id, room_id):
                self.user_room_repository.create_user_room(friend_user_id, room_id, friend_encrypted_group_key)
        return True

    def remove_user_from_room(self, current_user_id: str, list_user_id: list[str], room_id: str):
        room = self.room_repository.get_room_by_room_id(room_id)
        if room is None:
            raise AppException(ErrorCode.SHEET_NOT_FOUND)
        if room.creator_id != current_user_id:
            raise AppException(ErrorCode.EDIT_ROOM_NOT_PERMISSION)
        list_user_id_need_delete = list(filter(lambda x: x != current_user_id, list_user_id))
        self.user_room_repository.delete_user_room_by_room_id_and_list_user_id(room_id, list_user_id_need_delete)
            

    def leave_room(self, user_id: str, room_id: str):
        room = self.room_repository.get_room_by_room_id(room_id)
        if room is None:
            raise AppException(ErrorCode.SHEET_NOT_FOUND)
        if user_id != room.creator_id:
            self.user_room_repository.delete_user_room_by_user_id_and_room_id(user_id, room_id)

    def get_user_in_room(self, room_id: str):
        if not self.room_repository.check_exist_room_by_room_id(room_id):
            raise AppException(ErrorCode.SHEET_NOT_FOUND)
        users = self.user_room_repository.get_user_in_room(room_id)
        return [UserResponse.fromUserModel(user) for user in users]

    def delete_room(self, user_id: str, room_id:str):
        room = self.room_repository.get_room_by_room_id(room_id)
        if room is None:
            raise AppException(ErrorCode.SHEET_NOT_FOUND)
        if room.room_type == E_Room_Type.MANY:
            if room.creator_id == user_id:
                self.room_repository.delete_room_by_id(room_id)
                self.user_room_repository.delete_user_room_by_room_id(room_id)
                return room.room_id
        else:
            user_room_db = self.user_room_repository.get_user_room_by_user_id_and_room_id(user_id, room_id)
            if user_room_db is not None:
                self.room_repository.delete_room_by_id(room_id)
                self.user_room_repository.delete_user_room_by_room_id(room_id)
                return room.room_id
        return ""
        
    def get_room_chat_one_filter(self, request: FilterRoomOneRequest):

        result = self.room_repository.get_rooms_one_filter(
            friend_name= request.friend_name,
            user_id =  request.user_id,
            page = request.page,
            page_size = request.page_size,
            sorts_by = request.sorts_by,
            sorts_dir = request.sorts_dir
        )

        return BasePageResponse(
            items=[
                RoomChatOneResponse(
                    room_id = item.Room.room_id,
                    room_name = item.Room.room_name,
                    creator_id = item.Room.creator_id,
                    last_mess = item.Room.last_mess,
                    room_type = item.Room.room_type,
                    avatar_url = item.Room.avatar_url,
                    description = item.Room.description,
                    created_at = item.Room.created_at,
                    updated_at = item.Room.updated_at,
                    friend_id = item.friend_id,
                    friend_email = item.friend_email,
                    friend_frist_name = item.friend_frist_name,
                    friend_last_name = item.friend_last_name,
                    friend_avatar_url = item.friend_avatar_url,
                    last_sender = item[1] if item[1] is not None else UserResponse(
                        user_id = "",
                        email = "",
                        first_name = "",
                        last_name = "",
                        avatar_url = "",
                        is_verified = True,
                        method = E_Login_Method.NORMAL,
                        public_key = None,
                        biography = None
                    ),
                    encrypted_group_key= item.encrypted_group_key
                ) for item in result["items"]],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"]
        )

    def create_room_one(self,
                    room_name: str,
                    creator_id: str,
                    room_type: E_Room_Type,
                    avatar_url: str,
                    description: str,
                    member_ids: list[str],
                    encrypted_group_keys: list[str],
                    encrypted_group_key: str
                    ):
        if len(member_ids) >= 1:
            friend_id = member_ids[0]
            if not self.room_repository.is_exits_chat_one_one(creator_id, friend_id):
                room = self.room_repository.create_room(
                    room_name=room_name,
                    creator_id=creator_id,
                    room_type=room_type,
                    avatar_url=avatar_url,
                    description=description
                )
                list_user_room = [UserRoom(user_id = creator_id, room_id = room.room_id, encrypted_group_key = encrypted_group_key)]
                for member_id, member_encrypted_group_key  in zip(member_ids, encrypted_group_keys):
                    if member_id != creator_id:
                        list_user_room.append(UserRoom(user_id = member_id, room_id = room.room_id, encrypted_group_key = member_encrypted_group_key))
                        break
                self.user_room_repository.save_all(list_user_room)
                return room.room_id
        return None

    def create_room_many(self,
                    room_name: str,
                    creator_id: str,
                    room_type: E_Room_Type,
                    avatar_url: str,
                    description: str,
                    member_ids: list[str],
                    encrypted_group_keys: list[str],
                    encrypted_group_key: str
                    ):
        room = self.room_repository.create_room(
            room_name=room_name,
            creator_id=creator_id,
            room_type=room_type,
            avatar_url=avatar_url,
            description=description
        )
        
        visited = set()

        list_user_room = [UserRoom(user_id = creator_id, room_id = room.room_id, encrypted_group_key = encrypted_group_key)]
        visited.add(creator_id)
        for member_id, member_encrypted_group_key in zip(member_ids, encrypted_group_keys):
            if member_id not in visited:
                list_user_room.append(UserRoom(user_id = member_id, room_id = room.room_id, encrypted_group_key = member_encrypted_group_key))
                visited.add(member_id)
        self.user_room_repository.save_all(list_user_room)
        return room.room_id
    
    def get_encrypted_group_key_by_room_id(self, user_id: str, room_id: str) -> str:
        user_room_db = self.user_room_repository.get_user_room_by_user_id_and_room_id(user_id, room_id)
        if user_room_db is None:
            raise AppException(ErrorCode.SHEET_NOT_FOUND)
        return user_room_db.encrypted_group_key

    def get_room_one_one(self, current_user_id: str, user_id: str) -> Room:
        return self.room_repository.find_chat_one_one(current_user_id, user_id)
    
    def get_room_with_friend_id(self, current_user_id, friend_id):
        list_user_1 = self.room_repository.get_room_one_has_user_id(current_user_id)
        list_user_2 = self.room_repository.get_room_one_has_user_id(friend_id)
        set_room_id_2 = set([user_2.room_id for user_2 in list_user_2])
        for user_1 in list_user_1:
            if user_1.room_id in set_room_id_2:
                return user_1.room_id
        return ""
