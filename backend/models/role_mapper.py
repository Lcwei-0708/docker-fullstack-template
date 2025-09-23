from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base

class RoleMapper(Base):
    __tablename__ = "role_mapper"
    
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    role_id = Column(String(36), ForeignKey("roles.id"), primary_key=True)
    
    # Relationships
    user = relationship("Users", back_populates="role_mappings")
    role = relationship("Roles", back_populates="user_mappings") 