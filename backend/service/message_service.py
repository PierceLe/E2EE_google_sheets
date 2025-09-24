import datetime
from dto.response.message.message_response import MessageResponse
from model.message import Message
from model.user import User
from repository.message_repository import MessageRepository
from repository.room_repository import RoomRepository
from repository.user_room_repository import UserRoomRepository
from dto.request.auth.user_create_request import UserCreateRequest
from dto.response.user_response import UserResponse
from dto.response.user_full_response import UserFullResponse

class MessageService():
    def __init__(self):
        self.message_repository = MessageRepository()
        self.room_repository = RoomRepository()

    def save(self, sender_id, room_id, message_type, content, file_url):
        mess = Message(
            sender_id = sender_id,
            room_id = room_id,
            message_type = message_type,
            content = content, 
            file_url = file_url
        )
        mess_db = self.message_repository.save(mess)
        self.room_repository.update_last_message_in_room(room_id, mess.content, sender_id)
        return mess_db
    
    def get_all_mess_in_room(self, room_id: str):
        items = self.message_repository.get_all_mess_in_room(room_id)
        res = []
        for item in items:
            mess_db: Message = item.Message
            user_db: User = item.User
            res.append(MessageResponse(
                id = mess_db.id,
                room_id = mess_db.room_id,
                message_type = mess_db.message_type,
                content = mess_db.content,
                file_url = mess_db.file_url,
                created_at = mess_db.created_at,
                updated_at = mess_db.updated_at,
                sender = UserResponse.fromUserModel(user_db)))
        return res

    def get_more_mess_in_room(self, room_id: str, created_at: datetime.datetime, limit: int):
        print("get_more_mess_in_room: ", created_at)
        items = self.message_repository.get_more_mess_in_room(room_id, created_at, limit)
        res = []
        for item in items[::-1]:
            mess_db: Message = item.Message
            user_db: User = item.User
            res.append(MessageResponse(
                id = mess_db.id,
                room_id = mess_db.room_id,
                message_type = mess_db.message_type,
                content = mess_db.content,
                file_url = mess_db.file_url,
                created_at = mess_db.created_at,
                updated_at = mess_db.updated_at,
                sender = UserResponse.fromUserModel(user_db)))
        return res