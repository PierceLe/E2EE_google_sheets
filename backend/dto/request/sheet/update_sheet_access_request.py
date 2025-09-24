from pydantic import BaseModel
from typing import Optional


class UpdateSheetAccessRequest(BaseModel):
    role: Optional[str] = None  # owner, editor, viewer
    is_favorite: Optional[bool] = None
    encrypted_sheet_key: Optional[str] = None

    class Config:
        from_attributes = True
