from typing import Optional
from exception.error_code import ErrorCode

class AppException(Exception):
    def __init__(self, error_code: ErrorCode, error_message: Optional[str] = None):
        self.error_code = error_code
        self.error_message = error_message
        

    def __str__(self):
        return f"{self.error_code.code}: {self.error_code.error_message}"
