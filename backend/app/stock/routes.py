from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
from datetime import datetime

from app.core.deps import get_db, get_current_user, require_role
from app.core.config import settings
from app.stock.models import StockMovement, IngredientStockMovement
from app.products.models import Product, Ingredient
from app.auth.models import User
from app.audit.models import AuditLog

router = APIRouter(prefix="/api/stock", tags=["Stock"])


class StockOverviewItem(BaseModel):
    product_id: int
    product_name: str
    category_name: str
    section: str
    stock_quantity: int
    low_stock_threshold: int
    is_low_stock: bool

class StockAdjust(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity_change: int = Field(..., ge=-1_000_000, le=1_000_000)
    reason: Literal["adjustment", "restock", "waste", "correction", "sale", "refund"] = "adjustment"
    details: str = Field(default="", max_length=500)

    @field_validator("quantity_change")
    @classmethod
    def reject_zero_quantity(cls, value: int) -> int:
        if value == 0:
            raise ValueError("quantity_change cannot be zero")
        return value


class StockMovementOut(BaseModel):
    id: int
    product_id: int
    product_name: str = ""
    quantity_change: int
    reason: str
    details: str
    triggered_by: Optional[int]
    triggered_by_name: str = ""
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IngredientStockOverviewItem(BaseModel):
    ingredient_id: int
    name: str
    unit: str
    category: str
    current_stock: float
    low_stock_threshold: float
    cost_per_unit: float
    supplier: str
    is_low_stock: bool


class IngredientStockAdjust(BaseModel):
    ingredient_id: int = Field(..., gt=0)
    quantity_change: float = Field(..., ge=-1_000_000, le=1_000_000)
    reason: Literal["adjustment", "restock", "waste", "correction", "sale", "refund"] = "adjustment"
    details: str = Field(default="", max_length=500)

    @field_validator("quantity_change")
    @classmethod
    def reject_zero_quantity(cls, value: float) -> float:
        if value == 0:
            raise ValueError("quantity_change cannot be zero")
        return value


class IngredientStockMovementOut(BaseModel):
    id: int
    ingredient_id: int
    ingredient_name: str = ""
    quantity_change: float
    reason: str
    details: str
    triggered_by: Optional[int]
    triggered_by_name: str = ""
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


@router.get("", response_model=list[StockOverviewItem])
def stock_overview(
    low_only: bool = Query(False),
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_STOCK_MANAGER)),
):
    q = db.query(Product)
    products = q.order_by(Product.name).all()
    result = []
    for p in products:
        is_low = p.stock_quantity <= p.low_stock_threshold
        if low_only and not is_low:
            continue
        result.append(StockOverviewItem(
            product_id=p.id,
            product_name=p.name,
            category_name=p.category.name if p.category else "",
            section=p.section,
            stock_quantity=p.stock_quantity,
            low_stock_threshold=p.low_stock_threshold,
            is_low_stock=is_low,
        ))
    return result


@router.get("/alerts", response_model=list[StockOverviewItem])
def low_stock_alerts(
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_STOCK_MANAGER)),
):
    products = db.query(Product).all()
    alerts = []
    for p in products:
        if p.stock_quantity <= p.low_stock_threshold:
            alerts.append(StockOverviewItem(
                product_id=p.id,
                product_name=p.name,
                category_name=p.category.name if p.category else "",
                section=p.section,
                stock_quantity=p.stock_quantity,
                low_stock_threshold=p.low_stock_threshold,
                is_low_stock=True,
            ))
    return alerts


@router.get("/movements", response_model=list[StockMovementOut])
def list_movements(
    product_id: Optional[int] = Query(None, gt=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_STOCK_MANAGER)),
):
    q = db.query(StockMovement)
    if product_id:
        if not db.query(Product).filter(Product.id == product_id).first():
            raise HTTPException(status_code=404, detail="Produit introuvable")
        q = q.filter(StockMovement.product_id == product_id)
    movements = q.order_by(StockMovement.created_at.desc()).limit(limit).all()
    result = []
    for m in movements:
        product = db.query(Product).filter(Product.id == m.product_id).first()
        user = db.query(User).filter(User.id == m.triggered_by).first() if m.triggered_by else None
        out = StockMovementOut.model_validate(m)
        out.product_name = product.name if product else ""
        out.triggered_by_name = user.full_name if user else ""
        result.append(out)
    return result


