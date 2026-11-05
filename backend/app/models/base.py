import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, String
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class TimestampMixin:
    """Standard timestamp mixin for database models."""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

