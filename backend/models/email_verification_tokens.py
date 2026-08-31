from sqlalchemy import TIMESTAMP, Boolean, Column, ForeignKey, String, Text, text
from sqlalchemy.orm import relationship
from uuid_utils import uuid7

from core.database import Base


class EmailVerificationTokens(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid7()), unique=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    email = Column(String(50), nullable=False, index=True)
    token = Column(Text, nullable=False, unique=True, index=True)
    token_type = Column(String(20), nullable=False, index=True)
    is_used = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )
    expires_at = Column(TIMESTAMP, nullable=False)

    # Relationships
    user = relationship("Users", back_populates="email_verification_tokens")
