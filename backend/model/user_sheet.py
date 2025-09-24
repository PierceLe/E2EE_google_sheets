from sqlalchemy import Column, Enum, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.mysql import CHAR
from database import Base


class UserSheet(Base):
    __tablename__ = "user_sheet"

    user_id = Column(
        CHAR(36),
        ForeignKey("user.user_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )
    sheet_id = Column(
        CHAR(36),
        ForeignKey("sheet.sheet_id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )
    role = Column(
        Enum("owner", "editor", "viewer", name="user_sheet_role"),
        nullable=False,
        server_default="viewer"
    )
    encrypted_sheet_key = Column(Text, nullable=False)
    is_favorite = Column(Boolean, server_default="false", nullable=False)
    last_accessed_at = Column(DateTime, nullable=True)