from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func

from app.core.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    contact_name = Column(String(200), default="")
    phone = Column(String(50), default="")
    email = Column(String(254), default="")
    notes = Column(Text, default="")
    created_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True, nullable=False)
