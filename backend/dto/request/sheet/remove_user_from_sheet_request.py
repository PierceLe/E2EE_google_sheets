from pydantic import BaseModel
from typing import List


class RemoveUserFromSheetRequest(BaseModel):
    user_ids: List[str]

    class Config:
        from_attributes = True
