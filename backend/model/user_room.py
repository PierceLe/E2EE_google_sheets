import uuid

from sqlalchemy import Column, String, Text

from database import Base


class UserRoom(Base):
    __tablename__ = 'user_room'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)

    user_id = Column(String(36))
    room_id = Column(String(36))

    encrypted_group_key = Column(Text())