from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from generator_validation_plots import FIGURES_DIR, MONTHS, DataBundle, ensure_dirs, load_data, set_style


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


def plot_weekday_panel(ax: plt.Axes, data: DataBundle) -> None:
    overall = (
        data.active_orders.groupby(["weekday_num", "weekday"], observed=True)
        .size()
        .reset_index(name="order_count")
        .sort_values("weekday_num")
    )
    ax.bar(overall["weekday"].astype(str), overall["order_count"], color="#4c78a8")
    ax.set_title("Overall Order Volume by Weekday")
    ax.set_ylabel("Orders")
    ax.set_xlabel("Day of week")


def plot_hourly_panel(ax: plt.Axes, data: DataBundle) -> None:
    overall = data.active_orders.groupby("hour").size().reset_index(name="order_count")
    ax.bar(overall["hour"], overall["order_count"], color="#4c78a8")
    ax.set_title("Overall Orders by Hour")
    ax.set_xlabel("Hour")
    ax.set_ylabel("Orders")
    ax.set_xticks(range(0, 24, 2))


def plot_item_seasonality_panel(ax: plt.Axes, data: DataBundle) -> None:
    chosen_items = ["Iced Latte", "Oatmeal with Berries"]
    item_data = data.active_lines[data.active_lines["item_name"].isin(chosen_items)].copy()
    seasonality = (
        item_data.groupby(["item_name", "month", "month_name"], observed=True)
        .size()
        .reset_index(name="line_count")
        .sort_values(["item_name", "month"])
    )
    full_grid = pd.MultiIndex.from_product(
        [chosen_items, range(1, 13)], names=["item_name", "month"]
    ).to_frame(index=False)
    full_grid["month_name"] = pd.Categorical(
        full_grid["month"].map(dict(enumerate(MONTHS, start=1))),
        categories=MONTHS,
        ordered=True,
    )
    seasonality = full_grid.merge(
        seasonality[["item_name", "month", "line_count"]],
        on=["item_name", "month"],
        how="left",
    ).fillna({"line_count": 0})
    seasonality["month_name"] = pd.Categorical(
        seasonality["month"].map(dict(enumerate(MONTHS, start=1))),
        categories=MONTHS,
        ordered=True,
    )

    colors = {"Iced Latte": "#4c78a8", "Oatmeal with Berries": "#8c564b"}
    for item in chosen_items:
        item_curve = seasonality[seasonality["item_name"].eq(item)]
        ax.plot(
            item_curve["month_name"].astype(str),
            item_curve["line_count"],
            marker="o",
            linewidth=2.2,
            label=item,
            color=colors[item],
        )
    ax.set_title("Item Seasonality: Summer vs Winter Item")
    ax.set_xlabel("Month")
    ax.set_ylabel("Order lines across 2023-2025")
    ax.legend(loc="upper left")


def plot_revenue_panel(ax: plt.Axes, data: DataBundle) -> None:
    monthly = (
        data.active_orders.groupby("year_month")
        .agg(total_revenue=("revenue", "sum"), order_count=("order_id", "count"))
        .reset_index()
        .sort_values("year_month")
    )
    monthly["month_index"] = np.arange(len(monthly))
    coef = np.polyfit(monthly["month_index"], monthly["total_revenue"], 1)
    monthly["trend_revenue"] = np.polyval(coef, monthly["month_index"])
    trend_growth = (monthly["trend_revenue"].iloc[-1] / monthly["trend_revenue"].iloc[0]) - 1

    ax.plot(
        monthly["year_month"],
        monthly["total_revenue"],
        marker="o",
        markersize=4,
        linewidth=1.5,
        color="#4c78a8",
        label="Monthly revenue",
    )
    ax.plot(
        monthly["year_month"],
        monthly["trend_revenue"],
        linewidth=2.2,
        color="#e45756",
        label=f"Fitted trend: {trend_growth:.1%}/year",
    )
    ax.set_title("Monthly Revenue with Fitted Linear Trend")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.legend(loc="upper left")
    ax.text(
        0.98,
        0.05,
        "Injected baseline growth: 15%/year\n"
        f"Fitted trend: {trend_growth:.1%}/year\n"
        "(baseline + seasonal and holiday effects)",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#cccccc"},
    )


def save_overview(data: DataBundle) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    panels = [
        ("A", axes[0, 0], plot_weekday_panel),
        ("B", axes[0, 1], plot_hourly_panel),
        ("C", axes[1, 0], plot_item_seasonality_panel),
        ("D", axes[1, 1], plot_revenue_panel),
    ]
    for label, ax, plotter in panels:
        plotter(ax, data)
        add_panel_label(ax, label)

    fig.suptitle("Generator Validation: Demand Structure Checks", fontsize=15, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    output_path = FIGURES_DIR / "generator_validation_overview.png"
    fig.savefig(output_path, bbox_inches="tight", dpi=180)
    plt.close(fig)
    print(f"Saved: {output_path}")


def main() -> None:
    ensure_dirs()
    set_style()
    save_overview(load_data())


if __name__ == "__main__":
    main()
