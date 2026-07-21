from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.audit.models import AuditLog
from app.auth.models import User
from app.core.config import settings
from app.core.deps import ensure_order_access, get_db, require_role
from app.orders.models import Order
from app.payments.models import Payment
from app.products.models import Product
from app.stock.models import IngredientStockMovement

router = APIRouter(prefix="/api/payments", tags=["Payments"])

PaymentMethod = Literal["cash", "card", "mobile"]


class PaymentCreate(BaseModel):
    order_id: int = Field(..., gt=0)
    amount: float = Field(..., gt=0, le=1_000_000)
    method: PaymentMethod = "cash"
    reference: str = Field(default="", max_length=100)


class PaymentOut(BaseModel):
    id: int
    order_id: int
    amount: float
    method: str
    status: str
    reference: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


@router.post("", response_model=PaymentOut)
def process_payment(
    data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_CASHIER)),
):
    order = db.query(Order).filter(Order.id == data.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    ensure_order_access(current_user, order)
    if order.status == "paid":
        raise HTTPException(status_code=400, detail="Commande deja payee")

    try:
        payment = Payment(
            order_id=data.order_id,
            amount=data.amount,
            method=data.method,
            reference=data.reference,
            status="completed",
        )
        db.add(payment)
        order.status = "paid"

        for item in order.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                product.stock_quantity = max(0, product.stock_quantity - item.quantity)
                for recipe_line in product.recipe:
                    consumption = recipe_line.quantity_needed * item.quantity
                    recipe_line.ingredient.current_stock = max(
                        0, recipe_line.ingredient.current_stock - consumption
                    )
                    db.add(IngredientStockMovement(
                        ingredient_id=recipe_line.ingredient_id,
                        quantity_change=-consumption,
                        reason="sale",
                        details=f"Order #{order.id}: {item.quantity}x {product.name}",
                        triggered_by=current_user.id,
                    ))

        if order.table_id:
            from app.orders.models import Table
            table = db.query(Table).filter(Table.id == order.table_id).first()
            if table:
                table.status = "available"

        db.add(AuditLog(
            user_id=current_user.id,
            action="payment",
            entity_type="payment",
            entity_id=payment.id,
            details=f"Payment of {data.amount} DT via {data.method} for order #{order.id}",
        ))
        db.commit()
        db.refresh(payment)
    except Exception:
        db.rollback()
        raise

    return PaymentOut.model_validate(payment)


@router.get("/{order_id}", response_model=list[PaymentOut])
def get_payments_for_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_CASHIER)),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    ensure_order_access(current_user, order)
    payments = db.query(Payment).filter(Payment.order_id == order_id).all()
    return [PaymentOut.model_validate(p) for p in payments]


@router.post("/{payment_id}/refund", response_model=PaymentOut)
def refund_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Paiement introuvable")
    if payment.status == "refunded":
        raise HTTPException(status_code=400, detail="Deja rembourse")

    order = db.query(Order).filter(Order.id == payment.order_id).first()
    if not order or order.status != "paid":
        raise HTTPException(status_code=400, detail="Commande non payee")

    try:
        payment.status = "refunded"

        for item in order.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                product.stock_quantity += item.quantity
                for recipe_line in product.recipe:
                    restoration = recipe_line.quantity_needed * item.quantity
                    recipe_line.ingredient.current_stock += restoration
                    db.add(IngredientStockMovement(
                        ingredient_id=recipe_line.ingredient_id,
                        quantity_change=+restoration,
                        reason="refund",
                        details=f"Refund #{payment.id}, Order #{order.id}: {item.quantity}x {product.name}",
                        triggered_by=current_user.id,
                    ))

        db.add(AuditLog(
            user_id=current_user.id,
            action="refund",
            entity_type="payment",
            entity_id=payment.id,
            details=f"Refund of {payment.amount} DT for order #{order.id}",
        ))
        db.commit()
        db.refresh(payment)
    except Exception:
        db.rollback()
        raise

    return PaymentOut.model_validate(payment)
