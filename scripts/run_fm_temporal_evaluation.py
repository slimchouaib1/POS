from __future__ import annotations

import math
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import LabelEncoder


ROOT = Path(__file__).resolve().parents[1]
AI_ROOT = ROOT / "backend" / "Ai models"
RAW_DIR = AI_ROOT / "data" / "raw"
MODULE1_FINAL_DIR = AI_ROOT / "data" / "final" / "Module 1"
RECOMMENDATIONS_DIR = AI_ROOT / "notebooks" / "Recommendations"
FIGURES_DIR = RECOMMENDATIONS_DIR / "figures"
METRICS_DIR = RECOMMENDATIONS_DIR / "metrics"
REPORTS_DIR = RECOMMENDATIONS_DIR / "reports"

NEG_RATIO = 2
TOP_K = 5
RANDOM_SEED = 42


def ensure_dirs() -> None:
    for directory in [FIGURES_DIR, METRICS_DIR, REPORTS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def get_meal_period(hour: int) -> str:
    if 6 <= hour <= 10:
        return "breakfast"
    if 11 <= hour <= 14:
        return "lunch"
    if 15 <= hour <= 17:
        return "afternoon"
    if 18 <= hour <= 22:
        return "dinner"
    return "late_night"


def prepare_fm_frame() -> tuple[pd.DataFrame, dict[str, LabelEncoder]]:
    data_path = RAW_DIR / "enterprise_pos_dataset.csv"
    print(f"Loading raw orders from {data_path}", flush=True)
    df = pd.read_csv(data_path, sep="|")
    df = df[df["is_voided"].astype(str).str.lower().ne("true")].copy()
    df["order_date"] = pd.to_datetime(df["order_date"])
    parsed_time = pd.to_datetime(df["order_time"], format="%I:%M %p", errors="coerce")
    if parsed_time.isna().any():
        parsed_time = parsed_time.fillna(pd.to_datetime(df["order_time"], errors="coerce"))
    df["hour"] = parsed_time.dt.hour.astype(int)
    df["day_of_week"] = df["order_date"].dt.dayofweek.astype(int)
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["meal_period"] = df["hour"].apply(get_meal_period)

    encoders: dict[str, LabelEncoder] = {}
    for col, idx_col in [
        ("customer_id", "user_idx"),
        ("item_name", "item_idx"),
        ("meal_period", "meal_idx"),
        ("restaurant_type", "restaurant_idx"),
        ("category", "category_idx"),
    ]:
        encoder = LabelEncoder()
        df[idx_col] = encoder.fit_transform(df[col].astype(str))
        encoders[col] = encoder

    print(
        f"Prepared {len(df):,} non-voided order lines, "
        f"{df['customer_id'].nunique():,} customers, {df['item_name'].nunique():,} items.",
        flush=True,
    )
    return df, encoders


def build_temporal_samples(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    group_cols = [
        "user_idx",
        "item_idx",
        "order_date",
        "hour",
        "day_of_week",
        "is_weekend",
        "meal_idx",
        "restaurant_idx",
        "category_idx",
    ]
    positive_samples = df.groupby(group_cols, as_index=False).size()
    positive_samples = positive_samples.rename(columns={"size": "count"})
    positive_samples["label"] = 1
    positive_samples["order_date"] = pd.to_datetime(positive_samples["order_date"])

    unique_dates = np.array(sorted(positive_samples["order_date"].dropna().unique()))
    cutoff_date = pd.Timestamp(unique_dates[int(0.8 * len(unique_dates))])
    train_pos = positive_samples[positive_samples["order_date"] < cutoff_date].copy()
    test_pos = positive_samples[positive_samples["order_date"] >= cutoff_date].copy()

    all_items = set(positive_samples["item_idx"].unique())

    def sample_period_negatives(
        positive_period: pd.DataFrame, random_seed: int
    ) -> pd.DataFrame:
        rng = np.random.default_rng(random_seed)
        context_lookup = (
            positive_period.groupby(["user_idx", "meal_idx"])["item_idx"]
            .agg(lambda s: set(s))
            .to_dict()
        )
        negatives = []
        for row in positive_period.itertuples(index=False):
            context_items = context_lookup.get((row.user_idx, row.meal_idx), set())
            negative_items = np.array(sorted(all_items - context_items), dtype=int)
            if len(negative_items) == 0:
                continue
            chosen = rng.choice(
                negative_items,
                size=min(NEG_RATIO, len(negative_items)),
                replace=False,
            )
            for item_idx in chosen:
                negatives.append(
                    {
                        "user_idx": row.user_idx,
                        "item_idx": int(item_idx),
                        "order_date": row.order_date,
                        "hour": row.hour,
                        "day_of_week": row.day_of_week,
                        "is_weekend": row.is_weekend,
                        "meal_idx": row.meal_idx,
                        "restaurant_idx": row.restaurant_idx,
                        "category_idx": row.category_idx,
                        "count": 0,
                        "label": 0,
                    }
                )
        return pd.DataFrame(negatives)

    train_neg = sample_period_negatives(train_pos, random_seed=42)
    test_neg = sample_period_negatives(test_pos, random_seed=43)
    train_data = (
        pd.concat([train_pos, train_neg], ignore_index=True)
        .sample(frac=1, random_state=42)
        .reset_index(drop=True)
    )
    test_data = (
        pd.concat([test_pos, test_neg], ignore_index=True)
        .sample(frac=1, random_state=42)
        .reset_index(drop=True)
    )

    print(
        "Temporal split preserves order_date: "
        f"cutoff={cutoff_date.date()}, train positives={len(train_pos):,}, "
        f"test positives={len(test_pos):,}.",
        flush=True,
    )
    print(
        "Negative sampling is period-local: "
        f"train negatives={len(train_neg):,}, test negatives={len(test_neg):,}.",
        flush=True,
    )
    return train_data, test_data, cutoff_date


class FeatureBuilder:
    def __init__(self, df: pd.DataFrame):
        self.n_users = int(df["user_idx"].nunique())
        self.n_items = int(df["item_idx"].nunique())
        self.n_meals = int(df["meal_idx"].nunique())
        self.n_restaurants = int(df["restaurant_idx"].nunique())
        self.n_categories = int(df["category_idx"].nunique())

    def build(self, data: pd.DataFrame, config: str = "full") -> csr_matrix:
        n = len(data)
        rows = np.arange(n)
        user_features = csr_matrix(
            (np.ones(n), (rows, data["user_idx"].to_numpy())),
            shape=(n, self.n_users),
        )
        item_features = csr_matrix(
            (np.ones(n), (rows, data["item_idx"].to_numpy())),
            shape=(n, self.n_items),
        )
        features = [user_features, item_features]

        if config in ["meal", "meal_day", "full"]:
            meal_features = csr_matrix(
                (np.ones(n), (rows, data["meal_idx"].to_numpy())),
                shape=(n, self.n_meals),
            )
            features.append(meal_features)

        if config in ["meal_day", "full"]:
            day_features = csr_matrix(
                (np.ones(n), (rows, data["day_of_week"].to_numpy())),
                shape=(n, 7),
            )
            weekend_feature = csr_matrix(data["is_weekend"].to_numpy().reshape(-1, 1))
            features.extend([day_features, weekend_feature])

        if config == "full":
            hour_feature = csr_matrix((data["hour"].to_numpy() / 23.0).reshape(-1, 1))
            restaurant_features = csr_matrix(
                (np.ones(n), (rows, data["restaurant_idx"].to_numpy())),
                shape=(n, self.n_restaurants),
            )
            category_features = csr_matrix(
                (np.ones(n), (rows, data["category_idx"].to_numpy())),
                shape=(n, self.n_categories),
            )
            features.extend([hour_feature, restaurant_features, category_features])

        return hstack(features, format="csr")


class FactorizationMachine:
    def __init__(
        self,
        n_features: int,
        n_factors: int = 20,
        lr: float = 0.05,
        reg: float = 0.001,
        n_epochs: int = 50,
        batch_size: int = 64,
    ):
        self.n_features = n_features
        self.n_factors = n_factors
        self.lr = lr
        self.reg = reg
        self.n_epochs = n_epochs
        self.batch_size = batch_size
        self.w0 = 0.0
        self.w = np.zeros(n_features)
        self.V = np.random.normal(0, 0.01, (n_features, n_factors))

    @staticmethod
    def _sigmoid(x: np.ndarray) -> np.ndarray:
        return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))

    @staticmethod
    def _log_loss(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        eps = 1e-15
        y_pred = np.clip(y_pred, eps, 1 - eps)
        return float(-np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred)))

    def _predict_raw(self, x_matrix: csr_matrix, x_sq: csr_matrix | None = None) -> np.ndarray:
        if x_sq is None:
            x_sq = x_matrix.power(2)
        linear = self.w0 + x_matrix.dot(self.w)
        xv = x_matrix.dot(self.V)
        xv_sq = x_sq.dot(self.V**2)
        interactions = 0.5 * np.sum(xv**2 - xv_sq, axis=1)
        return np.asarray(linear).ravel() + np.asarray(interactions).ravel()

    def predict_proba(self, x_matrix: csr_matrix) -> np.ndarray:
        return self._sigmoid(self._predict_raw(x_matrix))

    def fit(
        self,
        x_train: csr_matrix,
        y_train: np.ndarray,
        x_val: csr_matrix | None = None,
        y_val: np.ndarray | None = None,
    ) -> None:
        n_samples = x_train.shape[0]
        x_train_sq = x_train.power(2)
        indices = np.arange(n_samples)
        for epoch in range(self.n_epochs):
            np.random.shuffle(indices)
            epoch_loss = 0.0
            batches = 0
            for start in range(0, n_samples, self.batch_size):
                batch_idx = indices[start : start + self.batch_size]
                x_b = x_train[batch_idx]
                x_b_sq = x_train_sq[batch_idx]
                y_b = y_train[batch_idx]
                preds = self._sigmoid(self._predict_raw(x_b, x_b_sq))
                error = preds - y_b
                bsz = len(y_b)

                self.w0 -= self.lr * float(np.mean(error))
                grad_w = np.asarray(x_b.T.dot(error)).ravel() / bsz + self.reg * self.w
                self.w -= self.lr * grad_w

                xv = x_b.dot(self.V)
                term1 = x_b.T.dot(error[:, None] * xv) / bsz
                term2_scale = np.asarray(x_b_sq.T.dot(error)).ravel() / bsz
                grad_v = np.asarray(term1) - term2_scale[:, None] * self.V + self.reg * self.V
                self.V -= self.lr * grad_v

                epoch_loss += self._log_loss(y_b, preds)
                batches += 1

            if x_val is not None and y_val is not None:
                val_pred = self.predict_proba(x_val)
                val_loss = self._log_loss(y_val, val_pred)
                print(
                    f"Epoch {epoch + 1:02d}/{self.n_epochs} - "
                    f"loss={epoch_loss / batches:.4f} - val_loss={val_loss:.4f}",
                    flush=True,
                )
            else:
                print(
                    f"Epoch {epoch + 1:02d}/{self.n_epochs} - loss={epoch_loss / batches:.4f}",
                    flush=True,
                )


