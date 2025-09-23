import uuid
from core.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Text, TIMESTAMP, text

class RoleAttributes(Base):
    __tablename__ = "role_attributes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    
    # Relationships
    role_mappings = relationship("RoleAttributesMapper", back_populates="attribute") 