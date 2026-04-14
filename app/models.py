from sqlalchemy import Column, Integer, String, DateTime, func
from .db import Base


class NumberEntry(Base):
    __tablename__ = "numbers"

    id = Column(Integer, primary_key=True, index=True)
    normalized_number = Column(String, unique=True, index=True, nullable=False)
    submitted_by = Column(String, nullable=False, default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())