def ranking_metrics_for_user(actual_items: set[int], recommended_items: list[int], k: int) -> dict[str, float]:
    rec_k = recommended_items[:k]
    hits = len(set(rec_k) & actual_items)
    precision = hits / k
    recall = hits / len(actual_items) if actual_items else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    dcg = 0.0
    for idx, item in enumerate(rec_k):
        if item in actual_items:
            dcg += 1.0 / math.log2(idx + 2)
    ideal_hits = min(len(actual_items), k)
    idcg = sum(1.0 / math.log2(idx + 2) for idx in range(ideal_hits))
    ndcg = dcg / idcg if idcg else 0.0
    return {
        f"precision@{k}": precision,
        f"recall@{k}": recall,
        f"f1@{k}": f1,
        f"ndcg@{k}": ndcg,
    }


def evaluate_fm_recommendations(
    fm_model: FactorizationMachine,
    test_data: pd.DataFrame,
    feature_builder: FeatureBuilder,
    config: str,
    top_k: int = TOP_K,
) -> dict[str, float]:
    positive_test = test_data[test_data["label"] == 1].copy()
    contexts = [
        "user_idx",
        "hour",
        "day_of_week",
        "is_weekend",
        "meal_idx",
        "restaurant_idx",
    ]
    all_items = sorted(test_data["item_idx"].unique())
    metrics = []
    grouped = positive_test.groupby(contexts)["item_idx"].agg(lambda s: set(s)).reset_index()
    print(f"Ranking evaluation contexts for {config}: {len(grouped):,}", flush=True)
    for row in grouped.itertuples(index=False):
        actual_items = row.item_idx
        n_items = len(all_items)
        candidates = pd.DataFrame(
            {
                "user_idx": [row.user_idx] * n_items,
                "item_idx": all_items,
                "hour": [row.hour] * n_items,
                "day_of_week": [row.day_of_week] * n_items,
                "is_weekend": [row.is_weekend] * n_items,
                "meal_idx": [row.meal_idx] * n_items,
                "restaurant_idx": [row.restaurant_idx] * n_items,
                "category_idx": [0] * n_items,
            }
        )
        scores = fm_model.predict_proba(feature_builder.build(candidates, config=config))
        ranked_items = [item for _, item in sorted(zip(scores, all_items), reverse=True)]
        metrics.append(ranking_metrics_for_user(actual_items, ranked_items, top_k))

    return pd.DataFrame(metrics).mean().to_dict()


