"""
AI Anomaly Detection Service
Loads real anomaly alerts from Notebooks Module 3 and serves them.
"""
import json
import pickle
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.ai.anomalies.models import AnomalyAlert
from app.core.config import settings
from app.customers.models import Customer
from app.orders.models import Order
from app.payments.models import Payment
from app.products.models import Product

_alerts_df = None
_full_df = None
_metadata = None
_live_model = None
_live_preprocessor = None
_live_schema = None
_live_metadata = None

LIVE_MODEL_NAME = "Random Forest Live"
HIGH_DISCOUNT_ALERT_RATE = 0.70


def _candidate_ai_roots() -> list[Path]:
    configured = Path(settings.NOTEBOOKS_PATH)
    roots = [
        configured,
        Path("Ai models"),
        Path("backend") / "Ai models",
        Path(__file__).resolve().parents[3] / "Ai models",
    ]

    unique_roots = []
    for root in roots:
        if root not in unique_roots:
            unique_roots.append(root)
    return unique_roots


def _candidate_export_paths(filename: str) -> list[Path]:
    candidates = []
    for root in _candidate_ai_roots():
        candidates.extend([
            root / "Module 3" / "Final" / "exports" / filename,
            root / "data" / "processed" / "Module 3" / filename,
            root / "data" / "final" / "Module 3" / filename,
        ])
    return candidates


def _first_existing_export(filename: str) -> Path | None:
    for path in _candidate_export_paths(filename):
        if path.exists():
            return path
    return None


def _candidate_model_paths(filename: str) -> list[Path]:
    return [root / "models" / "Module 3" / filename for root in _candidate_ai_roots()]


def _first_existing_model(filename: str) -> Path | None:
    for path in _candidate_model_paths(filename):
        if path.exists():
            return path
    return None


def _load_data():
    global _alerts_df, _full_df, _metadata

    if _alerts_df is not None:
        return

    # Load alerts (dashboard summary)
    alerts_path = _first_existing_export("final_anomaly_alerts_dashboard.csv")
    if alerts_path and alerts_path.exists():
        _alerts_df = pd.read_csv(alerts_path)
    else:
        _alerts_df = pd.DataFrame()

    # Load full alerts (with all features for order details)
    full_path = _first_existing_export("final_anomaly_alerts_full.csv")
    if full_path and full_path.exists():
        _full_df = pd.read_csv(full_path)
    else:
        _full_df = pd.DataFrame()

    # Load metadata
    meta_path = _first_existing_export("final_anomaly_module_metadata.json")
    if meta_path and meta_path.exists():
        with open(meta_path, "r") as f:
            _metadata = json.load(f)
    else:
        _metadata = {}


def get_alerts_data() -> list[dict]:
    """Return all real alerts as dicts for seeding into DB."""
    _load_data()
    if _alerts_df is None or _alerts_df.empty:
        return []

    alerts = []
    for _, row in _alerts_df.iterrows():
        score = float(row.get("anomaly_score", row.get("risk_score", 0)))

        # Determine risk level from score using real thresholds
        critical = float(_metadata.get("critical_threshold", 0.9724)) if _metadata else 0.9724
        decision = float(_metadata.get("decision_threshold", 0.2545)) if _metadata else 0.2545

        if score >= critical:
            risk_level = "CRITIQUE"
        elif score >= decision:
            risk_level = "ALERTE"
        else:
            risk_level = "NORMAL"

        alerts.append({
            "order_id": str(row.get("order_id", "")),
            "risk_score": round(score, 4),
            "risk_level": risk_level,
            "predicted_label": int(row.get("predicted_label", row.get("is_anomaly", 0))),
            "anomaly_type": str(row.get("anomaly_type", row.get("type", ""))),
            "reason_codes": str(row.get("reason_codes", row.get("features", ""))),
            "alert_explanation": str(row.get("alert_explanation", row.get("explanation", "Transaction signalée par le modèle Random Forest"))),
            "model_name": "Random Forest",
        })

    return alerts


