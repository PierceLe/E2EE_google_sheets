from dto.response.base_response import BaseResponse
from typing import Any

class ErrorResponse(BaseResponse):
    code: int
    error_message: str