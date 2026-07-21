from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.deps import ensure_order_access, get_db, get_current_user, is_order_elevated_user, require_role
from app.core.config import settings
from app.orders.models import Table, Order, OrderItem
from app.orders.schemas import (
    TableOut, OrderCreate, OrderUpdate, OrderOut, OrderItemOut, OrderStatus, TableStatus,
)
from app.products.models import Product
from app.customers.models import Customer
from app.auth.models import User
from app.stock.models import IngredientStockMovement
from app.audit.models import AuditLog

router = APIRouter(prefix="/api", tags=["Orders & Tables"])


# ─── Tables ─────────────────────────────────────────
@router.get("/tables", response_model=list[TableOut])
def list_tables(
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_CASHIER)),
):
    return db.query(Table).order_by(Table.number).all()


@router.put("/tables/{table_id}/status")
def update_table_status(
    table_id: int,
    status: TableStatus = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_CASHIER)),
):
    table = db.query(Table).filter(Table.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Table introuvable")
    table.status = status
    db.add(AuditLog(
        user_id=current_user.id,
        action="update_table_status",
        entity_type="table",
        entity_id=table.id,
        details=f"Table {table.number} status set to {status}",
    ))
    db.commit()
    return {"detail": "Statut mis à jour", "status": status}


# ─── Orders ─────────────────────────────────────────
def _build_order_out(order: Order, db: Session) -> OrderOut:
    cashier = db.query(User).filter(User.id == order.cashier_id).first()
    items_out = []
    for item in order.items:
        items_out.append(OrderItemOut.model_validate(item))
    out = OrderOut(
        id=order.id,
        table_id=order.table_id,
        table_number=order.table.number if order.table else None,
        customer_id=order.customer_id,
        cashier_id=order.cashier_id,
        cashier_name=cashier.full_name if cashier else "",
        status=order.status,
        total_amount=order.total_amount,
        discount_pct=order.discount_pct,
        discount_amount=order.discount_amount,
        notes=order.notes or "",
        cancel_reason=order.cancel_reason or "",
        items=items_out,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )
    return out


def _recalculate_order(order: Order):
    subtotal = sum(item.subtotal for item in order.items)
    order.discount_amount = round(subtotal * (order.discount_pct / 100), 2)
    order.total_amount = round(subtotal - order.discount_amount, 2)


@router.get("/orders", response_model=list[OrderOut])
def list_orders(
    status: Optional[OrderStatus] = Query(None),
    table_id: Optional[int] = Query(None, gt=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_CASHIER)),
):
    q = db.query(Order)
    if not is_order_elevated_user(current_user):
        q = q.filter(Order.cashier_id == current_user.id)
    if status:
        q = q.filter(Order.status == status)
    if table_id:
        q = q.filter(Order.table_id == table_id)
    orders = q.order_by(Order.created_at.desc()).limit(limit).all()
    return [_build_order_out(o, db) for o in orders]


@router.post("/orders", response_model=OrderOut)
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_CASHIER)),
):
    if data.table_id and not db.query(Table).filter(Table.id == data.table_id).first():
        raise HTTPException(status_code=404, detail="Table introuvable")
    if data.customer_id and not db.query(Customer).filter(Customer.id == data.customer_id).first():
        raise HTTPException(status_code=404, detail="Client introuvable")

    order = Order(
        table_id=data.table_id,
        customer_id=data.customer_id,
        cashier_id=current_user.id,
        status="draft",
        notes=data.notes,
        discount_pct=data.discount_pct,
    )
    db.add(order)
    db.flush()

    # Add items
    for item_data in data.items:
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        if not product:
            raise HTTPException(status_code=400, detail=f"Produit {item_data.product_id} introuvable")
        unit_price = product.price
        subtotal = round(unit_price * item_data.quantity * (1 - item_data.discount_pct / 100), 2)
        oi = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            quantity=item_data.quantity,
            unit_price=unit_price,
            discount_pct=item_data.discount_pct,
            subtotal=subtotal,
            notes=item_data.notes,
        )
        db.add(oi)

    db.flush()
    db.refresh(order)
    _recalculate_order(order)

    # Mark table as occupied
    if order.table_id:
        table = db.query(Table).filter(Table.id == order.table_id).first()
        if table:
            table.status = "occupied"

    db.add(AuditLog(
        user_id=current_user.id, action="create_order", entity_type="order",
        entity_id=order.id, details=f"Created order #{order.id} with {len(data.items)} items, total {order.total_amount} DT",
    ))
    db.commit()
    db.refresh(order)
    return _build_order_out(order, db)


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_CASHIER)),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    ensure_order_access(current_user, order)
    return _build_order_out(order, db)


