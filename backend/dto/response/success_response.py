from dto.response.base_response import BaseResponse
from typing import Any
from pydantic import Field

class SuccessResponse(BaseResponse):
    """Standard success response for all successful API operations"""
    
    code: int = Field(
        default=0,
        description="Success code (always 0 for successful operations)",
        example=0
    )
    message: str = Field(
        default="successfully",
        description="Success message describing the operation result",
        example="successfully"
    )
    result: Any = Field(
        default=None,
        description="Operation result data (type varies by endpoint)",
        example={"data": "example result"}
    )

    class Config:
        schema_extra = {
            "example": {
                "code": 0,
                "message": "successfully",
                "result": {
                    "example_field": "example_value",
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            }
        }
