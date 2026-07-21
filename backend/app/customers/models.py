from sqlalchemy import Column, Integer, String, Float, DateTime, func
from app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), default="")
    phone = Column(String(20), default="")
    archetype = Column(String(50), default="")
    price_tier = Column(String(20), default="")
    time_preference = Column(String(20), default="")
    day_preference = Column(String(20), default="")
    visit_count = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    last_visit = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
