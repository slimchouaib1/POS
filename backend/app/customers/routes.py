import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.audit.models import AuditLog
from app.auth.models import User
from app.core.config import settings
from app.core.deps import get_db, require_role
from app.customers.models import Customer

router = APIRouter(prefix="/api/customers", tags=["Customers"])


class CustomerOut(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    archetype: str
    price_tier: str
    time_preference: str
    day_preference: str
    visit_count: int
    total_spent: float
    last_visit: Optional[datetime] = None

    class Config:
        from_attributes = True


class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=6, max_length=20)
    email: EmailStr | None = None

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        digits = re.sub(r"\D", "", value)
        if len(digits) < 6 or len(digits) > 15:
            raise ValueError("Phone number must contain 6 to 15 digits")
        return f"+{digits}" if value.strip().startswith("+") else digits


def _mask_phone(phone: str) -> str:
    if len(phone) <= 4:
        return "****"
    return f"***{phone[-4:]}"


@router.get("", response_model=list[CustomerOut])
def list_customers(
    search: Optional[str] = Query(None, max_length=100),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_CASHIER)),
):
    q = db.query(Customer)
    if search:
        q = q.filter(
            or_(
                Customer.name.ilike(f"%{search}%"),
                Customer.phone.ilike(f"%{search}%"),
            )
        )
    customers = q.order_by(Customer.total_spent.desc()).offset(offset).limit(limit).all()
    return [CustomerOut.model_validate(c) for c in customers]


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_CASHIER)),
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Client introuvable")
    return CustomerOut.model_validate(customer)


@router.post("", response_model=CustomerOut)
def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_CASHIER)),
):
    existing = db.query(Customer).filter(Customer.phone == data.phone).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "A customer with this phone number already exists",
                "existing_customer": CustomerOut.model_validate(existing).model_dump(),
            },
        )

    customer = Customer(
        name=data.name.strip(),
        phone=data.phone,
        email=str(data.email) if data.email else "",
    )
    db.add(customer)
    db.flush()

    db.add(AuditLog(
        user_id=current_user.id,
        action="create_customer",
        entity_type="customer",
        entity_id=customer.id,
        details=f"Quick-registered customer '{customer.name}' (phone: {_mask_phone(customer.phone)})",
    ))
    db.commit()
    db.refresh(customer)
    return CustomerOut.model_validate(customer)
