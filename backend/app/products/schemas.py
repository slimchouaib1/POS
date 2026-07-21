from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    description: str = Field(default="", max_length=500)
    icon: str = Field(default="box", max_length=40)
    display_order: int = Field(default=0, ge=0, le=10_000)


class CategoryOut(BaseModel):
    id: int
    name: str
    description: str
    icon: str
    display_order: int
    product_count: int = 0

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    category_id: int = Field(..., gt=0)
    section: str = Field(default="", max_length=80)
    price: float = Field(..., ge=0, le=100_000)
    description: str = Field(default="", max_length=1000)
    image_url: str = Field(default="", max_length=2048)
    stock_quantity: int = Field(default=100, ge=0, le=1_000_000)
    low_stock_threshold: int = Field(default=10, ge=0, le=1_000_000)


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    category_id: Optional[int] = Field(default=None, gt=0)
    section: Optional[str] = Field(default=None, max_length=80)
    price: Optional[float] = Field(default=None, ge=0, le=100_000)
    description: Optional[str] = Field(default=None, max_length=1000)
    image_url: Optional[str] = Field(default=None, max_length=2048)
    is_available: Optional[bool] = None
    stock_quantity: Optional[int] = Field(default=None, ge=0, le=1_000_000)
    low_stock_threshold: Optional[int] = Field(default=None, ge=0, le=1_000_000)


class ProductOut(BaseModel):
    id: int
    name: str
    category_id: int
    category_name: str = ""
    section: str
    price: float
    description: str
    image_url: str
    is_available: bool
    stock_quantity: int
    low_stock_threshold: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IngredientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    unit: str = Field(..., min_length=1, max_length=30)
    current_stock: float = Field(default=0.0, ge=0, le=1_000_000)
    low_stock_threshold: float = Field(default=500.0, ge=0, le=1_000_000)
    cost_per_unit: float = Field(default=0.01, ge=0, le=100_000)
    supplier: str = Field(default="", max_length=120)
    category: str = Field(default="", max_length=80)


class IngredientUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    unit: Optional[str] = Field(default=None, min_length=1, max_length=30)
    current_stock: Optional[float] = Field(default=None, ge=0, le=1_000_000)
    low_stock_threshold: Optional[float] = Field(default=None, ge=0, le=1_000_000)
    cost_per_unit: Optional[float] = Field(default=None, ge=0, le=100_000)
    supplier: Optional[str] = Field(default=None, max_length=120)
    category: Optional[str] = Field(default=None, max_length=80)


class IngredientOut(BaseModel):
    id: int
    name: str
    unit: str
    current_stock: float
    low_stock_threshold: float
    cost_per_unit: float
    supplier: str
    category: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RecipeLineCreate(BaseModel):
    ingredient_id: int = Field(..., gt=0)
    quantity_needed: float = Field(..., gt=0, le=1_000_000)


class RecipeLineUpdate(BaseModel):
    quantity_needed: float = Field(..., gt=0, le=1_000_000)


class RecipeLineOut(BaseModel):
    ingredient_id: int
    ingredient_name: str
    unit: str
    quantity_needed: float

    class Config:
        from_attributes = True
