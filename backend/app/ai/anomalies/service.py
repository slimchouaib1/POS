"""
AI Anomaly Detection Service
Loads real anomaly alerts from Notebooks Module 3 and serves them.
"""
import pandas as pd
import json
from pathlib import Path
from app.core.config import settings

_alerts_df = None
_full_df = None
_metadata = None


def _load_data():
    global _alerts_df, _full_df, _metadata

    if _alerts_df is not None:
        return

    # Load alerts (dashboard summary)
    alerts_path = Path(settings.NOTEBOOKS_PATH) / "Module 3" / "Final" / "exports" / "final_anomaly_alerts_dashboard.csv"
    if alerts_path.exists():
        _alerts_df = pd.read_csv(alerts_path)
    else:
        _alerts_df = pd.DataFrame()

    # Load full alerts (with all features for order details)
    full_path = Path(settings.NOTEBOOKS_PATH) / "Module 3" / "Final" / "exports" / "final_anomaly_alerts_full.csv"
    if full_path.exists():
        _full_df = pd.read_csv(full_path)
    else:
        _full_df = pd.DataFrame()

    # Load metadata
    meta_path = Path(settings.NOTEBOOKS_PATH) / "Module 3" / "Final" / "exports" / "final_anomaly_module_metadata.json"
    if meta_path.exists():
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
