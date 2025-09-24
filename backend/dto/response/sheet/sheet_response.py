from pydantic import BaseModel
from datetime import datetime
from dto.response.user_response import UserResponse
from typing import Optional


class SheetResponse(BaseModel):
    sheet_id: str
    link: str
    creator_id: str
    created_at: datetime
    role: Optional[str] = None
    encrypted_sheet_key: Optional[str] = None
    is_favorite: Optional[bool] = None
    last_accessed_at: Optional[datetime] = None
    creator: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True