@router.post("/adjust", response_model=StockMovementOut)
def adjust_stock(
    data: StockAdjust,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_STOCK_MANAGER
    )),
):
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")

    product.stock_quantity = max(0, product.stock_quantity + data.quantity_change)

    movement = StockMovement(
        product_id=data.product_id,
        quantity_change=data.quantity_change,
        reason=data.reason,
        details=data.details,
        triggered_by=current_user.id,
    )
    db.add(movement)
    db.add(AuditLog(
        user_id=current_user.id,
        action="adjust_stock",
        entity_type="product",
        entity_id=product.id,
        details=f"Adjusted product stock by {data.quantity_change}; reason={data.reason}",
    ))
    db.commit()
    db.refresh(movement)

    out = StockMovementOut.model_validate(movement)
    out.product_name = product.name
    out.triggered_by_name = current_user.full_name
    return out


# ─── Ingredients ────────────────────────────────────────

@router.get("/ingredients", response_model=list[IngredientStockOverviewItem])
def ingredient_stock_overview(
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_STOCK_MANAGER)),
):
    ingredients = db.query(Ingredient).order_by(Ingredient.name).all()
    result = []
    for ing in ingredients:
        is_low = ing.current_stock <= ing.low_stock_threshold
        result.append(IngredientStockOverviewItem(
            ingredient_id=ing.id,
            name=ing.name,
            unit=ing.unit,
            category=ing.category,
            current_stock=ing.current_stock,
            low_stock_threshold=ing.low_stock_threshold,
            cost_per_unit=ing.cost_per_unit,
            supplier=ing.supplier,
            is_low_stock=is_low,
        ))
    return result


@router.post("/ingredients/adjust", response_model=IngredientStockMovementOut)
def adjust_ingredient_stock(
    data: IngredientStockAdjust,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_STOCK_MANAGER
    )),
):
    ingredient = db.query(Ingredient).filter(Ingredient.id == data.ingredient_id).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingrédient introuvable")

    try:
        ingredient.current_stock = max(0, ingredient.current_stock + data.quantity_change)

        movement = IngredientStockMovement(
            ingredient_id=data.ingredient_id,
            quantity_change=data.quantity_change,
            reason=data.reason,
            details=data.details,
            triggered_by=current_user.id,
        )
        db.add(movement)
        db.add(AuditLog(
            user_id=current_user.id,
            action="adjust_ingredient_stock",
            entity_type="ingredient",
            entity_id=ingredient.id,
            details=f"Adjusted ingredient stock by {data.quantity_change}; reason={data.reason}",
        ))
        db.commit()
        db.refresh(movement)
    except Exception:
        db.rollback()
        raise

    out = IngredientStockMovementOut.model_validate(movement)
    out.ingredient_name = ingredient.name
    out.triggered_by_name = current_user.full_name
    return out


@router.get("/ingredients/movements", response_model=list[IngredientStockMovementOut])
def list_ingredient_movements(
    ingredient_id: Optional[int] = Query(None, gt=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_STOCK_MANAGER)),
):
    q = db.query(IngredientStockMovement)
    if ingredient_id:
        if not db.query(Ingredient).filter(Ingredient.id == ingredient_id).first():
            raise HTTPException(status_code=404, detail="Ingrédient introuvable")
        q = q.filter(IngredientStockMovement.ingredient_id == ingredient_id)
    movements = q.order_by(IngredientStockMovement.created_at.desc()).limit(limit).all()
    
    result = []
    for m in movements:
        ingredient = db.query(Ingredient).filter(Ingredient.id == m.ingredient_id).first()
        user = db.query(User).filter(User.id == m.triggered_by).first() if m.triggered_by else None
        out = IngredientStockMovementOut.model_validate(m)
        out.ingredient_name = ingredient.name if ingredient else ""
        out.triggered_by_name = user.full_name if user else ""
        result.append(out)
    return result
