from dto.response.base_response import BaseResponse
from typing import Any
from pydantic import Field

class ErrorResponse(BaseResponse):
    """Standard error response for failed API operations"""
    
    code: int = Field(
        ...,
        description="Error code (non-zero for errors, specific codes for different error types)",
        example=400
    )
    error_message: str = Field(
        ...,
        description="Human-readable error message describing what went wrong",
        example="Invalid request parameters"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "code": 400,
                "error_message": "Invalid request parameters"
            }
        }