def get_metadata() -> dict:
    """Return model metadata."""
    _load_data()
    if not _metadata:
        return {"model": "Random Forest", "thresholds": {}}

    # The exported JSON uses flat keys, not nested ones
    return {
        "model": _metadata.get("final_model", _metadata.get("model_name", "Random Forest")),
        "accuracy": _metadata.get("accuracy"),
        "f1_score": _metadata.get("f1"),
        "precision": _metadata.get("precision"),
        "recall": _metadata.get("recall"),
        "pr_auc": _metadata.get("pr_auc"),
        "thresholds": {
            "decision_threshold": _metadata.get("decision_threshold"),
            "critical_threshold": _metadata.get("critical_threshold"),
        },
        "risk_levels": _metadata.get("risk_levels", {}),
        "total_alerts": _metadata.get("alert_count", len(_alerts_df) if _alerts_df is not None else 0),
        "alert_rate": _metadata.get("alert_rate"),
        "false_alerts": _metadata.get("false_alerts"),
        "missed_anomalies": _metadata.get("missed_anomalies"),
    }


def _safe(val):
    """Convert NaN/NaT and numpy types to JSON-safe Python types."""
    if pd.isna(val):
        return None
    import numpy as np
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        return float(val)
    if isinstance(val, (np.bool_,)):
        return bool(val)
    return val


def get_order_details(order_id: str) -> dict | None:
    """Look up full order details from the enriched CSV by order_id."""
    _load_data()
    if _full_df is None or _full_df.empty:
        return None

    matches = _full_df[_full_df["order_id"].astype(str) == str(order_id)]
    if matches.empty:
        return None

    row = matches.iloc[0]

    return {
        # ── Core order info ──
        "order_id": str(row.get("order_id", "")),
        "order_datetime": _safe(row.get("order_datetime")),
        "order_date": _safe(row.get("order_date")),
        "order_time": _safe(row.get("order_time")),
        "cashier_id": _safe(row.get("cashier_id")),
        "customer_id": _safe(row.get("customer_id")),
        "total_amount": _safe(row.get("total_amount")),
        "payment_method": _safe(row.get("payment_method")),
        "table_number": _safe(row.get("table_number")),
        "restaurant_type": _safe(row.get("restaurant_type")),
        "main_category": _safe(row.get("main_category")),

        # ── Basket details ──
        "basket_size": _safe(row.get("basket_size")),
        "n_unique_items": _safe(row.get("n_unique_items")),
        "n_unique_categories": _safe(row.get("n_unique_categories")),
        "avg_line_total": _safe(row.get("avg_line_total")),
        "max_line_total": _safe(row.get("max_line_total")),
        "min_line_total": _safe(row.get("min_line_total")),
        "avg_item_price": _safe(row.get("avg_item_price")),
        "max_item_price": _safe(row.get("max_item_price")),
        "min_item_price": _safe(row.get("min_item_price")),
        "avg_amount_per_item": _safe(row.get("avg_amount_per_item")),
        "unique_item_ratio": _safe(row.get("unique_item_ratio")),

        # ── Discount info ──
        "has_discount": bool(row.get("has_discount_order", 0)),
        "mean_discount_rate": _safe(row.get("mean_discount_rate")),
        "max_discount_rate": _safe(row.get("max_discount_rate")),
        "discount_line_count": _safe(row.get("discount_line_count")),
        "discount_line_rate": _safe(row.get("discount_line_rate")),
        "estimated_discount_amount": _safe(row.get("estimated_discount_amount")),

        # ── Void info ──
        "is_voided_order": bool(row.get("is_voided_order", False)),
        "void_line_count": _safe(row.get("void_line_count")),
        "void_line_rate": _safe(row.get("void_line_rate")),

        # ── Price deviation ──
        "mean_price_deviation_pct": _safe(row.get("mean_price_deviation_pct")),
        "max_abs_price_deviation_pct": _safe(row.get("max_abs_price_deviation_pct")),

        # ── Timing ──
        "order_hour": _safe(row.get("order_hour")),
        "order_dayofweek": _safe(row.get("order_dayofweek")),
        "is_weekend": bool(row.get("is_weekend", 0)),
        "cashier_shift": _safe(row.get("cashier_shift")),

        # ── Cashier stats ──
        "cashier_total_orders": _safe(row.get("cashier_total_orders")),
        "cashier_avg_order_amount": _safe(row.get("cashier_avg_order_amount")),
        "cashier_void_rate": _safe(row.get("cashier_void_rate")),
        "cashier_discount_order_rate": _safe(row.get("cashier_discount_order_rate")),
        "cashier_amount_zscore": _safe(row.get("cashier_amount_zscore")),
        "cashier_flagged": bool(row.get("cashier_flagged", 0)),

        # ── Customer stats ──
        "customer_total_orders": _safe(row.get("customer_total_orders")),
        "customer_avg_order_amount": _safe(row.get("customer_avg_order_amount")),
        "customer_avg_basket_size": _safe(row.get("customer_avg_basket_size")),
        "customer_amount_zscore": _safe(row.get("customer_amount_zscore")),
        "archetype": _safe(row.get("archetype")),
        "price_tier": _safe(row.get("price_tier")),

        # ── Anomaly info ──
        "anomaly_score": _safe(row.get("anomaly_score")),
        "anomaly_type": _safe(row.get("anomaly_type")),
        "risk_level": _safe(row.get("risk_level")),
        "alert_explanation": _safe(row.get("alert_explanation")),
        "anomaly_description": _safe(row.get("anomaly_description")),
    }



