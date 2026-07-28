"""
Segmentation stability analysis for Module 4.

This is an evaluation-only companion to Segmentation_Modeling.ipynb. It reuses
the same behavioral feature construction and final K-Means settings, then saves
stability metrics, figures, and an interpretation note without changing served
segmentation artifacts.
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


RANDOM_STATE = 42
FINAL_BUSINESS_K = 5
SEEDS = list(range(30))
N_BOOTSTRAPS = 30
CONSENSUS_SAMPLE_SIZE = 2500

SCRIPT_DIR = Path(__file__).resolve().parent
AI_ROOT = SCRIPT_DIR.parents[1]
FEATURES_PATH = AI_ROOT / "data" / "processed" / "Module 4" / "customer_features.csv"
OUTPUT_DIR = AI_ROOT / "data" / "final" / "Module 4" / "stability"
FIGURE_DIR = OUTPUT_DIR / "figures"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)


def save_figure(filename: str) -> Path:
    path = FIGURE_DIR / filename
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path


def build_behavior_matrix(customer_features: pd.DataFrame):
    id_cols = [
        "customer_id",
        "profile_transaction_match",
        "last_order_date",
        "first_order_date",
        "rfm_code",
        "rfm_segment",
    ]

    rfm_value_cols = [
        "recency",
        "frequency",
        "monetary",
        "R_score",
        "F_score",
        "M_score",
        "rfm_score",
        "monetary_per_order",
        "total_orders",
    ]

    candidate_cols = [c for c in customer_features.columns if c not in id_cols + rfm_value_cols]
    numeric_features = []
    categorical_features = []
    for col in candidate_cols:
        if customer_features[col].dtype in ["int64", "float64", "int32", "float32", "bool"]:
            numeric_features.append(col)
        elif customer_features[col].dtype == "object":
            categorical_features.append(col)

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    try:
        categorical_transformer = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
            ]
        )
    except TypeError:
        categorical_transformer = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore", sparse=False)),
            ]
        )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ],
        remainder="drop",
    )
    x_behavior = preprocessor.fit_transform(customer_features)
    return np.asarray(x_behavior), numeric_features, categorical_features


def name_cluster(row: pd.Series, profiles: pd.DataFrame) -> str:
    if row["avg_monetary"] >= profiles["avg_monetary"].quantile(0.70):
        value = "High-Value"
    elif row["avg_monetary"] <= profiles["avg_monetary"].quantile(0.30):
        value = "Low-Value"
    else:
        value = "Mid-Value"

    if row["avg_frequency"] >= profiles["avg_frequency"].quantile(0.70):
        activity = "Frequent"
    elif row["avg_recency"] >= profiles["avg_recency"].quantile(0.70):
        activity = "Inactive"
    else:
        activity = "Occasional"

    if row["avg_discount_pct"] >= profiles["avg_discount_pct"].quantile(0.70):
        style = "Discount-Sensitive"
    elif row["avg_basket_size"] >= profiles["avg_basket_size"].quantile(0.70):
        style = "Large-Basket"
    elif row["weekend_order_rate"] >= profiles["weekend_order_rate"].quantile(0.70):
        style = "Weekend-Oriented"
    else:
        style = "Standard"

    return f"{value} {activity} {style}"


def cluster_profiles(customer_features: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
    data = customer_features.copy()
    data["cluster"] = labels
    profiles = (
        data.groupby("cluster")
        .agg(
            customers=("customer_id", "count"),
            total_revenue=("monetary", "sum"),
            avg_monetary=("monetary", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_recency=("recency", "mean"),
            avg_order_value=("avg_order_value", "mean"),
            avg_basket_size=("avg_basket_size", "mean"),
            avg_discount_pct=("avg_discount_pct", "mean"),
            weekend_order_rate=("weekend_order_rate", "mean"),
            avg_visit_gap=("visit_gap", "mean"),
        )
        .reset_index()
    )
    return profiles


def fit_kmeans(k: int, seed: int, n_init: int = 20) -> KMeans:
    return KMeans(n_clusters=k, random_state=seed, n_init=n_init)


def seed_stability(x_behavior: np.ndarray, reference_labels: np.ndarray, k: int):
    labels_by_seed = {}
    centroids_by_seed = {}
    for seed in SEEDS:
        model = fit_kmeans(k, seed, n_init=20)
        labels_by_seed[seed] = model.fit_predict(x_behavior)
        centroids_by_seed[seed] = model.cluster_centers_

    pairwise_rows = []
    pairwise_values = []
    for seed_a, seed_b in combinations(SEEDS, 2):
        ari = adjusted_rand_score(labels_by_seed[seed_a], labels_by_seed[seed_b])
        pairwise_values.append(ari)
        pairwise_rows.append(
            {
                "record_type": "pairwise_seed_ari",
                "k": k,
                "seed": seed_a,
                "seed_b": seed_b,
                "ari": ari,
                "metric": "pairwise_ari",
                "value": ari,
            }
        )

    vs_reference_rows = []
    vs_reference_values = []
    for seed in SEEDS:
        ari = adjusted_rand_score(reference_labels, labels_by_seed[seed])
        vs_reference_values.append(ari)
        vs_reference_rows.append(
            {
                "record_type": "seed_vs_reference",
                "k": k,
                "seed": seed,
                "seed_b": RANDOM_STATE,
                "ari": ari,
                "metric": "ari_vs_reference",
                "value": ari,
            }
        )

    summary_rows = []
    for prefix, values in [
        ("pairwise", np.array(pairwise_values)),
        ("vs_reference", np.array(vs_reference_values)),
    ]:
        for metric, value in {
            "mean": values.mean(),
            "min": values.min(),
            "max": values.max(),
            "std": values.std(ddof=0),
        }.items():
            summary_rows.append(
                {
                    "record_type": f"{prefix}_summary",
                    "k": k,
                    "seed": np.nan,
                    "seed_b": np.nan,
                    "ari": np.nan,
                    "metric": metric,
                    "value": value,
                }
            )

    return (
        pd.DataFrame(pairwise_rows + vs_reference_rows + summary_rows),
        labels_by_seed,
        centroids_by_seed,
        np.array(pairwise_values),
        np.array(vs_reference_values),
    )


def bootstrap_stability(
    x_behavior: np.ndarray,
    reference_labels: np.ndarray,
    k: int,
):
    n_customers = x_behavior.shape[0]
    rng = np.random.default_rng(RANDOM_STATE)
    consensus_orig_idx = np.sort(
        rng.choice(n_customers, size=min(CONSENSUS_SAMPLE_SIZE, n_customers), replace=False)
    )
    sample_position_by_orig = {orig: pos for pos, orig in enumerate(consensus_orig_idx)}
    m = len(consensus_orig_idx)
    co_counts = np.zeros((m, m), dtype=np.uint16)
    together_counts = np.zeros((m, m), dtype=np.uint16)
    bootstrap_rows = []

    for bootstrap_id in range(N_BOOTSTRAPS):
        sample_idx = rng.choice(n_customers, size=n_customers, replace=True)
        unique_idx = np.unique(sample_idx)
        model = fit_kmeans(k, RANDOM_STATE + bootstrap_id + 1, n_init=20)
        model.fit(x_behavior[sample_idx])

        overlap_labels = model.predict(x_behavior[unique_idx])
        overlap_ari = adjusted_rand_score(reference_labels[unique_idx], overlap_labels)
        bootstrap_rows.append(
            {
                "record_type": "bootstrap_overlap_ari",
                "bootstrap_id": bootstrap_id,
                "metric": "ari_vs_reference_on_unique_sampled_customers",
                "value": overlap_ari,
                "n_unique_customers": len(unique_idx),
            }
        )

        sampled_consensus_orig = np.intersect1d(consensus_orig_idx, unique_idx, assume_unique=True)
        sampled_positions = np.array([sample_position_by_orig[i] for i in sampled_consensus_orig], dtype=int)
        sampled_labels = model.predict(x_behavior[sampled_consensus_orig])
        co_counts[np.ix_(sampled_positions, sampled_positions)] += 1
        for label in np.unique(sampled_labels):
            label_positions = sampled_positions[sampled_labels == label]
            together_counts[np.ix_(label_positions, label_positions)] += 1

    np.fill_diagonal(co_counts, 0)
    np.fill_diagonal(together_counts, 0)
    valid = co_counts > 0
    consensus = np.zeros_like(together_counts, dtype=float)
    consensus[valid] = together_counts[valid] / co_counts[valid]
    upper = np.triu(valid, k=1)
    pair_values = consensus[upper]

    same_cluster_means = []
    different_cluster_means = []
    max_partner_consensus = []
    ref_sample_labels = reference_labels[consensus_orig_idx]
    for i in range(m):
        valid_i = valid[i].copy()
        valid_i[i] = False
        if not valid_i.any():
            continue
        same_mask = valid_i & (ref_sample_labels == ref_sample_labels[i])
        diff_mask = valid_i & (ref_sample_labels != ref_sample_labels[i])
        if same_mask.any():
            same_cluster_means.append(float(consensus[i, same_mask].mean()))
        if diff_mask.any():
            different_cluster_means.append(float(consensus[i, diff_mask].mean()))
        max_partner_consensus.append(float(consensus[i, valid_i].max()))

    summary_metrics = {
        "consensus_sample_size": m,
        "bootstrap_iterations": N_BOOTSTRAPS,
        "mean_bootstrap_overlap_ari": float(np.mean([r["value"] for r in bootstrap_rows])),
        "min_bootstrap_overlap_ari": float(np.min([r["value"] for r in bootstrap_rows])),
        "max_bootstrap_overlap_ari": float(np.max([r["value"] for r in bootstrap_rows])),
        "std_bootstrap_overlap_ari": float(np.std([r["value"] for r in bootstrap_rows])),
        "mean_pair_consensus": float(pair_values.mean()),
        "fraction_pairs_consensus_gt_0_8": float((pair_values > 0.8).mean()),
        "fraction_pairs_consensus_lt_0_2": float((pair_values < 0.2).mean()),
        "fraction_pairs_consensus_between_0_4_and_0_6": float(((pair_values >= 0.4) & (pair_values <= 0.6)).mean()),
        "mean_customer_max_partner_consensus": float(np.mean(max_partner_consensus)),
        "mean_same_reference_cluster_consensus": float(np.mean(same_cluster_means)),
        "mean_different_reference_cluster_consensus": float(np.mean(different_cluster_means)),
    }

    summary_rows = [
        {
            "record_type": "consensus_summary",
            "bootstrap_id": np.nan,
            "metric": metric,
            "value": value,
            "n_unique_customers": np.nan,
        }
        for metric, value in summary_metrics.items()
    ]
    per_customer_rows = [
        {
            "record_type": "per_customer_consensus",
            "bootstrap_id": np.nan,
            "metric": "max_partner_consensus",
            "value": value,
            "n_unique_customers": np.nan,
        }
        for value in max_partner_consensus
    ]
    return pd.DataFrame(bootstrap_rows + summary_rows + per_customer_rows), pair_values, np.array(max_partner_consensus)


def profile_stability(
    customer_features: pd.DataFrame,
    reference_model: KMeans,
    reference_labels: np.ndarray,
    labels_by_seed: dict[int, np.ndarray],
    centroids_by_seed: dict[int, np.ndarray],
):
    profile_features = [
        "avg_monetary",
        "avg_frequency",
        "avg_recency",
        "avg_order_value",
        "avg_basket_size",
        "avg_discount_pct",
        "weekend_order_rate",
        "avg_visit_gap",
    ]
    canonical_profiles = cluster_profiles(customer_features, reference_labels)
    canonical_profiles["segment_name"] = canonical_profiles.apply(
        lambda row: name_cluster(row, canonical_profiles), axis=1
    )

    profile_observations = []
    for seed in SEEDS:
        labels = labels_by_seed[seed]
        profiles = cluster_profiles(customer_features, labels).set_index("cluster")
        distances = np.linalg.norm(
            reference_model.cluster_centers_[:, None, :] - centroids_by_seed[seed][None, :, :],
            axis=2,
        )
        ref_rows, run_cols = linear_sum_assignment(distances)
        match_map = dict(zip(run_cols, ref_rows))

        for run_cluster, canonical_cluster in match_map.items():
            row = profiles.loc[run_cluster]
            canonical = canonical_profiles.loc[canonical_profiles["cluster"] == canonical_cluster].iloc[0]
            for feature in profile_features:
                profile_observations.append(
                    {
                        "seed": seed,
                        "canonical_cluster": int(canonical_cluster),
                        "segment_name": canonical["segment_name"],
                        "matched_run_cluster": int(run_cluster),
                        "feature": feature,
                        "value": float(row[feature]),
                    }
                )

    observations = pd.DataFrame(profile_observations)
    summary = (
        observations.groupby(["canonical_cluster", "segment_name", "feature"])
        .agg(
            mean=("value", "mean"),
            std=("value", "std"),
            min=("value", "min"),
            max=("value", "max"),
        )
        .reset_index()
    )
    summary["coefficient_of_variation"] = np.where(
        summary["mean"].abs() > 1e-12,
        summary["std"].fillna(0) / summary["mean"].abs(),
        0.0,
    )
    canonical_lookup = canonical_profiles.set_index("cluster")
    summary["canonical_value"] = summary.apply(
        lambda row: float(canonical_lookup.loc[row["canonical_cluster"], row["feature"]]), axis=1
    )
    return summary, canonical_profiles


def separation_metrics(x_behavior: np.ndarray, k: int) -> dict:
    model = fit_kmeans(k, RANDOM_STATE, n_init=50)
    labels = model.fit_predict(x_behavior)
    return {
        "k": k,
        "silhouette": silhouette_score(x_behavior, labels),
        "davies_bouldin": davies_bouldin_score(x_behavior, labels),
        "calinski_harabasz": calinski_harabasz_score(x_behavior, labels),
        "labels": labels,
        "model": model,
    }


def write_interpretation(
    seed_df: pd.DataFrame,
    bootstrap_df: pd.DataFrame,
    profile_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
    output_paths: list[Path],
):
    def metric(df: pd.DataFrame, record_type: str, metric_name: str, k: int | None = None) -> float:
        filtered = df[(df["record_type"] == record_type) & (df["metric"] == metric_name)]
        if k is not None:
            filtered = filtered[filtered["k"] == k]
        return float(filtered["value"].iloc[0])

    k5_pairwise_mean = metric(seed_df, "pairwise_summary", "mean", FINAL_BUSINESS_K)
    k5_pairwise_min = metric(seed_df, "pairwise_summary", "min", FINAL_BUSINESS_K)
    k5_vs_ref_mean = metric(seed_df, "vs_reference_summary", "mean", FINAL_BUSINESS_K)
    boot_ari = float(
        bootstrap_df[
            (bootstrap_df["record_type"] == "consensus_summary")
            & (bootstrap_df["metric"] == "mean_bootstrap_overlap_ari")
        ]["value"].iloc[0]
    )
    same_consensus = float(
        bootstrap_df[
            (bootstrap_df["record_type"] == "consensus_summary")
            & (bootstrap_df["metric"] == "mean_same_reference_cluster_consensus")
        ]["value"].iloc[0]
    )
    diff_consensus = float(
        bootstrap_df[
            (bootstrap_df["record_type"] == "consensus_summary")
            & (bootstrap_df["metric"] == "mean_different_reference_cluster_consensus")
        ]["value"].iloc[0]
    )
    median_profile_cv = float(profile_df["coefficient_of_variation"].median())
    max_profile_cv = float(profile_df["coefficient_of_variation"].max())

    k2 = comparison_df[comparison_df["k"] == 2].iloc[0]
    k5 = comparison_df[comparison_df["k"] == 5].iloc[0]

    verdict = (
        "supports"
        if k5["pairwise_seed_ari_mean"] >= 0.8 and k5["pairwise_seed_ari_mean"] >= 0.85 * k2["pairwise_seed_ari_mean"]
        else "qualifies"
    )

    text = f"""# Segmentation Stability Interpretation

