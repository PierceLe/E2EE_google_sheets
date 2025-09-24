from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class EventResponse(BaseModel):
    event_id: str
    user_id: str
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    color: Optional[str] = None
    is_recurring: bool
    recurrence_pattern: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 