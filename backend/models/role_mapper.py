from core.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, ForeignKey, TIMESTAMP, text

class RoleMapper(Base):
    __tablename__ = "role_mapper"
    
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    role_id = Column(String(36), ForeignKey("roles.id"), primary_key=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    
    # Relationships
    user = relationship("Users", back_populates="role_mappings")
    role = relationship("Roles", back_populates="user_mappings") 