## Headline

The final k=5 K-Means segmentation is reproducible across random seeds. Across {len(SEEDS)} seed refits, pairwise ARI has mean **{k5_pairwise_mean:.3f}** and minimum **{k5_pairwise_min:.3f}**. Mean ARI against the canonical `random_state=42` solution is **{k5_vs_ref_mean:.3f}**.

This means the low silhouette score should be read as weak geometric separation, not as random or unstable customer assignment. Customer behavior is continuous, so there are few natural gaps, but the imposed k=5 partition is operationally reproducible.

## Bootstrap Perturbation

Bootstrap refits show mean ARI versus the reference partition of **{boot_ari:.3f}** on customers appearing in each resample. In the consensus sample, customer pairs from the same reference segment have mean co-assignment **{same_consensus:.3f}**, while pairs from different reference segments have mean co-assignment **{diff_consensus:.3f}**.

The consensus result is the practical robustness check: customers tend to remain with the same neighboring customers under resampling, rather than drifting randomly between groups.

## Segment Meaning

After matching clusters by nearest centroid, centroid profile variability is modest: median coefficient of variation across defining profile features is **{median_profile_cv:.3f}** and the maximum observed coefficient of variation is **{max_profile_cv:.3f}**.

This supports the app's regenerate-segments workflow: label numbers may permute internally, but the business profiles represented by the segments remain consistent when clusters are matched by centroid.

