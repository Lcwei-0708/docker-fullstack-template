import uuid
from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from core.database import Base

class RoleAttributes(Base):
    __tablename__ = "role_attributes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Relationships
    role_mappings = relationship("RoleAttributesMapper", back_populates="attribute") 