def _load_live_artifacts() -> bool:
    """Lazy-load the trained supervised anomaly artifacts for online scoring."""
    global _live_model, _live_preprocessor, _live_schema, _live_metadata

    if _live_model is not None and _live_preprocessor is not None and _live_schema is not None:
        return True

    model_path = _first_existing_model("final_anomaly_model.pkl") or _first_existing_model("best_supervised_model.pkl")
    preprocessor_path = _first_existing_model("final_anomaly_preprocessor.pkl") or _first_existing_model("supervised_preprocessor.pkl")
    schema_path = _first_existing_export("anomaly_feature_schema.json")
    metadata_path = _first_existing_export("final_anomaly_module_metadata.json") or _first_existing_export("final_supervised_model_metadata.json")

    if not model_path or not preprocessor_path or not schema_path:
        return False

    with open(model_path, "rb") as f:
        _live_model = pickle.load(f)
    with open(preprocessor_path, "rb") as f:
        _live_preprocessor = pickle.load(f)
    with open(schema_path, "r", encoding="utf-8") as f:
        _live_schema = json.load(f)

    if metadata_path:
        with open(metadata_path, "r", encoding="utf-8") as f:
            _live_metadata = json.load(f)
    else:
        _live_metadata = {}

    return True


def _mean(values: list[float], default: float = 0.0) -> float:
    values = [float(v) for v in values if v is not None]
    return sum(values) / len(values) if values else default


def _std(values: list[float]) -> float:
    values = [float(v) for v in values if v is not None]
    if len(values) < 2:
        return 0.0
    avg = _mean(values)
    return (sum((v - avg) ** 2 for v in values) / len(values)) ** 0.5


def _zscore(value: float, avg: float, std: float) -> float:
    return (float(value) - float(avg)) / float(std) if std else 0.0


def _dominant(values: list[str], default: str = "unknown") -> str:
    cleaned = [str(v) for v in values if v]
    if not cleaned:
        return default
    return Counter(cleaned).most_common(1)[0][0]


def _discount_rate(percent_value: float | None) -> float:
    return max(0.0, min(float(percent_value or 0.0) / 100.0, 1.0))


def _latest_payment_method(db: Session, order: Order) -> str:
    payment = (
        db.query(Payment)
        .filter(Payment.order_id == order.id, Payment.status == "completed")
        .order_by(Payment.created_at.desc(), Payment.id.desc())
        .first()
    )
    return payment.method if payment else "unknown"


