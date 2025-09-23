import uuid
from core.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Boolean, TIMESTAMP, ForeignKey, Text

class PasswordResetTokens(Base):
    __tablename__ = "password_reset_tokens"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    token = Column(Text, nullable=False, unique=True, index=True)
    is_used = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    updated_at = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')
    expires_at = Column(TIMESTAMP, nullable=False)
    
    # Relationships
    user = relationship("Users", back_populates="password_reset_tokens")