def train_temporal_fm() -> pd.DataFrame:
    np.random.seed(RANDOM_SEED)
    df, _ = prepare_fm_frame()
    train_data, test_data, _ = build_temporal_samples(df)
    feature_builder = FeatureBuilder(df)
    y_train = train_data["label"].to_numpy(dtype=float)
    y_test = test_data["label"].to_numpy(dtype=float)
    configs = {
        "user_item": "User + Item",
        "full": "User + Item + Meal + Day + Weekend + Hour + Restaurant + Category",
    }
    rows = []
    for config_key, config_name in configs.items():
        print(f"\nTraining temporal FM config: {config_name}", flush=True)
        x_train = feature_builder.build(train_data, config=config_key)
        x_test = feature_builder.build(test_data, config=config_key)
        print(
            f"Features={x_train.shape[1]}, train={x_train.shape[0]:,}, test={x_test.shape[0]:,}, "
            "epochs=50, batch_size=64",
            flush=True,
        )
        model = FactorizationMachine(
            n_features=x_train.shape[1],
            n_factors=20,
            lr=0.05,
            reg=0.001,
            n_epochs=50,
            batch_size=64,
        )
        model.fit(x_train, y_train, x_test, y_test)
        test_pred = model.predict_proba(x_test)
        threshold = np.percentile(test_pred, 100 * (1 - y_test.mean()))
        test_binary = (test_pred >= threshold).astype(int)
        rec_metrics = evaluate_fm_recommendations(
            model,
            test_data,
            feature_builder,
            config_key,
            top_k=TOP_K,
        )
        row = {
            "model": f"FM ({config_name})",
            "split_method": "temporal",
            "test_loss": model._log_loss(y_test, test_pred),
            "accuracy": accuracy_score(y_test, test_binary),
            "precision": precision_score(y_test, test_binary, zero_division=0),
            "recall": recall_score(y_test, test_binary, zero_division=0),
            "f1": f1_score(y_test, test_binary, zero_division=0),
            "auc": roc_auc_score(y_test, test_pred),
        }
        row.update(rec_metrics)
        rows.append(row)
        print(
            f"Completed {config_name}: AUC={row['auc']:.4f}, F1={row['f1']:.4f}, "
            f"F1@5={row[f'f1@{TOP_K}']:.4f}, NDCG@5={row[f'ndcg@{TOP_K}']:.4f}",
            flush=True,
        )

    fm_temporal = pd.DataFrame(rows)
    for output_path in [
        MODULE1_FINAL_DIR / "fm_temporal_evaluation_results.csv",
        METRICS_DIR / "fm_temporal_evaluation_results.csv",
    ]:
        fm_temporal.to_csv(output_path, index=False)
        print(f"Saved: {output_path}", flush=True)
    return fm_temporal


