"""
Segmentation Pipeline — callable from the regenerate endpoint.
Re-builds customer features from the live database (orders + customers),
then runs RFM rule-based + KMeans (k=5) + hybrid segmentation.
Persists results to the CSVs that the dashboard service reads.
"""
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline as SkPipeline
from sklearn.cluster import KMeans

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings

logger = logging.getLogger(__name__)

RANDOM_STATE = 42
N_CLUSTERS = 5
OUTPUT_DIR = Path(settings.NOTEBOOKS_PATH) / "Module 4"


# ── RFM rule assignment (exact replica from notebook) ────────────────────
def assign_rfm_segment(row):
    r, f, m = row["R_score"], row["F_score"], row["M_score"]
    score = row["rfm_score"]
    if score == 0:
        return "No Transaction History"
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    elif r >= 3 and f >= 4:
        return "Loyal Customers"
    elif r >= 4 and f <= 2:
        return "New / Promising"
    elif r >= 3 and f >= 2 and m >= 3:
        return "Potential Loyalists"
    elif r == 3 and f <= 2:
        return "Need Attention"
    elif r == 2 and f >= 3:
        return "At Risk"
    elif r <= 2 and f >= 4 and m >= 4:
        return "Cannot Lose Them"
    elif r <= 2 and f <= 2 and m <= 2:
        return "Lost / Hibernating"
    else:
        return "Others"


def quintile_score(series, reverse=False):
    ranked = series.rank(method="first", ascending=not reverse)
    try:
        return pd.qcut(ranked, 5, labels=[1, 2, 3, 4, 5]).astype(int)
    except ValueError:
        return pd.cut(ranked, 5, labels=[1, 2, 3, 4, 5], include_lowest=True).astype(int)


def assign_value_tier(score):
    if score >= 12:
        return "High-Value"
    elif score >= 8:
        return "Mid-Value"
    elif score > 0:
        return "Low-Value"
    else:
        return "No-History"


def meal_period(hour):
    if pd.isna(hour):
        return "unknown"
    if 6 <= hour < 11:
        return "morning"
    if 11 <= hour < 16:
        return "lunch"
    if 16 <= hour < 23:
        return "dinner"
    return "late_night"