def _historical_order_stats(orders: list[Order]) -> dict:
    totals = [float(o.total_amount or 0.0) for o in orders]
    basket_sizes = [sum(int(item.quantity or 0) for item in o.items) for o in orders]
    discounts = [1.0 if (float(o.discount_pct or 0.0) > 0.0 or any(float(item.discount_pct or 0.0) > 0.0 for item in o.items)) else 0.0 for o in orders]
    return {
        "count": len(orders),
        "avg_total": _mean(totals),
        "std_total": _std(totals),
        "avg_basket": _mean(basket_sizes),
        "discount_order_rate": _mean(discounts),
        "avg_discount_rate": _mean([_discount_rate(o.discount_pct) for o in orders]),
        "void_rate": _mean([1.0 if o.status == "cancelled" else 0.0 for o in orders]),
    }


def _profile_value(value: str | None, default: str = "unknown") -> str:
    return value if value else default


def _build_live_feature_row(db: Session, order: Order) -> dict:
    product_ids = [item.product_id for item in order.items if item.product_id]
    products = {}
    if product_ids:
        products = {p.id: p for p in db.query(Product).filter(Product.id.in_(product_ids)).all()}

    created_at = order.created_at or datetime.utcnow()
    items = list(order.items)
    item_count = len(items)
    basket_size = sum(int(item.quantity or 0) for item in items)
    line_totals = [float(item.subtotal or 0.0) for item in items]
    unit_prices = [float(item.unit_price or 0.0) for item in items]
    gross_line_totals = [float(item.unit_price or 0.0) * int(item.quantity or 0) for item in items]

    order_discount_rate = _discount_rate(order.discount_pct)
    item_discount_rates = [_discount_rate(item.discount_pct) for item in items]
    effective_line_discount_rates = [max(order_discount_rate, rate) for rate in item_discount_rates]
    discount_line_count = sum(1 for rate in effective_line_discount_rates if rate > 0)
    line_discount_amount = sum(max(gross - net, 0.0) for gross, net in zip(gross_line_totals, line_totals))
    estimated_discount_amount = round(line_discount_amount + float(order.discount_amount or 0.0), 2)

    categories = []
    sections = []
    price_deviations = []
    for item in items:
        product = products.get(item.product_id)
        if product:
            if product.category:
                categories.append(product.category.name)
            if product.section:
                sections.append(product.section)
            if product.price:
                price_deviations.append((float(item.unit_price or 0.0) - float(product.price)) / float(product.price))

    customer = db.query(Customer).filter(Customer.id == order.customer_id).first() if order.customer_id else None
    past_customer_orders = []
    if order.customer_id:
        past_customer_orders = (
            db.query(Order)
            .filter(Order.customer_id == order.customer_id, Order.id != order.id)
            .all()
        )
    past_cashier_orders = (
        db.query(Order)
        .filter(Order.cashier_id == order.cashier_id, Order.id != order.id)
        .all()
    )
    customer_stats = _historical_order_stats(past_customer_orders)
    cashier_stats = _historical_order_stats(past_cashier_orders)

    expected_visits = float(customer.visit_count or 0) if customer else float(customer_stats["count"])
    actual_visits = max(expected_visits, float(customer_stats["count"] + 1 if order.customer_id else 0))
    customer_visit_ratio = actual_visits / expected_visits if expected_visits else 1.0

    total_amount = float(order.total_amount or 0.0)
    avg_amount_per_item = total_amount / basket_size if basket_size else 0.0
    unique_item_count = len(set(product_ids))

    hour = int(created_at.hour)
    dayofweek = int(created_at.weekday())
    cashier_shift = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"

    row = {
        "table_number": float(order.table.number if order.table else 0),
        "basket_size": float(basket_size),
        "n_unique_items": float(unique_item_count),
        "n_unique_categories": float(len(set(categories))),
        "total_amount": total_amount,
        "avg_line_total": _mean(line_totals),
        "max_line_total": max(line_totals) if line_totals else 0.0,
        "min_line_total": min(line_totals) if line_totals else 0.0,
        "avg_item_price": _mean(unit_prices),
        "max_item_price": max(unit_prices) if unit_prices else 0.0,
        "min_item_price": min(unit_prices) if unit_prices else 0.0,
        "mean_discount_rate": _mean(effective_line_discount_rates),
        "max_discount_rate": max([order_discount_rate, *item_discount_rates]) if items else order_discount_rate,
        "discount_line_count": float(discount_line_count),
        "estimated_discount_amount": float(estimated_discount_amount),
        "void_line_count": 0.0,
        "mean_price_deviation_pct": _mean(price_deviations),
        "max_abs_price_deviation_pct": max([abs(v) for v in price_deviations]) if price_deviations else 0.0,
        "mean_abs_price_deviation_pct": _mean([abs(v) for v in price_deviations]),
        "mean_daily_item_quantity": 0.0,
        "max_daily_item_quantity": 0.0,
        "mean_demand_zscore": 0.0,
        "max_abs_demand_zscore": 0.0,
        "discount_line_rate": float(discount_line_count / item_count) if item_count else 0.0,
        "void_line_rate": 0.0,
        "avg_amount_per_item": float(avg_amount_per_item),
        "unique_item_ratio": float(unique_item_count / basket_size) if basket_size else 0.0,
        "expected_visits": expected_visits,
        "actual_visits": actual_visits,
        "customer_visit_gap": actual_visits - expected_visits,
        "customer_visit_ratio": customer_visit_ratio,
        "order_hour": float(hour),
        "order_dayofweek": float(dayofweek),
        "order_month": float(created_at.month),
        "cashier_total_orders": float(cashier_stats["count"]),
        "cashier_avg_order_amount": cashier_stats["avg_total"],
        "cashier_std_order_amount": cashier_stats["std_total"],
        "cashier_void_rate": cashier_stats["void_rate"],
        "cashier_discount_order_rate": cashier_stats["discount_order_rate"],
        "cashier_avg_discount_rate": cashier_stats["avg_discount_rate"],
        "cashier_amount_zscore": _zscore(total_amount, cashier_stats["avg_total"], cashier_stats["std_total"]),
        "customer_total_orders": float(customer_stats["count"]),
        "customer_avg_order_amount": customer_stats["avg_total"],
        "customer_std_order_amount": customer_stats["std_total"],
        "customer_avg_basket_size": customer_stats["avg_basket"],
        "customer_amount_zscore": _zscore(total_amount, customer_stats["avg_total"], customer_stats["std_total"]),
        "customer_basket_deviation": float(basket_size - customer_stats["avg_basket"]) if customer_stats["count"] else 0.0,
        "is_voided_order": int(order.status == "cancelled"),
        "void_reason_exists": int(bool(order.cancel_reason)),
        "has_discount_order": int(order_discount_rate > 0 or any(rate > 0 for rate in item_discount_rates)),
        "cashier_flagged": 0,
        "is_weekend": int(dayofweek >= 5),
        "is_odd_hour": int(hour < 6 or hour >= 23),
        "is_morning": int(6 <= hour < 11),
        "is_lunch": int(11 <= hour < 15),
        "is_dinner": int(18 <= hour < 23),
        "payment_method": _latest_payment_method(db, order),
        "restaurant_type": _dominant(sections),
        "main_category": _dominant(categories),
        "cashier_shift": cashier_shift,
        "archetype": _profile_value(customer.archetype if customer else None),
        "price_tier": _profile_value(customer.price_tier if customer else None),
        "time_preference": _profile_value(customer.time_preference if customer else None),
        "day_preference": _profile_value(customer.day_preference if customer else None),
        "basket_size_bias": "unknown",
    }

    return row


