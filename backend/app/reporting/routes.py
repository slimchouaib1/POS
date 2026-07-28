from io import BytesIO
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
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
    return datetime.utcnow() - timedelta(days=_range_days(date_range, fallback_days))


def _range_days(date_range: str | None, fallback_days: int = 30) -> int:
    days_by_range = {
        "last_week": 7,
        "last_month": 30,
        "last_year": 365,
    }
    return days_by_range.get(date_range or "", fallback_days)


def _paid_order_query(db: Session, start_at: datetime | None = None, end_at: datetime | None = None):
    q = db.query(Order).filter(Order.status == "paid")
    if start_at is not None:
        q = q.filter(Order.created_at >= start_at)
    if end_at is not None:
        q = q.filter(Order.created_at <= end_at)
    return q


def _aggregate_orders(db: Session, start_at: datetime, end_at: datetime) -> dict:
    filters = [Order.status == "paid", Order.created_at >= start_at, Order.created_at <= end_at]
    total_orders = db.query(Order).filter(*filters).count()
    total_revenue = db.query(sqlfunc.sum(Order.total_amount)).filter(*filters).scalar() or 0
    unique_customers = db.query(sqlfunc.count(sqlfunc.distinct(Order.customer_id))).filter(
        *filters,
        Order.customer_id.isnot(None),
    ).scalar() or 0
    return {
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "avg_basket": round(total_revenue / total_orders, 2) if total_orders else 0,
        "customer_count": unique_customers,
    }


def _delta(current: float, previous: float) -> dict:
    change = current - previous
    pct = None if previous == 0 else round((change / previous) * 100, 2)
    return {"absolute": round(change, 2), "percent": pct}


def _sales_export_payload(db: Session, date_range: str | None, days: int):
    since = _range_start(date_range, days)
    orders = (
        _paid_order_query(db, start_at=since)
        .order_by(Order.created_at.desc(), Order.id.desc())
        .all()
    )
    daily = sales_report(period="daily", days=days, date_range=date_range, db=db, _=None)["data"]
    dashboard = dashboard_kpis(date_range=date_range or "last_month", db=db, _=None)
    rows = []
    for order in orders:
        subtotal = sum(item.subtotal for item in order.items)
        payment_methods = ", ".join(p.method for p in order.payments if p.status == "completed")
        rows.append({
            "order_id": order.id,
            "created_at": order.created_at,
            "table": f"Table {order.table.number}" if order.table else "Takeaway",
            "cashier": order.cashier_id,
            "payment_methods": payment_methods,
            "subtotal": round(subtotal, 2),
            "discount": round(order.discount_amount or 0, 2),
            "total": round(order.total_amount or 0, 2),
            "status": order.status,
        })
    return {"since": since, "orders": rows, "daily": daily, "dashboard": dashboard}


def _xlsx_col(index: int) -> str:
    letters = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def _xlsx_cell(value, row_index: int, col_index: int) -> str:
    ref = f"{_xlsx_col(col_index)}{row_index}"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{ref}"><v>{value}</v></c>'
    text = "" if value is None else str(value)
    return f'<c r="{ref}" t="inlineStr"><is><t>{escape(text)}</t></is></c>'


def _xlsx_sheet(rows: list[list]) -> str:
    body = []
    for row_index, row in enumerate(rows, start=1):
        cells = "".join(_xlsx_cell(value, row_index, col_index) for col_index, value in enumerate(row, start=1))
        body.append(f'<row r="{row_index}">{cells}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(body)}</sheetData>"
        "</worksheet>"
    )


def _xlsx_workbook(sheets: list[tuple[str, list[list]]]) -> BytesIO:
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            + "".join(
                f'<Override PartName="/xl/worksheets/sheet{index}.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                for index in range(1, len(sheets) + 1)
            )
            + "</Types>",
        )
        archive.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>",
        )
        archive.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            "<sheets>"
            + "".join(
                f'<sheet name="{escape(name)}" sheetId="{index}" r:id="rId{index}"/>'
                for index, (name, _) in enumerate(sheets, start=1)
            )
            + "</sheets></workbook>",
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + "".join(
                f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                f'Target="worksheets/sheet{index}.xml"/>'
                for index in range(1, len(sheets) + 1)
            )
            + "</Relationships>",
        )
        for index, (_, rows) in enumerate(sheets, start=1):
            archive.writestr(f"xl/worksheets/sheet{index}.xml", _xlsx_sheet(rows))
    output.seek(0)
    return output


