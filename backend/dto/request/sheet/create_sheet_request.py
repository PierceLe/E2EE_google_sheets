from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl


class CreateSheetRequest(BaseModel):
    """Request model for creating a new encrypted sheet"""
    
    link: str = Field(
        ...,
        description="Google Sheets URL to be encrypted and managed",
        example="https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit",
        min_length=1
    )
    member_ids: List[str] = Field(
        default=[],
        description="List of user IDs to add as initial members (excluding creator)",
        example=["user_456", "user_789"]
    )
    encrypted_sheet_keys: List[str] = Field(
        default=[],
        description="List of sheet keys encrypted for each member (one per member_id)",
        example=["encrypted_key_for_user_456", "encrypted_key_for_user_789"]
    )
    encrypted_sheet_key: str = Field(
        ...,
        description="Sheet's AES key encrypted with creator's RSA public key",
        example="U2FsdGVkX1+vupppZksvRf5pq5g5XjFRIipRkwB0K1Y96Qsv2Lm+31cmzaAILwyt",
        min_length=1
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "link": "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit",
                "member_ids": ["user_456", "user_789"],
                "encrypted_sheet_keys": [
                    "U2FsdGVkX1+member456_encrypted_key",
                    "U2FsdGVkX1+member789_encrypted_key"
                ],
                "encrypted_sheet_key": "U2FsdGVkX1+creator_encrypted_sheet_key"
            }
        }
