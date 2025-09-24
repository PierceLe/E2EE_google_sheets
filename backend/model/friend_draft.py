import datetime
import uuid
from sqlalchemy import Column, DateTime, String, Boolean, UniqueConstraint
from database import Base

class FriendDraft(Base):
    __tablename__ = "friend_draft"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36))
    friend_id = Column(String(36))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "friend_id", name="friend_draft_unique_constraint_1"),)