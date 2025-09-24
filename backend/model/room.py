import uuid
from sqlalchemy import Column, String, DateTime, Enum as SqlEnum
from database import Base
from enums.enum_room_type import E_Room_Type
import datetime

class Room(Base):
    __tablename__ = "room"

    room_id = Column(String(36), primary_key= True, default=lambda: str(uuid.uuid4()), index=True)

    room_name = Column(String(50), index= True)
    creator_id = Column(String(36))
    last_mess = Column(String(500))
    room_type = Column(SqlEnum(E_Room_Type), nullable=False)
    avatar_url = Column(String(500))
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    last_sender_id = Column(String(36))