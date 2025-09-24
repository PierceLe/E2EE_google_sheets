from typing import Any
from pydantic import BaseModel


class WebSocketResponse(BaseModel):
    action: str
    data: Any

    class Config:
        from_attributes = True  # To support conversion from ORM models