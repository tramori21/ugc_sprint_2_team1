import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from db.postgres import Base


class SocialAccount(Base):
    __tablename__ = 'social_accounts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    provider = Column(String(32), nullable=False)
    social_id = Column(String(255), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User')

    __table_args__ = (
        UniqueConstraint('provider', 'social_id', name='uq_social_provider_social_id'),
    )
