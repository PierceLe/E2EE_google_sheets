from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

# Association table for user-sheet relationships (many-to-many)
user_sheet_association = Table(
    'user_sheets',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('sheet_id', Integer, ForeignKey('sheets.id'), primary_key=True),
    Column('permission', String(20), default='read')  # read, write, admin
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    google_id = Column(String(255), unique=True, nullable=True)
    
    # E2EE key management
    public_key = Column(Text, nullable=True)  # RSA public key for key exchange
    encrypted_private_key = Column(Text, nullable=True)  # User's encrypted private key
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owned_sheets = relationship("Sheet", back_populates="owner")
    shared_sheets = relationship("Sheet", secondary=user_sheet_association, back_populates="shared_users")
    encryption_keys = relationship("EncryptionKey", back_populates="user")


class Sheet(Base):
    __tablename__ = "sheets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    google_sheet_id = Column(String(255), unique=True, nullable=False)  # Google Sheets ID
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Encrypted metadata
    encrypted_title = Column(Text, nullable=True)  # Original title (encrypted)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="owned_sheets")
    shared_users = relationship("User", secondary=user_sheet_association, back_populates="shared_sheets")
    encryption_keys = relationship("EncryptionKey", back_populates="sheet")


class EncryptionKey(Base):
    __tablename__ = "encryption_keys"

    id = Column(Integer, primary_key=True, index=True)
    sheet_id = Column(Integer, ForeignKey("sheets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Encrypted sheet key (encrypted with user's public key)
    encrypted_key = Column(Text, nullable=False)
    key_version = Column(Integer, default=1)  # For key rotation
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sheet = relationship("Sheet", back_populates="encryption_keys")
    user = relationship("User", back_populates="encryption_keys")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sheet_id = Column(Integer, ForeignKey("sheets.id"), nullable=True)
    action = Column(String(100), nullable=False)  # create, read, update, delete, share
    details = Column(Text, nullable=True)  # JSON details about the action
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
