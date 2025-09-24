from pydantic import BaseModel
from datetime import datetime

class GetEventsByRangeRequest(BaseModel):
    start_date: datetime
    end_date: datetime

    class Config:
        from_attributes = True 