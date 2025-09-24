from pydantic import BaseModel
from typing import Any


class BaseResponse(BaseModel):
    code: int

    class Config:
        from_attributes = True  # To support conversion from ORM models
