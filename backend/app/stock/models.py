from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, func, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity_change = Column(Integer, nullable=False)  # positive=in, negative=out
    reason = Column(String(100), default="")  # order, adjustment, restock, waste
    details = Column(Text, default="")
    triggered_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class IngredientStockMovement(Base):
    __tablename__ = "ingredient_stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    quantity_change = Column(Float, nullable=False)      # negative=out (sale), positive=in (restock/refund)
    reason = Column(String(100), default="")             # sale, adjustment, restock, waste, refund
    details = Column(Text, default="")
    triggered_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False, index=True)
    quantity_ordered = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)
    created_at = Column(DateTime, server_default=func.now())
    received_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    ingredient = relationship("Ingredient")
    creator = relationship("User")
