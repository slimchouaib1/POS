from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    amount = Column(Float, nullable=False)
    method = Column(String(20), default="cash")  # cash, card, mobile
    status = Column(String(20), default="completed")  # completed, refunded
    reference = Column(String(100), default="")
    created_at = Column(DateTime, server_default=func.now())

    order = relationship("Order", back_populates="payments")
