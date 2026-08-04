from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch


SCRIPT_DIR = Path(__file__).resolve().parent
AI_ROOT = SCRIPT_DIR.parents[2]
SOURCE_PATH = AI_ROOT / "data" / "final" / "Module 4" / "stability" / "segmentation_k2_vs_k5_comparison.csv"
FIGURE_DIR = SCRIPT_DIR / "figures"
OUTPUT_PATH = FIGURE_DIR / "segmentation_k2_vs_k5_stability_comparison.png"

EXPECTED = {
    2: {"silhouette": 0.164, "pairwise_seed_ari_mean": 0.9999},
    5: {"silhouette": 0.100, "pairwise_seed_ari_mean": 0.9974},
}
COLORS = {2: "#64748B", 5: "#E3344F"}


def set_style() -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 180,
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": False,
        }
    )


def load_comparison() -> pd.DataFrame:
    comparison = pd.read_csv(SOURCE_PATH)
    comparison["k"] = comparison["k"].astype(int)
    comparison = comparison[comparison["k"].isin([2, 5])].sort_values("k")
    if len(comparison) != 2:
        raise ValueError(f"Expected K=2 and K=5 rows in {SOURCE_PATH}")
    return comparison


def discrepancy_notes(comparison: pd.DataFrame) -> list[str]:
    notes = []
    for row in comparison.itertuples(index=False):
        expected = EXPECTED[int(row.k)]
        if round(float(row.silhouette), 3) != round(expected["silhouette"], 3):
            notes.append(
                f"K={int(row.k)} silhouette differs: saved={float(row.silhouette):.6f}, "
                f"expected~={expected['silhouette']:.3f}"
            )
        if round(float(row.pairwise_seed_ari_mean), 4) != round(
            expected["pairwise_seed_ari_mean"], 4
        ):
            notes.append(
                f"K={int(row.k)} seed ARI differs: saved={float(row.pairwise_seed_ari_mean):.6f}, "
                f"expected~={expected['pairwise_seed_ari_mean']:.4f}"
            )
    return notes


def add_panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.12,
        1.08,
        label,
        transform=ax.transAxes,
        fontsize=12,
        fontweight="bold",
        va="top",
        ha="left",
    )


def annotate_bars(ax: plt.Axes, values: pd.Series, fmt: str, y_offset: float) -> None:
    for patch, value in zip(ax.patches, values):
        ax.text(
            patch.get_x() + patch.get_width() / 2,
            patch.get_height() + y_offset,
            fmt.format(value),
            ha="center",
            va="bottom",
            fontsize=9,
        )


def create_figure(comparison: pd.DataFrame) -> Path:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    labels = [f"K={k}" for k in comparison["k"]]
    colors = [COLORS[int(k)] for k in comparison["k"]]
    x = np.arange(len(comparison))

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))

    axes[0].bar(x, comparison["silhouette"], color=colors, width=0.58)
    axes[0].set_title("Statistical Separation")
    axes[0].set_xticks(x, labels)
    axes[0].set_ylabel("Silhouette score")
    axes[0].set_ylim(0, 0.25)
    annotate_bars(axes[0], comparison["silhouette"], "{:.3f}", 0.006)
    add_panel_label(axes[0], "A")

    axes[1].bar(x, comparison["pairwise_seed_ari_mean"], color=colors, width=0.58)
    axes[1].set_title("Reproducibility")
    axes[1].set_xticks(x, labels)
    axes[1].set_ylabel("Mean pairwise seed ARI")
    axes[1].set_ylim(0.95, 1.0)
    axes[1].text(
        0.02,
        0.04,
        "Zoomed y-axis",
        transform=axes[1].transAxes,
        ha="left",
        va="bottom",
        fontsize=9,
        color="#374151",
    )
    annotate_bars(axes[1], comparison["pairwise_seed_ari_mean"], "{:.4f}", 0.001)
    add_panel_label(axes[1], "B")

    legend_handles = [Patch(facecolor=COLORS[k], label=f"K={k}") for k in [2, 5]]
    fig.legend(handles=legend_handles, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 0.93))
    fig.suptitle("K = 2 vs K = 5: Separation and Stability Trade-off", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(OUTPUT_PATH, bbox_inches="tight", dpi=180)
    plt.close(fig)
    return OUTPUT_PATH


def main() -> None:
    set_style()
    comparison = load_comparison()
    notes = discrepancy_notes(comparison)
    for note in notes:
        print(f"DISCREPANCY: {note}")
    output_path = create_figure(comparison)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
