from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Table(Base):
    __tablename__ = "tables"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, unique=True, nullable=False)
    section = Column(String(50), default="Main")
    capacity = Column(Integer, default=4)
    status = Column(String(20), default="available")  # available, occupied, reserved

    orders = relationship("Order", back_populates="table")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    cashier_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="draft")  # draft, in_progress, served, paid, cancelled
    total_amount = Column(Float, default=0.0)
    discount_pct = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    notes = Column(Text, default="")
    cancel_reason = Column(Text, default="")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    table = relationship("Table", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(200), default="")  # denormalized for receipts
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    discount_pct = Column(Float, default=0.0)
    subtotal = Column(Float, nullable=False)
    notes = Column(Text, default="")

    order = relationship("Order", back_populates="items")