def _live_reason_codes(row: dict, score: float, decision_threshold: float) -> list[str]:
    reasons = []
    if row.get("max_discount_rate", 0.0) >= HIGH_DISCOUNT_ALERT_RATE:
        reasons.append(f"high_discount_{row['max_discount_rate']:.0%}")
    if row.get("is_voided_order"):
        reasons.append("voided_order")
    if row.get("is_odd_hour"):
        reasons.append("odd_hour_order")
    if abs(float(row.get("cashier_amount_zscore", 0.0))) >= 3.0:
        reasons.append("unusual_cashier_amount")
    if abs(float(row.get("customer_amount_zscore", 0.0))) >= 3.0:
        reasons.append("unusual_customer_amount")
    if abs(float(row.get("customer_basket_deviation", 0.0))) >= 5.0:
        reasons.append("unusual_customer_basket")
    if row.get("cashier_discount_order_rate", 0.0) >= 0.50 and row.get("has_discount_order"):
        reasons.append("cashier_discount_history")
    if score >= decision_threshold:
        reasons.append("random_forest_score")
    return reasons or ["live_anomaly_score"]


def _score_with_live_model(row: dict) -> float | None:
    if not _load_live_artifacts():
        return None

    feature_columns = _live_schema.get("feature_columns", [])
    frame = pd.DataFrame([{col: row.get(col, 0) for col in feature_columns}], columns=feature_columns)
    transformed = _live_preprocessor.transform(frame)
    if hasattr(_live_model, "predict_proba"):
        return float(_live_model.predict_proba(transformed)[0][1])
    if hasattr(_live_model, "decision_function"):
        raw_score = float(_live_model.decision_function(transformed)[0])
        return max(0.0, min((raw_score + 1.0) / 2.0, 1.0))
    return float(_live_model.predict(transformed)[0])


