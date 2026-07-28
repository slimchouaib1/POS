from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc
from datetime import datetime, timedelta
from typing import Optional

from app.core.deps import get_db, require_role
from app.core.config import settings
from app.orders.models import Order, OrderItem
from app.payments.models import Payment
from app.products.models import Product
from app.customers.models import Customer

router = APIRouter(prefix="/api/reports", tags=["Reporting"])


def _range_start(date_range: str | None, fallback_days: int = 30) -> datetime:
    days_by_range = {
        "last_week": 7,
        "last_month": 30,
        "last_year": 365,
    }
    return datetime.utcnow() - timedelta(days=days_by_range.get(date_range or "", fallback_days))


@router.get("/dashboard")
def dashboard_kpis(
    date_range: Optional[str] = Query(
        "last_week",
        alias="range",
        pattern="^(last_week|last_month|last_year)$",
    ),
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    today = datetime.utcnow().date()
    since = _range_start(date_range)

    paid_order_filters = [Order.status == "paid", Order.created_at >= since]

    # Total orders & revenue for selected range
    total_orders = db.query(Order).filter(*paid_order_filters).count()
    total_revenue = db.query(sqlfunc.sum(Order.total_amount)).filter(*paid_order_filters).scalar() or 0

    # Today's metrics
    today_orders = db.query(Order).filter(
        Order.status == "paid",
        sqlfunc.date(Order.created_at) == today,
    ).count()
    today_revenue = db.query(sqlfunc.sum(Order.total_amount)).filter(
        Order.status == "paid",
        sqlfunc.date(Order.created_at) == today,
    ).scalar() or 0

    # Average basket
    avg_basket = round(total_revenue / max(total_orders, 1), 2)

    # Total customers
    customer_count = db.query(Customer).count()

    # Top 10 products by quantity sold
    top_products = (
        db.query(
            OrderItem.product_name,
            sqlfunc.sum(OrderItem.quantity).label("total_qty"),
            sqlfunc.sum(OrderItem.subtotal).label("total_revenue"),
        )
        .join(Order)
        .filter(*paid_order_filters)
        .group_by(OrderItem.product_name)
        .order_by(sqlfunc.sum(OrderItem.quantity).desc())
        .limit(10)
        .all()
    )

    # Active orders (not paid/cancelled)
    active_orders = db.query(Order).filter(
        Order.status.in_(["draft", "in_progress", "served"])
    ).count()

    # Low stock count
    low_stock = db.query(Product).filter(
        Product.stock_quantity <= Product.low_stock_threshold
    ).count()

    # Payment methods breakdown
    payment_methods = (
        db.query(
            Payment.method,
            sqlfunc.count(Payment.id).label("count"),
            sqlfunc.sum(Payment.amount).label("total"),
        )
        .join(Order)
        .filter(Payment.status == "completed", Order.created_at >= since)
        .group_by(Payment.method)
        .all()
    )

    return {
        "range": date_range,
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "customer_count": customer_count,
        "today_orders": today_orders,
        "today_revenue": round(today_revenue, 2),
        "avg_basket": avg_basket,
        "active_orders": active_orders,
        "low_stock_count": low_stock,
        "top_products": [
            {"name": p[0], "quantity": p[1], "revenue": round(p[2], 2)}
            for p in top_products
        ],
        "payment_methods": [
            {"method": pm[0], "count": pm[1], "total": round(pm[2], 2)}
            for pm in payment_methods
        ],
    }


@router.get("/sales")
def sales_report(
    period: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    days: int = Query(30, ge=1, le=365),
    date_range: Optional[str] = Query(
        None,
        alias="range",
        pattern="^(last_week|last_month|last_year)$",
    ),
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    since = _range_start(date_range, days)
    orders = (
        db.query(Order)
        .filter(Order.status == "paid", Order.created_at >= since)
        .order_by(Order.created_at)
        .all()
    )

    # Group by date
    from collections import defaultdict
    daily = defaultdict(lambda: {"orders": 0, "revenue": 0.0})
    for o in orders:
        day_key = o.created_at.strftime("%Y-%m-%d") if o.created_at else "unknown"
        daily[day_key]["orders"] += 1
        daily[day_key]["revenue"] += o.total_amount

    return {
        "period": period,
        "data": [
            {"date": k, "orders": v["orders"], "revenue": round(v["revenue"], 2)}
            for k, v in sorted(daily.items())
        ],
    }


@router.get("/products")
def product_performance(
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    results = (
        db.query(
            OrderItem.product_id,
            OrderItem.product_name,
            sqlfunc.sum(OrderItem.quantity).label("total_qty"),
            sqlfunc.sum(OrderItem.subtotal).label("total_revenue"),
            sqlfunc.count(OrderItem.id).label("order_count"),
        )
        .join(Order)
        .filter(Order.status == "paid")
        .group_by(OrderItem.product_id, OrderItem.product_name)
        .order_by(sqlfunc.sum(OrderItem.subtotal).desc())
        .all()
    )

    return [
        {
            "product_id": r[0],
            "product_name": r[1],
            "total_quantity": r[2],
            "total_revenue": round(r[3], 2),
            "order_count": r[4],
        }
        for r in results
    ]