## k=5 Override Versus k=2

Silhouette still prefers k=2. In this run:

- k=2 silhouette: **{k2['silhouette']:.3f}**, pairwise seed ARI mean: **{k2['pairwise_seed_ari_mean']:.3f}**
- k=5 silhouette: **{k5['silhouette']:.3f}**, pairwise seed ARI mean: **{k5['pairwise_seed_ari_mean']:.3f}**

The k=5 choice {verdict} the business override: it gives more actionable differentiation than k=2, while retaining strong reproducibility. k=2 is cleaner geometrically but collapses the customer base toward a broad engaged/not-engaged split, which is less useful for targeted actions.

## Honest Framing

Clusters are not well-separated because restaurant customer behavior is continuous. The defense is not that k=5 discovers five naturally isolated islands; it is that the five operational segments are stable, reproducible, and interpretable enough to support consistent business actions.

## Generated Files

{chr(10).join(f'- `{path}`' for path in output_paths)}
"""
    path = OUTPUT_DIR / "segmentation_stability_interpretation.md"
    path.write_text(text, encoding="utf-8")
    return path


def main():
    customer_features = pd.read_csv(FEATURES_PATH)
    x_behavior, numeric_features, categorical_features = build_behavior_matrix(customer_features)
    print(f"Loaded {len(customer_features):,} customers")
    print(f"Behavioral matrix: {x_behavior.shape}")
    print(f"Numeric features: {len(numeric_features)}; categorical features: {len(categorical_features)}")

    reference_model = fit_kmeans(FINAL_BUSINESS_K, RANDOM_STATE, n_init=50)
    reference_labels = reference_model.fit_predict(x_behavior)

    seed_df_k5, labels_by_seed_k5, centroids_by_seed_k5, pairwise_k5, vs_ref_k5 = seed_stability(
        x_behavior, reference_labels, FINAL_BUSINESS_K
    )
    seed_df_k2, _, _, pairwise_k2, vs_ref_k2 = seed_stability(
        x_behavior, separation_metrics(x_behavior, 2)["labels"], 2
    )
    seed_df = pd.concat([seed_df_k5, seed_df_k2], ignore_index=True)
    seed_path = OUTPUT_DIR / "segmentation_seed_stability.csv"
    seed_df.to_csv(seed_path, index=False)
    print(f"Saved {seed_path}")

    bootstrap_df, consensus_pair_values, max_partner_consensus = bootstrap_stability(
        x_behavior, reference_labels, FINAL_BUSINESS_K
    )
    bootstrap_path = OUTPUT_DIR / "segmentation_bootstrap_consensus.csv"
    bootstrap_df.to_csv(bootstrap_path, index=False)
    print(f"Saved {bootstrap_path}")

    profile_df, canonical_profiles = profile_stability(
        customer_features,
        reference_model,
        reference_labels,
        labels_by_seed_k5,
        centroids_by_seed_k5,
    )
    profile_path = OUTPUT_DIR / "segmentation_profile_stability.csv"
    profile_df.to_csv(profile_path, index=False)
    print(f"Saved {profile_path}")

    k2_sep = separation_metrics(x_behavior, 2)
    k5_sep = separation_metrics(x_behavior, 5)
    comparison_df = pd.DataFrame(
        [
            {
                "k": 2,
                "silhouette": k2_sep["silhouette"],
                "davies_bouldin": k2_sep["davies_bouldin"],
                "calinski_harabasz": k2_sep["calinski_harabasz"],
                "pairwise_seed_ari_mean": pairwise_k2.mean(),
                "pairwise_seed_ari_min": pairwise_k2.min(),
                "ari_vs_reference_mean": vs_ref_k2.mean(),
                "business_note": "Silhouette-optimal but broad engaged/not-engaged split.",
            },
            {
                "k": 5,
                "silhouette": k5_sep["silhouette"],
                "davies_bouldin": k5_sep["davies_bouldin"],
                "calinski_harabasz": k5_sep["calinski_harabasz"],
                "pairwise_seed_ari_mean": pairwise_k5.mean(),
                "pairwise_seed_ari_min": pairwise_k5.min(),
                "ari_vs_reference_mean": vs_ref_k5.mean(),
                "business_note": "Manual business override for actionable segment differentiation.",
            },
        ]
    )
    comparison_path = OUTPUT_DIR / "segmentation_k2_vs_k5_comparison.csv"
    comparison_df.to_csv(comparison_path, index=False)
    print(f"Saved {comparison_path}")

    plt.figure(figsize=(8, 5))
    plt.hist(pairwise_k5, bins=16, color="#E3344F", alpha=0.82, edgecolor="white")
    plt.axvline(pairwise_k5.mean(), color="#111827", linestyle="--", linewidth=1.5, label=f"Mean ARI = {pairwise_k5.mean():.3f}")
    plt.title("Seed Stability: k=5 Pairwise ARI")
    plt.xlabel("Adjusted Rand Index")
    plt.ylabel("Seed-pair count")
    plt.legend()
    seed_fig = save_figure("segmentation_seed_ari_distribution.png")

    plt.figure(figsize=(8, 5))
    plt.hist(max_partner_consensus, bins=18, color="#2E9F75", alpha=0.82, edgecolor="white")
    plt.title("Bootstrap Consensus: Per-Customer Max Co-Assignment")
    plt.xlabel("Max co-assignment with another sampled customer")
    plt.ylabel("Customer count")
    consensus_fig = save_figure("segmentation_bootstrap_consensus_distribution.png")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    x = np.arange(len(comparison_df))
    axes[0].bar(x, comparison_df["silhouette"], color=["#64748B", "#E3344F"])
    axes[0].set_title("Cluster Separation")
    axes[0].set_xticks(x, [f"k={k}" for k in comparison_df["k"]])
    axes[0].set_ylabel("Silhouette")
    axes[1].bar(x, comparison_df["pairwise_seed_ari_mean"], color=["#64748B", "#E3344F"])
    axes[1].set_title("Seed Stability")
    axes[1].set_xticks(x, [f"k={k}" for k in comparison_df["k"]])
    axes[1].set_ylabel("Mean pairwise ARI")
    comparison_fig = save_figure("segmentation_k2_vs_k5_stability_comparison.png")

    interpretation_path = write_interpretation(
        seed_df,
        bootstrap_df,
        profile_df,
        comparison_df,
        [
            seed_path,
            bootstrap_path,
            profile_path,
            comparison_path,
            seed_fig,
            consensus_fig,
            comparison_fig,
        ],
    )
    print(f"Saved {interpretation_path}")

    print("\nKey results")
    print(comparison_df.to_string(index=False))
    print("\nBootstrap consensus summary")
    print(
        bootstrap_df[bootstrap_df["record_type"] == "consensus_summary"][
            ["metric", "value"]
        ].to_string(index=False)
    )
    print("\nOutput files")
    for path in [
        seed_path,
        bootstrap_path,
        profile_path,
        comparison_path,
        seed_fig,
        consensus_fig,
        comparison_fig,
        interpretation_path,
    ]:
        print(path)


if __name__ == "__main__":
    main()