def metric_value(row: pd.Series | dict[str, float], metric: str) -> float:
    if isinstance(row, dict):
        return float(row[metric])
    return float(row[metric])


def build_comparison(fm_temporal: pd.DataFrame) -> pd.DataFrame:
    random_table = pd.read_csv(MODULE1_FINAL_DIR / "full_model_comparison.csv")
    fm_random = pd.read_csv(MODULE1_FINAL_DIR / "fm_evaluation_results.csv")
    svd_temporal = pd.read_csv(MODULE1_FINAL_DIR / "svd_temporal_evaluation_results.csv")
    als_temporal = pd.read_csv(MODULE1_FINAL_DIR / "als_temporal_evaluation_results.csv")

    random_lookup = {
        "Popularity Baseline": random_table[random_table["model"].eq("Popularity Baseline")].iloc[0],
        "SVD": random_table[random_table["model"].str.startswith("SVD")].iloc[0],
        "ALS": random_table[random_table["model"].str.startswith("ALS")].iloc[0],
        "FM (user+item)": fm_random[fm_random["model"].eq("FM (User + Item)")].iloc[0],
        "FM (full context)": fm_random[fm_random["model"].str.contains("Hour", regex=False)].iloc[0],
    }
    temporal_lookup = {
        "Popularity Baseline": svd_temporal[svd_temporal["model"].eq("Popularity Baseline")].iloc[0],
        "SVD": svd_temporal[svd_temporal["model"].str.startswith("SVD")].iloc[0],
        "ALS": als_temporal[als_temporal["model"].str.contains("Final", regex=False)].iloc[0],
        "FM (user+item)": fm_temporal[fm_temporal["model"].eq("FM (User + Item)")].iloc[0],
        "FM (full context)": fm_temporal[fm_temporal["model"].str.contains("Hour", regex=False)].iloc[0],
    }

    rows = []
    ranking_metrics = ["precision@5", "recall@5", "f1@5", "ndcg@5"]
    classification_metrics = ["auc", "f1"]
    for model_name in ["Popularity Baseline", "SVD", "ALS", "FM (user+item)", "FM (full context)"]:
        random_row = random_lookup[model_name]
        temporal_row = temporal_lookup[model_name]
        row = {"model": model_name}
        for metric in ranking_metrics:
            random_col = metric.replace("@5", "@k")
            temporal_col = metric.replace("@5", "@k")
            row[f"random_{metric}"] = metric_value(
                random_row, metric if metric in random_row.index else random_col
            )
            row[f"temporal_{metric}"] = metric_value(
                temporal_row, metric if metric in temporal_row.index else temporal_col
            )
            row[f"delta_{metric}"] = row[f"temporal_{metric}"] - row[f"random_{metric}"]
        for metric in classification_metrics:
            row[f"random_classification_{metric}"] = (
                metric_value(random_row, metric)
                if model_name.startswith("FM") and metric in random_row.index
                else np.nan
            )
            row[f"temporal_classification_{metric}"] = (
                metric_value(temporal_row, metric)
                if model_name.startswith("FM") and metric in temporal_row.index
                else np.nan
            )
            row[f"delta_classification_{metric}"] = (
                row[f"temporal_classification_{metric}"] - row[f"random_classification_{metric}"]
                if model_name.startswith("FM")
                else np.nan
            )
        row["comparability_caveat"] = (
            "FM ranking task differs from SVD/ALS; compare directionally, not as a strict same-task benchmark."
            if model_name.startswith("FM")
            else ""
        )
        rows.append(row)

    comparison = pd.DataFrame(rows)
    comparison_path = METRICS_DIR / "recommendation_random_vs_temporal_comparison.csv"
    comparison.to_csv(comparison_path, index=False)
    print(f"Saved: {comparison_path}", flush=True)

    fp_src = MODULE1_FINAL_DIR / "fp_growth_temporal_rule_stability.csv"
    fp_dest = METRICS_DIR / "fpgrowth_temporal_rule_stability.csv"
    shutil.copyfile(fp_src, fp_dest)
    print(f"Saved: {fp_dest}", flush=True)
    return comparison


