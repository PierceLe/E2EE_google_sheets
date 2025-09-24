import datetime
import uuid
from sqlalchemy import Column, String, DateTime, Enum as SqlEnum, Text
from database import Base
from enums.enum_message_type import E_Message_Type

class Message(Base):
    __tablename__ = "message"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    sender_id = Column(String(36), nullable= False)
    room_id = Column(String(36), nullable= False)
    message_type = Column(SqlEnum(E_Message_Type), nullable=False)
    content = Column(Text())
    file_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
