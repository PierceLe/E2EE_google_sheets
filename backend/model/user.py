import uuid
from sqlalchemy import Column, String, Text
from database import Base

class User(Base):
    __tablename__ = "user"
    
    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String(255), unique=True, index=True) 
    first_name = Column(String(100), unique=False)
    last_name = Column(String(100), unique=False)
    avatar_url = Column(String(500))
    pin = Column(Text())
    public_key = Column(Text())
    encrypted_private_key = Column(Text())
