from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: str
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    is_active: Optional[bool] = None
    public_key: Optional[str] = None
    encrypted_private_key: Optional[str] = None


class User(UserBase):
    id: int
    is_verified: bool
    google_id: Optional[str] = None
    public_key: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SheetBase(BaseModel):
    name: str
    google_sheet_id: str


class SheetCreate(SheetBase):
    encrypted_title: Optional[str] = None


class SheetUpdate(BaseModel):
    name: Optional[str] = None
    encrypted_title: Optional[str] = None
    is_active: Optional[bool] = None


class Sheet(SheetBase):
    id: int
    owner_id: int
    encrypted_title: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    owner: User
    shared_users: List[User] = []

    class Config:
        from_attributes = True


class EncryptionKeyBase(BaseModel):
    encrypted_key: str
    key_version: Optional[int] = 1


class EncryptionKeyCreate(EncryptionKeyBase):
    sheet_id: int
    user_id: int


class EncryptionKey(EncryptionKeyBase):
    id: int
    sheet_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class GoogleAuthRequest(BaseModel):
    code: str


class ShareSheetRequest(BaseModel):
    sheet_id: int
    user_email: str
    permission: str = "read"  # read, write, admin
    encrypted_key: str  # Sheet key encrypted with recipient's public key


class SheetDataRequest(BaseModel):
    sheet_id: int
    encrypted_data: str  # Encrypted spreadsheet data
    range_name: Optional[str] = None  # A1:Z100, etc.


class SheetDataResponse(BaseModel):
    sheet_id: int
    encrypted_data: str
    range_name: Optional[str] = None
    last_modified: datetime