def score_order_live(db: Session, order: Order) -> AnomalyAlert | None:
    """Score one database order now and create/update a live alert when needed."""
    row = _build_live_feature_row(db, order)
    metadata = _live_metadata or _metadata or {}
    decision_threshold = float(metadata.get("decision_threshold", 0.2545094002249068) or 0.2545094002249068)
    critical_threshold = float(metadata.get("critical_threshold", 0.9724476567258281) or 0.9724476567258281)

    try:
        model_score = _score_with_live_model(row)
        model_error = None
    except Exception as exc:
        model_score = None
        model_error = str(exc)[:200]
    score = float(model_score if model_score is not None else 0.0)
    high_discount = float(row.get("max_discount_rate", 0.0)) >= HIGH_DISCOUNT_ALERT_RATE
    should_alert = score >= decision_threshold or high_discount

    effective_score = max(score, decision_threshold if high_discount else score)
    if effective_score >= critical_threshold or float(row.get("max_discount_rate", 0.0)) >= 0.90:
        risk_level = "CRITIQUE"
    elif should_alert:
        risk_level = "ALERTE"
    else:
        risk_level = "NORMAL"

    existing = (
        db.query(AnomalyAlert)
        .filter(AnomalyAlert.order_id == str(order.id), AnomalyAlert.model_name == LIVE_MODEL_NAME)
        .first()
    )

    if not should_alert:
        if existing and existing.status == "new":
            existing.risk_score = round(effective_score, 4)
            existing.risk_level = "NORMAL"
            existing.predicted_label = 0
            existing.status = "closed"
            existing.alert_explanation = "Order is no longer flagged by the live anomaly scorer."
            db.add(existing)
        return None

    reasons = _live_reason_codes(row, score, decision_threshold)
    alert = existing or AnomalyAlert(order_id=str(order.id), model_name=LIVE_MODEL_NAME)
    alert.risk_score = round(effective_score, 4)
    alert.risk_level = risk_level
    alert.predicted_label = 1
    alert.anomaly_type = "high_discount" if high_discount else "live_model_score"
    alert.reason_codes = json.dumps(reasons)
    model_note = f"; model unavailable: {model_error}" if model_error else ""
    alert.alert_explanation = (
        f"Live anomaly detection flagged order #{order.id}. "
        f"RF score={score:.4f}; max discount={row.get('max_discount_rate', 0.0):.0%}{model_note}."
    )
    if not alert.status or alert.status == "closed":
        alert.status = "new"
    db.add(alert)
    return alert
