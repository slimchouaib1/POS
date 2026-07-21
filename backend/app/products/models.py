from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, func, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, default="")
    icon = Column(String(50), default="📦")
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    section = Column(String(50), default="")  # restaurant_type: American, Cafe, Italian, etc.
    price = Column(Float, nullable=False)
    description = Column(Text, default="")
    image_url = Column(String(500), default="")
    is_available = Column(Boolean, default=True)
    stock_quantity = Column(Integer, default=100)
    low_stock_threshold = Column(Integer, default=10)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    category = relationship("Category", back_populates="products")
    recipe = relationship("ProductIngredient", back_populates="product")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    unit = Column(String(50), nullable=False)            # g, ml, pcs, leaves, etc.
    current_stock = Column(Float, default=0)
    low_stock_threshold = Column(Float, default=500)
    cost_per_unit = Column(Float, default=0.01)           # DT per unit
    supplier = Column(String(200), default="")
    category = Column(String(100), default="")            # Protein, Dairy, Grain, Vegetable, etc.
    created_at = Column(DateTime, server_default=func.now())

    recipe_usages = relationship("ProductIngredient", back_populates="ingredient")


class ProductIngredient(Base):
    """Recipe join table: how much of each ingredient goes into 1 serving of a menu item."""
    __tablename__ = "product_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    quantity_needed = Column(Float, nullable=False)       # amount per 1 serving, in ingredient's unit

    product = relationship("Product", back_populates="recipe")
    ingredient = relationship("Ingredient", back_populates="recipe_usages")
