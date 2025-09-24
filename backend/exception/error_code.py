from enum import Enum

class ErrorCode(Enum):
    UNAUTHORIZED = (401, "Unauthorized")
    USER_NOT_FOUND = (1002, "User not found")
    INVALID_GOOGLE_TOKEN = (1013, "Invalid Google Token")
    PIN_INVALID = (1015, "Pin is invalid")
    SHEET_NOT_FOUND = (2001, "Sheet not found")
    EDIT_SHEET_NOT_PERMISSION = (2002, "Edit sheet not permission")

    def __init__(self, code: int, error_message: str):
        self.code = code
        self.error_message = error_message
        