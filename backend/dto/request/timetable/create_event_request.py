from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CreateEventRequest(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    color: Optional[str] = None
    is_recurring: Optional[bool] = False
    recurrence_pattern: Optional[str] = None

    class Config:
        from_attributes = True 