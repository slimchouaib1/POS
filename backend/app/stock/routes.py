from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
from datetime import datetime

from app.core.deps import get_db, get_current_user, require_role
from app.core.config import settings
from app.stock.models import StockMovement, IngredientStockMovement, PurchaseOrder
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


class PurchaseOrderCreate(BaseModel):
    ingredient_id: int = Field(..., gt=0)
    quantity_ordered: float = Field(..., gt=0, le=1_000_000)


class PurchaseOrderOut(BaseModel):
    id: int
    ingredient_id: int
    ingredient_name: str = ""
    unit: str = ""
    quantity_ordered: float
    status: Literal["pending", "received", "cancelled"]
    created_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    created_by: Optional[int]
    created_by_name: str = ""

    class Config:
        from_attributes = True


def _purchase_order_out(po: PurchaseOrder, db: Session) -> PurchaseOrderOut:
    ingredient = db.query(Ingredient).filter(Ingredient.id == po.ingredient_id).first()
    creator = db.query(User).filter(User.id == po.created_by).first() if po.created_by else None
    out = PurchaseOrderOut.model_validate(po)
    out.ingredient_name = ingredient.name if ingredient else ""
    out.unit = ingredient.unit if ingredient else ""
    out.created_by_name = creator.full_name if creator else ""
    return out


def _apply_ingredient_stock_change(
    db: Session,
    ingredient: Ingredient,
    quantity_change: float,
    reason: str,
    details: str,
    user: User,
) -> IngredientStockMovement:
    ingredient.current_stock = max(0, ingredient.current_stock + quantity_change)
    movement = IngredientStockMovement(
        ingredient_id=ingredient.id,
        quantity_change=quantity_change,
        reason=reason,
        details=details,
        triggered_by=user.id,
    )
    db.add(movement)
    return movement


def _stock_audit_action(reason: str) -> str:
    if reason == "restock":
        return "stock_restocked"
    if reason == "waste":
        return "stock_wasted"
    return "stock_adjusted"


@router.get("", response_model=list[StockOverviewItem])
def stock_overview(
    low_only: bool = Query(False),
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_STOCK_MANAGER)),
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
    _=Depends(require_role(settings.ROLE_STOCK_MANAGER)),
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
    _=Depends(require_role(settings.ROLE_STOCK_MANAGER)),
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
        action=_stock_audit_action(data.reason),
        entity_type="product",
        entity_id=product.id,
        details=f"Product {product.name} stock changed by {data.quantity_change}; reason={data.reason}",
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
    _=Depends(require_role(settings.ROLE_STOCK_MANAGER)),
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
        movement = _apply_ingredient_stock_change(
            db=db,
            ingredient=ingredient,
            quantity_change=data.quantity_change,
            reason=data.reason,
            details=data.details,
            user=current_user,
        )
        db.add(AuditLog(
            user_id=current_user.id,
            action=_stock_audit_action(data.reason),
            entity_type="ingredient",
            entity_id=ingredient.id,
            details=f"Ingredient {ingredient.name} stock changed by {data.quantity_change}; reason={data.reason}",
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
    _=Depends(require_role(settings.ROLE_STOCK_MANAGER)),
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


@router.post("/purchase-orders", response_model=PurchaseOrderOut)
def create_purchase_order(
    data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_STOCK_MANAGER
    )),
):
    ingredient = db.query(Ingredient).filter(Ingredient.id == data.ingredient_id).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    try:
        po = PurchaseOrder(
            ingredient_id=ingredient.id,
            quantity_ordered=data.quantity_ordered,
            status="pending",
            created_by=current_user.id,
        )
        db.add(po)
        db.flush()
        db.add(AuditLog(
            user_id=current_user.id,
            action="po_created",
            entity_type="purchase_order",
            entity_id=po.id,
            details=(
                f"Created purchase order #{po.id} for {data.quantity_ordered} "
                f"{ingredient.unit} of {ingredient.name}; supplier={ingredient.supplier}"
            ),
        ))
        db.commit()
        db.refresh(po)
    except Exception:
        db.rollback()
        raise

    return _purchase_order_out(po, db)


@router.get("/purchase-orders", response_model=list[PurchaseOrderOut])
def list_purchase_orders(
    status: Optional[Literal["pending", "received", "cancelled"]] = Query(None),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_STOCK_MANAGER)),
):
    q = db.query(PurchaseOrder)
    if status:
        q = q.filter(PurchaseOrder.status == status)
    orders = q.order_by(PurchaseOrder.created_at.desc(), PurchaseOrder.id.desc()).limit(limit).all()
    return [_purchase_order_out(po, db) for po in orders]


@router.post("/purchase-orders/{purchase_order_id}/receive", response_model=PurchaseOrderOut)
def receive_purchase_order(
    purchase_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_STOCK_MANAGER
    )),
):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == purchase_order_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if po.status != "pending":
        raise HTTPException(status_code=400, detail="Only pending purchase orders can be received")

    ingredient = db.query(Ingredient).filter(Ingredient.id == po.ingredient_id).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    try:
        po.status = "received"
        po.received_at = datetime.utcnow()
        movement = _apply_ingredient_stock_change(
            db=db,
            ingredient=ingredient,
            quantity_change=po.quantity_ordered,
            reason="restock",
            details=f"Purchase order #{po.id} received",
            user=current_user,
        )
        db.flush()
        db.add(AuditLog(
            user_id=current_user.id,
            action="po_received",
            entity_type="purchase_order",
            entity_id=po.id,
            details=(
                f"Received purchase order #{po.id}; added {po.quantity_ordered} "
                f"{ingredient.unit} to {ingredient.name}; supplier={ingredient.supplier}; "
                f"stock incremented; movement_id={movement.id}"
            ),
        ))
        db.commit()
        db.refresh(po)
    except Exception:
        db.rollback()
        raise

    return _purchase_order_out(po, db)


@router.post("/purchase-orders/{purchase_order_id}/cancel", response_model=PurchaseOrderOut)
def cancel_purchase_order(
    purchase_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_STOCK_MANAGER
    )),
):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == purchase_order_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if po.status != "pending":
        raise HTTPException(status_code=400, detail="Only pending purchase orders can be cancelled")
    ingredient = db.query(Ingredient).filter(Ingredient.id == po.ingredient_id).first()

    try:
        po.status = "cancelled"
        db.add(AuditLog(
            user_id=current_user.id,
            action="po_cancelled",
            entity_type="purchase_order",
            entity_id=po.id,
            details=f"Cancelled purchase order #{po.id}; supplier={ingredient.supplier if ingredient else ''}",
        ))
        db.commit()
        db.refresh(po)
    except Exception:
        db.rollback()
        raise

    return _purchase_order_out(po, db)
