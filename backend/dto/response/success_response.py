from dto.response.base_response import BaseResponse
from typing import Any

class SuccessResponse(BaseResponse):
    code: int = 0
    message: str = "successfully"
    result: Any = None  # Can be any type (dict, list, str, etc.)
   