@router.put("/orders/{order_id}", response_model=OrderOut)
def update_order(
    order_id: int,
    data: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_CASHIER)),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    ensure_order_access(current_user, order)
    if order.status in ("paid", "cancelled"):
        raise HTTPException(status_code=400, detail="Commande déjà finalisée")

    if data.notes is not None:
        order.notes = data.notes
    if data.discount_pct is not None:
        order.discount_pct = data.discount_pct
    if data.table_id is not None:
        if not db.query(Table).filter(Table.id == data.table_id).first():
            raise HTTPException(status_code=404, detail="Table introuvable")
        order.table_id = data.table_id
    if data.customer_id is not None:
        if not db.query(Customer).filter(Customer.id == data.customer_id).first():
            raise HTTPException(status_code=404, detail="Client introuvable")
        order.customer_id = data.customer_id

    if data.items is not None:
        # Replace all items
        for old_item in order.items:
            db.delete(old_item)
        db.flush()
        for item_data in data.items:
            product = db.query(Product).filter(Product.id == item_data.product_id).first()
            if not product:
                raise HTTPException(status_code=400, detail=f"Produit {item_data.product_id} introuvable")
            subtotal = round(product.price * item_data.quantity * (1 - item_data.discount_pct / 100), 2)
            oi = OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                quantity=item_data.quantity,
                unit_price=product.price,
                discount_pct=item_data.discount_pct,
                subtotal=subtotal,
                notes=item_data.notes,
            )
            db.add(oi)
        db.flush()
        db.refresh(order)

    _recalculate_order(order)
    db.add(AuditLog(
        user_id=current_user.id,
        action="update_order",
        entity_type="order",
        entity_id=order.id,
        details=f"Updated order #{order.id}",
    ))
    db.commit()
    db.refresh(order)
    return _build_order_out(order, db)


@router.patch("/orders/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: int,
    status: OrderStatus = Query(...),
    cancel_reason: str = Query("", max_length=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER, settings.ROLE_CASHIER)),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    ensure_order_access(current_user, order)

    old_status = order.status  # capture before mutation for double-deduction guard

    valid_transitions = {
        "draft": ["in_progress", "cancelled"],
        "in_progress": ["served", "cancelled"],
        "served": ["paid", "cancelled"],
        "paid": [],
        "cancelled": [],
    }
    if status not in valid_transitions.get(order.status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Transition invalide: {order.status} → {status}",
        )

    try:
        order.status = status

        if status == "cancelled":
            order.cancel_reason = cancel_reason
            # Free table
            if order.table_id:
                table = db.query(Table).filter(Table.id == order.table_id).first()
                if table:
                    table.status = "available"

        if status == "paid" and old_status != "paid":
            # Deduct product stock + consume ingredients via recipe
            for item in order.items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                if product:
                    product.stock_quantity = max(0, product.stock_quantity - item.quantity)
                    # Consume ingredients
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
            # Free table
            if order.table_id:
                table = db.query(Table).filter(Table.id == order.table_id).first()
                if table:
                    table.status = "available"

        db.add(AuditLog(
            user_id=current_user.id, action=f"order_{status}", entity_type="order",
            entity_id=order.id, details=f"Order #{order.id} status changed: {old_status} → {status}" + (f" Reason: {cancel_reason}" if cancel_reason else ""),
        ))
        db.commit()
        db.refresh(order)
    except Exception:
        db.rollback()
        raise

    return _build_order_out(order, db)
