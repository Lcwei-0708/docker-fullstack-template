import uuid
from datetime import datetime
from core.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Boolean, DateTime

class Users(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    email = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    hash_password = Column(String(255), nullable=True)
    status = Column(Boolean, nullable=False, default=True)
    password_reset_required = Column(Boolean, nullable=False, default=False, server_default='false')
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    login_logs = relationship("LoginLogs", back_populates="user")
    user_sessions = relationship("UserSessions", back_populates="user")
    role_mappings = relationship("RoleMapper", back_populates="user")
    password_reset_tokens = relationship("PasswordResetTokens", back_populates="user")