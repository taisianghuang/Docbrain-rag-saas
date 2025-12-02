import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON
from app.db.base import Base


class Client(Base):
    __tablename__ = "client"

    id = Column(String(length=36), primary_key=True,
                default=lambda: str(uuid.uuid4()))
    name = Column(String(length=255), nullable=True)
    # NOTE: For prototype we store API key plaintext in this column.
    # Replace with encrypted storage or external key manager in production.
    api_key = Column(String(length=1024), nullable=True)
    settings = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


__all__ = ["Client"]
