"""
AI Customer Segmentation Service
Loads real segmentation data from Notebooks Module 4:
- RFM segments (9)
- KMeans clusters (5)
- Hybrid segments (15)
- Per-customer segment assignments
"""
import pandas as pd
import json
from pathlib import Path
from app.core.config import settings

_segments_df = None
_hybrid_profiles = None
_rfm_summary = None
_kmeans_profiles = None


def _load_data():
    global _segments_df, _hybrid_profiles, _rfm_summary, _kmeans_profiles

    if _segments_df is not None:
        return

    base = Path(settings.NOTEBOOKS_PATH) / "Module 4"

    # Customer segments final (10,001 customers)
    path = base / "customer_segments_final.csv"
    if path.exists():
        _segments_df = pd.read_csv(path)
    else:
        _segments_df = pd.DataFrame()

    # Hybrid segment profiles
    path = base / "hybrid_segment_profiles.csv"
    if path.exists():
        _hybrid_profiles = pd.read_csv(path)
    else:
        _hybrid_profiles = pd.DataFrame()

    # RFM segment summary
    path = base / "rfm_segment_summary.csv"
    if path.exists():
        _rfm_summary = pd.read_csv(path)
    else:
        _rfm_summary = pd.DataFrame()

    # KMeans cluster profiles
    path = base / "kmeans_cluster_profiles.csv"
    if path.exists():
        _kmeans_profiles = pd.read_csv(path)
    else:
        _kmeans_profiles = pd.DataFrame()


def _force_reload():
    """Invalidate the cached data so the next _load_data() call re-reads fresh CSVs."""
    global _segments_df, _hybrid_profiles, _rfm_summary, _kmeans_profiles
    _segments_df = None
    _hybrid_profiles = None
    _rfm_summary = None
    _kmeans_profiles = None


def get_customer_segment(customer_id: int) -> dict:
    """Get segment info for a specific customer."""
    _load_data()

    if _segments_df is None or _segments_df.empty:
        return {"error": "Données de segmentation non disponibles"}

    # Find customer
    cust = _segments_df[_segments_df["customer_id"] == customer_id]
    if cust.empty:
        return {"error": f"Client {customer_id} non trouvé dans les segments"}

    row = cust.iloc[0]

    rfm_segment = str(row.get("rfm_segment", ""))
    kmeans_segment = str(row.get("kmeans_segment_name", row.get("kmeans_cluster", "")))
    hybrid_segment = str(row.get("hybrid_segment", ""))
    rfm_value_tier = str(row.get("rfm_value_tier", ""))

    # Get recommended action from hybrid profiles
    action = ""
    if _hybrid_profiles is not None and not _hybrid_profiles.empty and hybrid_segment:
        match = _hybrid_profiles[_hybrid_profiles["hybrid_segment"] == hybrid_segment]
        if not match.empty:
            action = str(match.iloc[0].get("recommended_action", match.iloc[0].get("business_action", "")))

    return {
        "customer_id": customer_id,
        "rfm_segment": rfm_segment,
        "rfm_value_tier": rfm_value_tier,
        "kmeans_segment": kmeans_segment,
        "hybrid_segment": hybrid_segment,
        "recommended_action": action,
        "explanation": (
            f"Client classé '{rfm_segment}' (RFM) et '{kmeans_segment}' (KMeans). "
            f"Segment hybride: '{hybrid_segment}'. "
            f"Action recommandée: {action if action else 'Non définie'}."
        ),
    }


def get_segmentation_overview() -> dict:
    """Return full segmentation dashboard data."""
    _load_data()

    result = {
        "total_customers": 0,
        "rfm_segments": [],
        "kmeans_segments": [],
        "hybrid_segments": [],
    }

    if _segments_df is not None and not _segments_df.empty:
        result["total_customers"] = len(_segments_df)

    # RFM summary
    if _rfm_summary is not None and not _rfm_summary.empty:
        for _, row in _rfm_summary.iterrows():
            result["rfm_segments"].append({
                "segment": str(row.get("rfm_segment", "")),
                "customers": int(row.get("customers", 0)),
                "total_revenue": round(float(row.get("total_revenue", 0)), 2),
                "avg_monetary": round(float(row.get("avg_monetary", 0)), 2),
                "avg_frequency": round(float(row.get("avg_frequency", 0)), 1),
                "avg_recency": round(float(row.get("avg_recency", 0)), 0),
            })

    # KMeans profiles
    if _kmeans_profiles is not None and not _kmeans_profiles.empty:
        for _, row in _kmeans_profiles.iterrows():
            result["kmeans_segments"].append({
                "cluster": int(row.get("kmeans_cluster", 0)),
                "segment_name": str(row.get("kmeans_segment_name", "")),
                "customers": int(row.get("customers", 0)),
                "total_revenue": round(float(row.get("total_revenue", 0)), 2),
                "avg_monetary": round(float(row.get("avg_monetary", 0)), 2),
                "avg_frequency": round(float(row.get("avg_frequency", 0)), 1),
                "avg_order_value": round(float(row.get("avg_order_value", 0)), 2),
                "avg_basket_size": round(float(row.get("avg_basket_size", 0)), 1),
                "weekend_order_rate": round(float(row.get("weekend_order_rate", 0)) * 100, 1),
            })

    # Hybrid segment distribution
    if _hybrid_profiles is not None and not _hybrid_profiles.empty:
        for _, row in _hybrid_profiles.iterrows():
            result["hybrid_segments"].append({
                "segment": str(row.get("hybrid_segment", "")),
                "customers": int(row.get("customers", row.get("count", 0))),
                "total_revenue": round(float(row.get("total_revenue", 0)), 2),
                "avg_monetary": round(float(row.get("avg_monetary", 0)), 2),
                "recommended_action": str(row.get("recommended_action", row.get("business_action", ""))),
            })
    elif _segments_df is not None and not _segments_df.empty and "hybrid_segment" in _segments_df.columns:
        # Build from raw data
        hybrid_counts = _segments_df["hybrid_segment"].value_counts()
        for seg, count in hybrid_counts.items():
            result["hybrid_segments"].append({
                "segment": str(seg),
                "customers": int(count),
                "total_revenue": 0,
                "avg_monetary": 0,
                "recommended_action": "",
            })

    return result
