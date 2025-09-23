from core.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Boolean, ForeignKey, TIMESTAMP, text

class RoleAttributesMapper(Base):
    __tablename__ = "role_attributes_mapper"
    
    role_id = Column(String(36), ForeignKey("roles.id"), primary_key=True)
    attributes_id = Column(String(36), ForeignKey("role_attributes.id"), primary_key=True)
    value = Column(Boolean, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    
    # Relationships
    role = relationship("Roles", back_populates="attribute_mappings")
    attribute = relationship("RoleAttributes", back_populates="role_mappings") 