import uuid
from sqlalchemy import Column, String, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from core.database import Base

class Roles(Base):
    __tablename__ = "roles"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP')
    updated_at = Column(TIMESTAMP, nullable=False, server_default='CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')
    
    # Relationships
    user_mappings = relationship("RoleMapper", back_populates="role")
    attribute_mappings = relationship("RoleAttributesMapper", back_populates="role") 