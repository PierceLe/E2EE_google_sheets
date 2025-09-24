import uuid

from sqlalchemy import Column, String, ForeignKey, DateTime, text
from sqlalchemy.dialects.mysql import CHAR
from database import Base

class Sheet(Base):
    __tablename__ = "sheet"

    sheet_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    link = Column(String(1000), nullable=False)
    creator_id = Column(CHAR(36),ForeignKey("user.user_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )