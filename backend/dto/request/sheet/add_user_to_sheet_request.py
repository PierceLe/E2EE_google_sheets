from pydantic import BaseModel
from typing import List


class AddUserToSheetRequest(BaseModel):
    user_ids: List[str]
    encrypted_sheet_keys: List[str]
    roles: List[str] = []  # Optional roles for each user (defaults to "viewer")

    class Config:
        from_attributes = True
