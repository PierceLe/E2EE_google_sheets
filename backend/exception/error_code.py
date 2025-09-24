from enum import Enum

class ErrorCode(Enum):
    UNAUTHORIZED = (401, "Unauthorized")
    USER_EXISTED = (1001, "User existed")
    USER_NOT_FOUND = (1002, "User not found")
    PASSWORD_INVALID = (1002, "Password must be at least 8 characters long and contain at least one uppercase letter and contain at least one uppercase letter, one lowercase letter and one special character")
    EMAIL_INVALID = (1003, "Email is invalid")
    EMAIL_VERIFICATION_FAILED =  (1004, "Email verification failed") 
    CONFIRM_PASSWORD_DIFFER_NEW_PASSWORD  = (1005, "Confirm Password differ Password") 
    PASSWORD_INCORRECT = (1006, "Password is incorrect") 
    ACCOUNT_INCORRECT = (1007, "Username or password is incorrect") 
    ACCOUNT_USED_2FA = (1008, "Account used 2fa for login") 
    ACCOUNT_NOT_USED_2FA = (1009, "Account not registered to use 2fa") 
    SIGUP_USING_2FA_FAILED = (1010, "2FA REGISTRATION FAILED")
    TWOFA_VERIFICATION_FAILED =  (1011, "2FA authentication failed")  
    CODE_2FA_WRONG =  (1012, "Code 2FA is incorrect") 
    INVALID_GOOGLE_TOKEN = (1013, "Invalid Google Token") 
    INVALID_METHOD_LOGIN = (1014, "Account was registered by another method")
    PIN_INVALID = (1015, "Pin is invalid")

    NOT_PERMISSION = (9998, "Not permission")
    UNCATEGORIZED_EXCEPTION = (9999, "An uncategorized error occurred")

    ROOM_NOT_FOUND = (2001, "Room not found")
    EDIT_ROOM_NOT_PERMISSION = (2002, "Edit room not permission")
    
    INVALID_TIME_RANGE = (3001, "Invalid time range: start time must be before end time")

    def __init__(self, code: int, error_message: str):
        self.code = code
        self.error_message = error_message
        