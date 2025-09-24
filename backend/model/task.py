import uuid
import datetime
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from database import Base

class Task(Base):
    __tablename__ = "task"
    
    task_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)

    room_id = Column(String(36), ForeignKey("room.room_id"))
    task_name = Column(String(100))  
    task_description = Column(String(500))
    assigner_id = Column(String(36))  
    assignee_id = Column(String(36))
    status = Column(String(12))  # TO DO, In Progress, REVIEW, DONE
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
