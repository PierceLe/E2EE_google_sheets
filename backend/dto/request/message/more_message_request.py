import datetime
from typing import Optional

from pydantic import BaseModel


class MoreMessageRequest(BaseModel):
    room_id: str
    created_at: datetime.datetime
    limit: Optional[int] = 20