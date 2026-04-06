import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from db.postgres import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    login = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    roles = relationship(
        'UserRole',
        back_populates='user',
        cascade='all, delete-orphan')
    login_history = relationship(
        'LoginHistory',
        back_populates='user',
        cascade='all, delete-orphan')
    refresh_tokens = relationship(
        'RefreshToken',
        back_populates='user',
        cascade='all, delete-orphan')