def run_pipeline(db: Session) -> dict:
    """
    Full segmentation pipeline. Returns a summary dict.
    Raises on failure so the caller can log appropriately.
    """
    logger.info("Segmentation pipeline started")

    # ── 1. Extract data from the live database ───────────────────────────
    customers_df = pd.read_sql("SELECT * FROM customers", db.bind)
    orders_df = pd.read_sql("SELECT * FROM orders WHERE status = 'paid'", db.bind)
    order_items_df = pd.read_sql(
        """
        SELECT oi.*, o.customer_id, o.created_at as order_datetime, o.table_id,
               o.discount_pct as order_discount_pct
        FROM order_items oi
        JOIN orders o ON o.id = oi.order_id
        WHERE o.status = 'paid' AND o.customer_id IS NOT NULL
        """,
        db.bind,
    )
    payments_df = pd.read_sql(
        "SELECT order_id, method FROM payments WHERE status = 'completed'",
        db.bind,
    )

    if order_items_df.empty or customers_df.empty:
        logger.warning("Not enough data to run segmentation")
        return {
            "status": "skipped",
            "message": "Not enough data (no paid orders with customers)",
            "customers_processed": 0,
            "segments_produced": 0,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # ── 2. Build order-level features ────────────────────────────────────
    order_items_df["order_datetime"] = pd.to_datetime(order_items_df["order_datetime"], errors="coerce")
    order_items_df["order_hour"] = order_items_df["order_datetime"].dt.hour
    order_items_df["day_of_week"] = order_items_df["order_datetime"].dt.day_name()
    order_items_df["day_of_week_num"] = order_items_df["order_datetime"].dt.dayofweek
    order_items_df["is_weekend"] = order_items_df["day_of_week_num"].isin([5, 6]).astype(int)
    order_items_df["meal_period"] = order_items_df["order_hour"].apply(meal_period)
    order_items_df["discount_pct_val"] = order_items_df.get("order_discount_pct", pd.Series(dtype=float)).fillna(0)

    # Join payment method
    payment_map = payments_df.drop_duplicates("order_id").set_index("order_id")["method"]
    order_items_df["payment_method"] = order_items_df["order_id"].map(payment_map).fillna("cash")

    order_level = (
        order_items_df
        .groupby("order_id")
        .agg(
            customer_id=("customer_id", "first"),
            order_datetime=("order_datetime", "first"),
            order_hour=("order_hour", "first"),
            day_of_week=("day_of_week", "first"),
            day_of_week_num=("day_of_week_num", "first"),
            is_weekend=("is_weekend", "first"),
            meal_period=("meal_period", "first"),
            payment_method=("payment_method", "first"),
            order_total=("subtotal", "sum"),
            order_avg_item_price=("unit_price", "mean"),
            order_discount_pct_mean=("discount_pct_val", "mean"),
            n_lines=("id", "count"),
            n_unique_items=("product_id", "nunique"),
        )
        .reset_index()
    )
    order_level["has_discount"] = (order_level["order_discount_pct_mean"] > 0).astype(int)
    order_level["basket_size"] = order_level["n_lines"]

    # ── 3. RFM features ──────────────────────────────────────────────────
    reference_date = order_level["order_datetime"].max() + pd.Timedelta(days=1)

    rfm = (
        order_level
        .groupby("customer_id")
        .agg(
            last_order_date=("order_datetime", "max"),
            first_order_date=("order_datetime", "min"),
            frequency=("order_id", "nunique"),
            monetary=("order_total", "sum"),
        )
        .reset_index()
    )
    rfm["recency"] = (reference_date - rfm["last_order_date"]).dt.days
    rfm["customer_tenure_days"] = (rfm["last_order_date"] - rfm["first_order_date"]).dt.days.clip(lower=0)
    rfm["monetary_per_order"] = rfm["monetary"] / rfm["frequency"].replace(0, np.nan)
    rfm["total_orders"] = rfm["frequency"]

    if len(rfm) >= 5:
        rfm["R_score"] = quintile_score(rfm["recency"], reverse=True)
        rfm["F_score"] = quintile_score(rfm["frequency"], reverse=False)
        rfm["M_score"] = quintile_score(rfm["monetary"], reverse=False)
    else:
        rfm["R_score"] = 3
        rfm["F_score"] = 3
        rfm["M_score"] = 3

    rfm["rfm_score"] = rfm["R_score"] + rfm["F_score"] + rfm["M_score"]
    rfm["rfm_code"] = rfm["R_score"].astype(str) + rfm["F_score"].astype(str) + rfm["M_score"].astype(str)

    # ── 4. Basket / discount / payment / time / category features ─────────
    basket_features = (
        order_level.groupby("customer_id").agg(
            avg_order_value=("order_total", "mean"),
            avg_basket_size=("basket_size", "mean"),
            avg_item_price=("order_avg_item_price", "mean"),
        ).reset_index()
    )

    discount_features = (
        order_level.groupby("customer_id").agg(
            avg_discount_pct=("order_discount_pct_mean", "mean"),
            discount_order_rate=("has_discount", "mean"),
        ).reset_index()
    )

    time_features = (
        order_level.groupby("customer_id").agg(
            avg_order_hour=("order_hour", "mean"),
            weekend_order_rate=("is_weekend", "mean"),
        ).reset_index()
    )

    # Preferred payment
    preferred_payment = (
        order_level.groupby(["customer_id", "payment_method"]).size()
        .reset_index(name="n")
        .sort_values(["customer_id", "n"], ascending=[True, False])
        .drop_duplicates("customer_id")
        .rename(columns={"payment_method": "preferred_payment_method"})[["customer_id", "preferred_payment_method"]]
    )

    # Preferred meal period
    preferred_meal = (
        order_level.groupby(["customer_id", "meal_period"]).size()
        .reset_index(name="n")
        .sort_values(["customer_id", "n"], ascending=[True, False])
        .drop_duplicates("customer_id")
        .rename(columns={"meal_period": "dominant_meal_period"})[["customer_id", "dominant_meal_period"]]
    )

    # ── 5. Merge all features ─────────────────────────────────────────────
    customer_features = rfm.copy()
    for tbl in [basket_features, discount_features, time_features, preferred_payment, preferred_meal]:
        customer_features = customer_features.merge(tbl, on="customer_id", how="left")

    # Merge customer profile data
    profile_cols = ["id", "name", "phone", "archetype", "price_tier", "time_preference", "day_preference", "visit_count"]
    available_cols = [c for c in profile_cols if c in customers_df.columns]
    profile = customers_df[available_cols].rename(columns={"id": "customer_id"})
    customer_features = customer_features.merge(profile, on="customer_id", how="left")

    # Fill NAs
    zero_fill = ["avg_order_value", "avg_basket_size", "avg_item_price",
                 "avg_discount_pct", "discount_order_rate", "weekend_order_rate", "avg_order_hour"]
    for c in zero_fill:
        if c in customer_features.columns:
            customer_features[c] = customer_features[c].fillna(0)

    cat_defaults = {
        "preferred_payment_method": "unknown",
        "dominant_meal_period": "unknown",
        "archetype": "unknown",
        "price_tier": "unknown",
        "time_preference": "unknown",
        "day_preference": "unknown",
    }
    for c, d in cat_defaults.items():
        if c in customer_features.columns:
            customer_features[c] = customer_features[c].fillna(d)

    # ── 6. RFM segment assignment ─────────────────────────────────────────
    customer_features["rfm_segment"] = customer_features.apply(assign_rfm_segment, axis=1)

    rfm_summary = (
        customer_features.groupby("rfm_segment").agg(
            customers=("customer_id", "count"),
            avg_recency=("recency", "mean"),
            avg_frequency=("frequency", "mean"),
            total_revenue=("monetary", "sum"),
            avg_monetary=("monetary", "mean"),
        ).sort_values("customers", ascending=False).reset_index()
    )

    # ── 7. KMeans clustering ──────────────────────────────────────────────
    numeric_features = [c for c in [
        "avg_order_value", "avg_basket_size", "avg_item_price",
        "avg_discount_pct", "discount_order_rate", "weekend_order_rate",
        "avg_order_hour", "recency", "frequency", "monetary",
    ] if c in customer_features.columns]

    categorical_features = [c for c in [
        "preferred_payment_method", "dominant_meal_period",
    ] if c in customer_features.columns]

    numeric_transformer = SkPipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    try:
        categorical_transformer = SkPipeline(steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ])
    except TypeError:
        categorical_transformer = SkPipeline(steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse=False)),
        ])

    transformers = [("num", numeric_transformer, numeric_features)]
    if categorical_features:
        transformers.append(("cat", categorical_transformer, categorical_features))

    preprocessor = ColumnTransformer(transformers=transformers, remainder="drop")

    n_customers = len(customer_features)
    actual_k = min(N_CLUSTERS, n_customers)

    if actual_k < 2:
        # Not enough data for clustering
        customer_features["kmeans_cluster"] = 0
        customer_features["kmeans_segment_name"] = "Single Cluster"
    else:
        X_behavior = preprocessor.fit_transform(customer_features)
        kmeans_model = KMeans(n_clusters=actual_k, random_state=RANDOM_STATE, n_init=50)
        customer_features["kmeans_cluster"] = kmeans_model.fit_predict(X_behavior)

    # ── 8. Name clusters by profile (stable naming) ───────────────────────
    kmeans_profiles = (
        customer_features.groupby("kmeans_cluster").agg(
            customers=("customer_id", "count"),
            total_revenue=("monetary", "sum"),
            avg_monetary=("monetary", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_recency=("recency", "mean"),
            avg_order_value=("avg_order_value", "mean"),
            avg_basket_size=("avg_basket_size", "mean"),
            avg_discount_pct=("avg_discount_pct", "mean"),
            weekend_order_rate=("weekend_order_rate", "mean"),
        ).reset_index()
    )

    def name_cluster(row):
        if len(kmeans_profiles) < 2:
            return "General Cluster"
        if row["avg_monetary"] >= kmeans_profiles["avg_monetary"].quantile(0.70):
            value = "High-Value"
        elif row["avg_monetary"] <= kmeans_profiles["avg_monetary"].quantile(0.30):
            value = "Low-Value"
        else:
            value = "Mid-Value"

        if row["avg_frequency"] >= kmeans_profiles["avg_frequency"].quantile(0.70):
            activity = "Frequent"
        elif row["avg_recency"] >= kmeans_profiles["avg_recency"].quantile(0.70):
            activity = "Inactive"
        else:
            activity = "Occasional"

        if row["avg_discount_pct"] >= kmeans_profiles["avg_discount_pct"].quantile(0.70):
            style = "Discount-Sensitive"
        elif row["avg_basket_size"] >= kmeans_profiles["avg_basket_size"].quantile(0.70):
            style = "Large-Basket"
        elif row["weekend_order_rate"] >= kmeans_profiles["weekend_order_rate"].quantile(0.70):
            style = "Weekend-Oriented"
        else:
            style = "Standard"

        return f"{value} {activity} {style}"

    kmeans_profiles["kmeans_segment_name"] = kmeans_profiles.apply(name_cluster, axis=1)
    name_map = dict(zip(kmeans_profiles["kmeans_cluster"], kmeans_profiles["kmeans_segment_name"]))
    customer_features["kmeans_segment_name"] = customer_features["kmeans_cluster"].map(name_map)

    # ── 9. Hybrid segments ────────────────────────────────────────────────
    customer_features["rfm_value_tier"] = customer_features["rfm_score"].apply(assign_value_tier)
    customer_features["hybrid_segment"] = (
        customer_features["rfm_value_tier"].astype(str) + " | " + customer_features["kmeans_segment_name"].astype(str)
    )

    hybrid_profiles = (
        customer_features.groupby("hybrid_segment").agg(
            customers=("customer_id", "count"),
            total_revenue=("monetary", "sum"),
            avg_monetary=("monetary", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_recency=("recency", "mean"),
            avg_order_value=("avg_order_value", "mean"),
            avg_basket_size=("avg_basket_size", "mean"),
            avg_discount_pct=("avg_discount_pct", "mean"),
        ).sort_values(["total_revenue", "customers"], ascending=False).reset_index()
    )

    # Recommended actions
    median_recency = customer_features["recency"].median()
    q75_basket = customer_features["avg_basket_size"].quantile(0.75)

    def recommend_action(row):
        seg = row["hybrid_segment"].lower()
        if "high-value" in seg and row["avg_recency"] <= median_recency:
            return "VIP loyalty program and premium personalization"
        if "high-value" in seg and row["avg_recency"] > median_recency:
            return "Win-back campaign for valuable customers"
        if "discount" in seg:
            return "Targeted promotions and coupon campaigns"
        if row["avg_basket_size"] > q75_basket:
            return "Bundle and cross-sell offers"
        if "low-value" in seg:
            return "Low-cost engagement campaign"
        return "Standard personalized communication"

    hybrid_profiles["recommended_action"] = hybrid_profiles.apply(recommend_action, axis=1)

    # ── 10. Persist CSVs ──────────────────────────────────────────────────
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    customer_features.to_csv(OUTPUT_DIR / "customer_segments_final.csv", index=False)
    rfm_summary.to_csv(OUTPUT_DIR / "rfm_segment_summary.csv", index=False)
    kmeans_profiles.to_csv(OUTPUT_DIR / "kmeans_cluster_profiles.csv", index=False)
    hybrid_profiles.to_csv(OUTPUT_DIR / "hybrid_segment_profiles.csv", index=False)

    n_rfm = len(rfm_summary)
    n_kmeans = len(kmeans_profiles)
    n_hybrid = len(hybrid_profiles)

    logger.info(f"Pipeline done: {n_customers} customers, {n_rfm} RFM + {n_kmeans} KMeans + {n_hybrid} hybrid segments")

    return {
        "status": "completed",
        "customers_processed": n_customers,
        "rfm_segments": n_rfm,
        "kmeans_clusters": n_kmeans,
        "hybrid_segments": n_hybrid,
        "segments_produced": n_rfm + n_kmeans + n_hybrid,
        "timestamp": datetime.utcnow().isoformat(),
    }
