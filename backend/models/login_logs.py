import uuid
from sqlalchemy import Column, String, Boolean, TIMESTAMP, Text, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base

class LoginLogs(Base):
    __tablename__ = "login_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    email = Column(String(50), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=False)
    is_success = Column(Boolean, nullable=False)
    failure_reason = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    updated_at = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')
    
    # Relationships
    user = relationship("Users", back_populates="login_logs") 