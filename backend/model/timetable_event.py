import uuid
import datetime
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from database import Base

class TimetableEvent(Base):
    __tablename__ = "timetable_event"
    
    event_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("user.user_id"))
    title = Column(String(100))
    description = Column(String(500))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    location = Column(String(200))
    color = Column(String(50))
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(100))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow) 