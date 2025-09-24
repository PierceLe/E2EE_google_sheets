import datetime
from typing import Optional, List
from sqlalchemy import and_, or_
from database import get_db
from model.message import Message
from model.user import User

class MessageRepository():
    def __init__(self):
        self.db = next(get_db())
    
    def save(self, message: Message) -> Message:
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def get_all_mess_in_room(self, room_id: str):
        return self.db.query(Message, User).filter(
            Message.room_id == room_id
            ).join(
                User, Message.sender_id == User.user_id
                ).order_by(Message.created_at.asc()
                           ).all()
    
    def get_all_mess_in_rooms(self, room_ids: List[str]):
        return self.db.query(Message, User).filter(
            Message.room_id in room_ids
            ).join(
                User, Message.sender_id == User.user_id
                ).order_by(Message.created_at.asc()
                           ).all()

    def get_more_mess_in_room(self, room_id: str, created_at: datetime.datetime, litmit: int = 50):
        query = self.db.query(Message, User).filter(
            and_(
                Message.room_id == room_id,
                Message.created_at < created_at
                )
            ).join(User, 
                   Message.sender_id == User.user_id
                   ).order_by(Message.created_at.desc()).limit(litmit)
        return query.all()