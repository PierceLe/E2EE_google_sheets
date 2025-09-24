from typing import Optional
from pydantic import BaseModel


class CreateSheetRequest(BaseModel):
    link: str
    member_ids: list[str] = []
    encrypted_sheet_keys: list[str] = []
    encrypted_sheet_key: str

    class Config:
        from_attributes = True
