from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

OrderStatus = Literal["draft", "in_progress", "served", "paid", "cancelled"]
TableStatus = Literal["available", "occupied", "reserved"]


class TableOut(BaseModel):
    id: int
    number: int
    section: str
    capacity: int
    status: str

    class Config:
        from_attributes = True


class OrderItemCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(default=1, gt=0, le=100)
    notes: str = Field(default="", max_length=500)
    discount_pct: float = Field(default=0.0, ge=0, le=100)


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    discount_pct: float
    subtotal: float
    notes: str

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    table_id: Optional[int] = Field(default=None, gt=0)
    customer_id: Optional[int] = Field(default=None, gt=0)
    items: list[OrderItemCreate] = Field(default_factory=list, min_length=1, max_length=100)
    notes: str = Field(default="", max_length=1000)
    discount_pct: float = Field(default=0.0, ge=0, le=100)


class OrderUpdate(BaseModel):
    items: Optional[list[OrderItemCreate]] = Field(default=None, min_length=1, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=1000)
    discount_pct: Optional[float] = Field(default=None, ge=0, le=100)
    table_id: Optional[int] = Field(default=None, gt=0)
    customer_id: Optional[int] = Field(default=None, gt=0)


class OrderOut(BaseModel):
    id: int
    table_id: Optional[int]
    table_number: Optional[int] = None
    customer_id: Optional[int]
    cashier_id: int
    cashier_name: str = ""
    status: str
    total_amount: float
    discount_pct: float
    discount_amount: float
    notes: str
    cancel_reason: str
    items: list[OrderItemOut] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
