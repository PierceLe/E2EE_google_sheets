from pydantic import BaseModel, Field
from typing import Any


class BaseResponse(BaseModel):
    """Base response model for all API endpoints"""
    
    code: int = Field(
        ..., 
        description="Response code: 0 for success, non-zero for errors",
        example=0
    )

    class Config:
        from_attributes = True  # To support conversion from ORM models
        schema_extra = {
            "example": {
                "code": 0
            }
        }
