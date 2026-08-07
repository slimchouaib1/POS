import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session

from app.audit.models import AuditLog
from app.auth.models import User
from app.core.config import settings
from app.core.deps import get_db, require_role
from app.suppliers.models import Supplier

router = APIRouter(prefix="/api/suppliers", tags=["Suppliers"])


class SupplierBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    contact_name: str = Field(default="", max_length=200)
    phone: str = Field(default="", max_length=50)
    email: Optional[EmailStr] = None
    notes: str = Field(default="", max_length=2000)

    @field_validator("name", "contact_name", "notes", mode="before")
    @classmethod
    def trim_text(cls, value):
        if value is None:
            return ""
        return str(value).strip()

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, value):
        if value is None:
            return ""
        value = str(value).strip()
        if not value:
            return ""
        normalized = re.sub(r"[^\d+]", "", value)
        if normalized.count("+") > 1 or ("+" in normalized and not normalized.startswith("+")):
            raise ValueError("phone may contain digits and an optional leading +")
        if len(re.sub(r"\D", "", normalized)) < 6:
            raise ValueError("phone must contain at least 6 digits")
        return normalized


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    contact_name: Optional[str] = Field(default=None, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=50)
    email: Optional[EmailStr] = None
    notes: Optional[str] = Field(default=None, max_length=2000)
    is_active: Optional[bool] = None

    @field_validator("name", "contact_name", "notes", mode="before")
    @classmethod
    def trim_text(cls, value):
        if value is None:
            return value
        return str(value).strip()

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, value):
        if value is None:
            return value
        value = str(value).strip()
        if not value:
            return ""
        normalized = re.sub(r"[^\d+]", "", value)
        if normalized.count("+") > 1 or ("+" in normalized and not normalized.startswith("+")):
            raise ValueError("phone may contain digits and an optional leading +")
        if len(re.sub(r"\D", "", normalized)) < 6:
            raise ValueError("phone must contain at least 6 digits")
        return normalized


class SupplierOut(BaseModel):
    id: int
    name: str
    contact_name: str
    phone: str
    email: str
    notes: str
    created_at: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True


def _supplier_write_roles():
    return require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_STOCK_MANAGER)


@router.get("", response_model=list[SupplierOut])
def list_suppliers(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_STOCK_MANAGER)),
):
    q = db.query(Supplier)
    if active_only:
        q = q.filter(Supplier.is_active.is_(True))
    return q.order_by(Supplier.name).all()


@router.get("/{supplier_id}", response_model=SupplierOut)
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_STOCK_MANAGER)),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.post("", response_model=SupplierOut)
def create_supplier(
    data: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_supplier_write_roles()),
):
    name = data.name.strip()
    existing = db.query(Supplier).filter(Supplier.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Supplier with this name already exists")
    values = data.model_dump(exclude={"email"})
    values["name"] = name
    values["email"] = str(data.email or "")
    supplier = Supplier(**values)
    try:
        db.add(supplier)
        db.flush()
        db.add(AuditLog(
            user_id=current_user.id,
            action="supplier_created",
            entity_type="supplier",
            entity_id=supplier.id,
            details=f"Created supplier {supplier.name}",
        ))
        db.commit()
        db.refresh(supplier)
    except Exception:
        db.rollback()
        raise
    return supplier


@router.put("/{supplier_id}", response_model=SupplierOut)
def update_supplier(
    supplier_id: int,
    data: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_supplier_write_roles()),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    updates = data.model_dump(exclude_unset=True)
    if "name" in updates:
        updates["name"] = updates["name"].strip()
        existing = db.query(Supplier).filter(Supplier.name == updates["name"], Supplier.id != supplier_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Supplier with this name already exists")
    if "email" in updates:
        updates["email"] = str(updates["email"] or "")
    was_active = supplier.is_active
    try:
        for key, value in updates.items():
            setattr(supplier, key, value)
        action = "supplier_deactivated" if was_active and supplier.is_active is False else "supplier_updated"
        db.add(AuditLog(
            user_id=current_user.id,
            action=action,
            entity_type="supplier",
            entity_id=supplier.id,
            details=(
                f"Deactivated supplier {supplier.name}"
                if action == "supplier_deactivated"
                else f"Updated supplier {supplier.name}"
            ),
        ))
        db.commit()
        db.refresh(supplier)
    except Exception:
        db.rollback()
        raise
    return supplier


@router.delete("/{supplier_id}", response_model=SupplierOut)
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_supplier_write_roles()),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    try:
        supplier.is_active = False
        db.add(AuditLog(
            user_id=current_user.id,
            action="supplier_deactivated",
            entity_type="supplier",
            entity_id=supplier.id,
            details=f"Deactivated supplier {supplier.name}",
        ))
        db.commit()
        db.refresh(supplier)
    except Exception:
        db.rollback()
        raise
    return supplier
