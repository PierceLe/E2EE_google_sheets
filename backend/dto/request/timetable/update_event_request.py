from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UpdateEventRequest(BaseModel):
    event_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    color: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None

    class Config:
        from_attributes = True 