def _pdf_escape(value) -> str:
    return str(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _simple_pdf(lines: list[str]) -> BytesIO:
    text_ops = ["BT", "/F1 16 Tf", "48 744 Td", f"({_pdf_escape(lines[0])}) Tj"]
    for line in lines[1:45]:
        text_ops.append("0 -16 Td")
        text_ops.append("/F1 9 Tf")
        text_ops.append(f"({_pdf_escape(line)}) Tj")
    text_ops.append("ET")
    stream = "\n".join(text_ops).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    output = BytesIO()
    output.write(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(output.tell())
        output.write(f"{index} 0 obj\n".encode("ascii"))
        output.write(obj)
        output.write(b"\nendobj\n")
    xref_offset = output.tell()
    output.write(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.write(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.write(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    output.seek(0)
    return output


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


@router.get("/dashboard/comparison")
def dashboard_period_comparison(
    date_range: str = Query(
        "last_month",
        alias="range",
        pattern="^(last_week|last_month|last_year)$",
    ),
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    anchor_end = db.query(sqlfunc.max(Order.created_at)).filter(Order.status == "paid").scalar()
    if not anchor_end:
        return {
            "range": date_range,
            "anchor": "latest_paid_order",
            "has_comparison": False,
            "message": "No paid orders available for comparison.",
        }

    days = _range_days(date_range)
    current_end = anchor_end
    current_start = current_end - timedelta(days=days)
    previous_end = current_start
    previous_start = previous_end - timedelta(days=days)
    current = _aggregate_orders(db, current_start, current_end)
    previous = _aggregate_orders(db, previous_start, previous_end)
    has_comparison = current["total_orders"] > 0 and previous["total_orders"] > 0

    return {
        "range": date_range,
        "anchor": "latest_paid_order",
        "has_comparison": has_comparison,
        "current_period": {
            "start": current_start.isoformat(),
            "end": current_end.isoformat(),
            **current,
        },
        "previous_period": {
            "start": previous_start.isoformat(),
            "end": previous_end.isoformat(),
            **previous,
        },
        "deltas": {
            "total_revenue": _delta(current["total_revenue"], previous["total_revenue"]),
            "total_orders": _delta(current["total_orders"], previous["total_orders"]),
            "avg_basket": _delta(current["avg_basket"], previous["avg_basket"]),
            "customer_count": _delta(current["customer_count"], previous["customer_count"]),
        },
        "message": "" if has_comparison else "Insufficient paid orders in one of the comparison windows.",
    }


@router.get("/sales/export/excel")
def export_sales_excel(
    date_range: Optional[str] = Query(
        "last_month",
        alias="range",
        pattern="^(last_week|last_month|last_year)$",
    ),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    payload = _sales_export_payload(db, date_range, days)
    summary_rows = [["Metric", "Value"]]
    for metric in ["range", "total_orders", "total_revenue", "avg_basket", "customer_count"]:
        summary_rows.append([metric, payload["dashboard"].get(metric)])
    summary_rows.append(["since", payload["since"].isoformat()])

    daily_rows = [["Date", "Orders", "Revenue"]]
    daily_rows.extend([row["date"], row["orders"], row["revenue"]] for row in payload["daily"])

    headers = ["Order ID", "Created At", "Table", "Cashier ID", "Payment Methods", "Subtotal", "Discount", "Total", "Status"]
    order_rows = [headers]
    for row in payload["orders"]:
        order_rows.append([
            row["order_id"],
            row["created_at"].isoformat() if row["created_at"] else "",
            row["table"],
            row["cashier"],
            row["payment_methods"],
            row["subtotal"],
            row["discount"],
            row["total"],
            row["status"],
        ])

    output = _xlsx_workbook([
        ("Summary", summary_rows),
        ("Daily Revenue", daily_rows),
        ("Paid Orders", order_rows),
    ])
    filename = f"sales_report_{date_range or 'custom'}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/sales/export/pdf")
def export_sales_pdf(
    date_range: Optional[str] = Query(
        "last_month",
        alias="range",
        pattern="^(last_week|last_month|last_year)$",
    ),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    _=Depends(require_role(settings.ROLE_ADMIN, settings.ROLE_MANAGER)),
):
    payload = _sales_export_payload(db, date_range, days)
    lines = [
        "Sales Report",
        f"Range: {date_range} | Since: {payload['since'].date().isoformat()}",
    ]
    for label, key in [
        ("Total orders", "total_orders"),
        ("Total revenue", "total_revenue"),
        ("Average basket", "avg_basket"),
        ("Customer count", "customer_count"),
    ]:
        lines.append(f"{label}: {payload['dashboard'].get(key)}")
    lines.append("")
    lines.append("Recent Paid Orders")
    for row in payload["orders"][:35]:
        created = row["created_at"].strftime("%Y-%m-%d %H:%M") if row["created_at"] else ""
        lines.append(f"#{row['order_id']}  {created}  total={row['total']:.2f} DT  payment={row['payment_methods'] or 'n/a'}")

    output = _simple_pdf(lines)
    filename = f"sales_report_{date_range or 'custom'}.pdf"
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