def apply_plot_style() -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 180,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.size": 10,
        }
    )


def generate_figures(comparison: pd.DataFrame) -> None:
    apply_plot_style()
    model_labels = comparison["model"].tolist()
    metrics = [
        ("precision@5", "Precision@5"),
        ("recall@5", "Recall@5"),
        ("f1@5", "F1@5"),
        ("ndcg@5", "NDCG@5"),
    ]
    colors = ["#e63946", "#457b9d"]

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    x = np.arange(len(model_labels))
    width = 0.36
    for ax, (metric, title) in zip(axes.ravel(), metrics):
        ax.bar(x - width / 2, comparison[f"random_{metric}"], width, label="Random split", color=colors[0])
        ax.bar(x + width / 2, comparison[f"temporal_{metric}"], width, label="Temporal split", color=colors[1])
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(model_labels, rotation=25, ha="right")
        ax.set_ylim(0, max(0.05, comparison[[f"random_{metric}", f"temporal_{metric}"]].to_numpy().max() * 1.25))
        ax.set_ylabel("Score")
    handles, labels = axes.ravel()[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False)
    fig.suptitle("Recommendation Random vs Temporal Split Comparison", y=1.02, fontsize=14, fontweight="bold")
    fig.tight_layout()
    grouped_path = FIGURES_DIR / "recommendation_random_vs_temporal_comparison.png"
    fig.savefig(grouped_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {grouped_path}", flush=True)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.bar(x - width / 2, comparison["random_f1@5"], width, label="Random split", color=colors[0])
    ax.bar(x + width / 2, comparison["temporal_f1@5"], width, label="Temporal split", color=colors[1])
    ax.set_xticks(x)
    ax.set_xticklabels(model_labels, rotation=25, ha="right")
    ax.set_ylabel("F1@5")
    ax.set_title("F1@5: Random vs Temporal Split")
    ax.set_ylim(0, max(0.05, comparison[["random_f1@5", "temporal_f1@5"]].to_numpy().max() * 1.25))
    ax.legend(frameon=False)
    fig.tight_layout()
    f1_path = FIGURES_DIR / "recommendation_f1_random_vs_temporal.png"
    fig.savefig(f1_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {f1_path}", flush=True)

    fp = pd.read_csv(METRICS_DIR / "fpgrowth_temporal_rule_stability.csv")
    fp_lookup = fp.set_index("metric")
    fp_metrics = [
        ("Rules at threshold", "Rule Count", 1.0),
        ("Mean confidence", "Mean Confidence", 100.0),
        ("Mean lift", "Mean Lift", 1.0),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for ax, (metric, title, scale) in zip(axes, fp_metrics):
        values = [
            float(fp_lookup.loc[metric, "full_data_current"]) * scale,
            float(fp_lookup.loc[metric, "train_mined_test_evaluated"]) * scale,
        ]
        ax.bar(["Full data", "Train mined\nTest evaluated"], values, color=["#e63946", "#2a9d8f"])
        ax.set_title(title)
        ax.set_ylabel("Percent" if scale == 100.0 else "Value")
        for idx, value in enumerate(values):
            label = f"{value:.1f}%" if scale == 100.0 else f"{value:.2f}" if metric != "Rules at threshold" else f"{value:.0f}"
            ax.text(idx, value, label, ha="center", va="bottom", fontsize=9)
        ax.set_ylim(0, max(values) * 1.22)
    fig.suptitle("FP-Growth Rule Stability Under Temporal Evaluation", y=1.03, fontsize=14, fontweight="bold")
    fig.tight_layout()
    fp_path = FIGURES_DIR / "fpgrowth_rule_stability.png"
    fig.savefig(fp_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {fp_path}", flush=True)


def write_interpretation(comparison: pd.DataFrame) -> None:
    fp = pd.read_csv(METRICS_DIR / "fpgrowth_temporal_rule_stability.csv").set_index("metric")
    ranked_random = comparison.sort_values("random_f1@5", ascending=False)
    ranked_temporal = comparison.sort_values("temporal_f1@5", ascending=False)
    degraded = comparison.assign(abs_f1_drop=lambda d: d["delta_f1@5"].abs()).sort_values("delta_f1@5")
    svd = comparison[comparison["model"].eq("SVD")].iloc[0]
    als = comparison[comparison["model"].eq("ALS")].iloc[0]
    pop = comparison[comparison["model"].eq("Popularity Baseline")].iloc[0]
    fm_full = comparison[comparison["model"].eq("FM (full context)")].iloc[0]

    rule_count_full = float(fp.loc["Rules at threshold", "full_data_current"])
    rule_count_temporal = float(fp.loc["Rules at threshold", "train_mined_test_evaluated"])
    conf_full = float(fp.loc["Mean confidence", "full_data_current"])
    conf_temporal = float(fp.loc["Mean confidence", "train_mined_test_evaluated"])
    lift_full = float(fp.loc["Mean lift", "full_data_current"])
    lift_temporal = float(fp.loc["Mean lift", "train_mined_test_evaluated"])

    lines = [
        "# Temporal Split Interpretation",
        "",
        "The temporal split is the stricter evaluation because every training interaction occurs before the test period. "
        "This removes the main future-information path created by random row-level hold-outs.",
        "",
        "## Degradation Pattern",
        "",
        f"The largest F1@5 drop is {degraded.iloc[0]['model']} "
        f"({degraded.iloc[0]['random_f1@5']:.3f} -> {degraded.iloc[0]['temporal_f1@5']:.3f}, "
        f"delta {degraded.iloc[0]['delta_f1@5']:+.3f}). SVD and ALS are the main degradations under the shared "
        "future-item ranking interpretation.",
        "",
        f"The expected largest FM degradation did not appear in this exact run. FM full context changes from "
        f"{fm_full['random_f1@5']:.3f} to {fm_full['temporal_f1@5']:.3f}, and its classification AUC changes from "
        f"{fm_full['random_classification_auc']:.3f} to {fm_full['temporal_classification_auc']:.3f}. This should not be "
        "read as evidence that FM is strictly better than SVD/ALS; it is a warning that the FM ranking protocol and "
        "period-local negative-sampling task are not directly comparable to the SVD/ALS held-out-item task.",
        "",
        "## Model Ranking",
        "",
        f"Random-split winner by F1@5: {ranked_random.iloc[0]['model']} "
        f"({ranked_random.iloc[0]['random_f1@5']:.3f}). "
        f"Temporal-split winner by F1@5: {ranked_temporal.iloc[0]['model']} "
        f"({ranked_temporal.iloc[0]['temporal_f1@5']:.3f}).",
        "",
        f"The SVD-over-ALS ordering held: SVD is {svd['temporal_f1@5']:.3f} and ALS is "
        f"{als['temporal_f1@5']:.3f}. The margin remains thin, so the conclusion should be stated as "
        "SVD slightly ahead, not decisively superior.",
        "",
        f"SVD also remains above the popularity baseline: {svd['temporal_f1@5']:.3f} vs "
        f"{pop['temporal_f1@5']:.3f}. The advantage narrowed under temporal evaluation but is still about "
        f"{svd['temporal_f1@5'] / pop['temporal_f1@5']:.1f}x.",
        "",
        "## FP-Growth Stability",
        "",
        f"FP-Growth retained {rule_count_temporal:.0f} train-mined/test-evaluated rules versus "
        f"{rule_count_full:.0f} full-data rules. The surviving rules are stronger: confidence moves from "
        f"{conf_full:.1%} to {conf_temporal:.1%}, and lift moves from {lift_full:.2f} to "
        f"{lift_temporal:.2f}. This supports the interpretation that the remaining association rules capture "
        "temporally stable basket structure.",
        "",
        "## Hybrid Recommendation Implications",
        "",
        "The hybrid should keep FP-Growth as basket-level support, especially for item-to-item add-ons and "
        "cold-start contexts. SVD/ALS remain the cleaner evidence for personalization under the temporal task. "
        "FM remains useful for context-sensitive re-ranking, but temporal metrics should be used when describing "
        "expected deployment performance.",
        "",
        "## FM/SVD Comparability Caveat",
        "",
        "The FM ranking task is not identical to the SVD/ALS hold-out task. SVD and ALS rank future held-out "
        "items per user; the FM evaluation ranks items inside user/context groups built from positive rows plus "
        "period-local negative samples. FM comparisons are therefore directional and leakage-focused, not a strict "
        "apples-to-apples replacement benchmark.",
        "",
        "## FM Temporal Classification Metrics",
        "",
    ]
    fm_rows = comparison[comparison["model"].str.startswith("FM")]
    for row in fm_rows.itertuples(index=False):
        lines.append(
            f"- {row.model}: temporal AUC={row.temporal_classification_auc:.3f}, "
            f"temporal classification F1={row.temporal_classification_f1:.3f}."
        )
    lines.append("")

    report_path = REPORTS_DIR / "temporal_split_interpretation.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved: {report_path}", flush=True)


def print_generated_paths() -> None:
    paths = [
        FIGURES_DIR / "recommendation_random_vs_temporal_comparison.png",
        FIGURES_DIR / "recommendation_f1_random_vs_temporal.png",
        FIGURES_DIR / "fpgrowth_rule_stability.png",
        METRICS_DIR / "recommendation_random_vs_temporal_comparison.csv",
        METRICS_DIR / "fpgrowth_temporal_rule_stability.csv",
        METRICS_DIR / "fm_temporal_evaluation_results.csv",
        REPORTS_DIR / "temporal_split_interpretation.md",
        MODULE1_FINAL_DIR / "fm_temporal_evaluation_results.csv",
    ]
    print("\nGenerated files:", flush=True)
    for path in paths:
        print(str(path), flush=True)


def main() -> None:
    ensure_dirs()
    fm_temporal = train_temporal_fm()
    comparison = build_comparison(fm_temporal)
    generate_figures(comparison)
    write_interpretation(comparison)
    print_generated_paths()


if __name__ == "__main__":
    main()
