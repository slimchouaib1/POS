from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
AI_ROOT = ROOT / "backend" / "Ai models"
RAW_DIR = AI_ROOT / "data" / "raw"
OUT_DIR = AI_ROOT / "notebooks" / "GeneratorValidation"
FIGURES_DIR = OUT_DIR / "figures"
METRICS_DIR = OUT_DIR / "metrics"
SUMMARY_PATH = OUT_DIR / "generator_validation_summary.md"

RAMADAN_PERIODS = [
    ("2023", pd.Timestamp("2023-03-23"), pd.Timestamp("2023-04-21")),
    ("2024", pd.Timestamp("2024-03-11"), pd.Timestamp("2024-04-09")),
    ("2025", pd.Timestamp("2025-03-01"), pd.Timestamp("2025-03-30")),
]

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


@dataclass
class DataBundle:
    lines: pd.DataFrame
    active_lines: pd.DataFrame
    orders: pd.DataFrame
    active_orders: pd.DataFrame
    customers: pd.DataFrame
    anomalies: pd.DataFrame


def ensure_dirs() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)


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


def parse_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().eq("true")


def load_data() -> DataBundle:
    lines = pd.read_csv(RAW_DIR / "enterprise_pos_dataset.csv", sep="|")
    lines["order_date"] = pd.to_datetime(lines["order_date"])
    parsed_time = pd.to_datetime(lines["order_time"], format="%I:%M %p", errors="coerce")
    if parsed_time.isna().any():
        parsed_time = parsed_time.fillna(pd.to_datetime(lines["order_time"], errors="coerce"))
    lines["hour"] = parsed_time.dt.hour.astype(int)
    lines["weekday_num"] = lines["order_date"].dt.dayofweek.astype(int)
    lines["weekday"] = pd.Categorical(
        lines["weekday_num"].map(dict(enumerate(DAYS))), categories=DAYS, ordered=True
    )
    lines["month"] = lines["order_date"].dt.month.astype(int)
    lines["month_name"] = pd.Categorical(
        lines["month"].map(dict(enumerate(MONTHS, start=1))), categories=MONTHS, ordered=True
    )
    lines["year_month"] = lines["order_date"].dt.to_period("M").dt.to_timestamp()
    lines["is_voided_bool"] = parse_bool(lines["is_voided"])
    lines["line_total"] = pd.to_numeric(lines["line_total"], errors="coerce").fillna(0.0)

    orders = (
        lines.sort_values("order_details_id")
        .groupby("order_id", as_index=False)
        .agg(
            order_date=("order_date", "first"),
            order_time=("order_time", "first"),
            hour=("hour", "first"),
            weekday_num=("weekday_num", "first"),
            weekday=("weekday", "first"),
            month=("month", "first"),
            month_name=("month_name", "first"),
            year_month=("year_month", "first"),
            restaurant_type=("restaurant_type", "first"),
            customer_id=("customer_id", "first"),
            revenue=("line_total", "sum"),
            is_voided_bool=("is_voided_bool", "any"),
        )
    )
    orders["weekday"] = pd.Categorical(orders["weekday"], categories=DAYS, ordered=True)
    orders["month_name"] = pd.Categorical(orders["month_name"], categories=MONTHS, ordered=True)

    customers = pd.read_csv(RAW_DIR / "customers.csv")
    anomalies = pd.read_csv(RAW_DIR / "anomalies_ground_truth.csv")

    return DataBundle(
        lines=lines,
        active_lines=lines[~lines["is_voided_bool"]].copy(),
        orders=orders,
        active_orders=orders[~orders["is_voided_bool"]].copy(),
        customers=customers,
        anomalies=anomalies,
    )


def savefig(fig: plt.Figure, filename: str) -> Path:
    path = FIGURES_DIR / filename
    fig.savefig(path, bbox_inches="tight", dpi=180)
    plt.close(fig)
    print(f"Saved: {path}")
    return path


def plot_weekday_demand(data: DataBundle) -> dict[str, str]:
    overall = (
        data.active_orders.groupby(["weekday_num", "weekday"], observed=True)
        .size()
        .reset_index(name="order_count")
    )
    overall["restaurant_type"] = "Overall"
    section = (
        data.active_orders.groupby(["restaurant_type", "weekday_num", "weekday"], observed=True)
        .size()
        .reset_index(name="order_count")
    )
    weekday = pd.concat([overall, section], ignore_index=True)
    totals = weekday.groupby("restaurant_type")["order_count"].transform("sum")
    weekday["section_share"] = weekday["order_count"] / totals
    weekday_path = METRICS_DIR / "weekday_demand_pattern.csv"
    weekday.to_csv(weekday_path, index=False)
    print(f"Saved: {weekday_path}")

    pivot = weekday[weekday["restaurant_type"].ne("Overall")].pivot(
        index="weekday", columns="restaurant_type", values="section_share"
    )
    selected = [s for s in ["Cafe", "Steakhouse", "Italian", "Healthy_Vegan"] if s in pivot.columns]

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    axes[0].bar(overall["weekday"].astype(str), overall["order_count"], color="#4c78a8")
    axes[0].set_title("Overall Order Volume by Weekday")
    axes[0].set_ylabel("Orders")
    axes[0].set_xlabel("Day of week")

    colors = {
        "Cafe": "#f58518",
        "Steakhouse": "#e45756",
        "Italian": "#72b7b2",
        "Healthy_Vegan": "#2ca02c",
    }
    for section_name in selected:
        width = 2.8 if section_name == "Healthy_Vegan" else 1.8
        axes[1].plot(
            pivot.index.astype(str),
            pivot[section_name],
            marker="o",
            linewidth=width,
            color=colors.get(section_name),
            label=section_name,
        )
    axes[1].set_title("Weekday Share by Section")
    axes[1].set_ylabel("Share of section orders")
    axes[1].set_xlabel("Day of week")
    axes[1].legend()
    axes[1].yaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    fig.suptitle("Generated Weekday Demand Pattern", fontsize=14, fontweight="bold")
    fig.tight_layout()
    savefig(fig, "weekday_demand_pattern.png")

    hv = weekday[weekday["restaurant_type"].eq("Healthy_Vegan")]
    hv_weekday_share = hv[hv["weekday_num"].between(0, 3)]["order_count"].sum() / hv["order_count"].sum()
    return {
        "metric_csv": str(weekday_path),
        "summary": f"Overall demand peaks late week/weekend; Healthy_Vegan is comparatively weekday-heavy with Mon-Thu at {hv_weekday_share:.1%} of its orders.",
    }


def plot_hourly_demand(data: DataBundle) -> dict[str, str]:
    overall = data.active_orders.groupby("hour").size().reset_index(name="order_count")
    overall["restaurant_type"] = "Overall"
    section = (
        data.active_orders.groupby(["restaurant_type", "hour"])
        .size()
        .reset_index(name="order_count")
    )
    hourly = pd.concat([overall, section], ignore_index=True)
    hourly["section_total"] = hourly.groupby("restaurant_type")["order_count"].transform("sum")
    hourly["section_share"] = hourly["order_count"] / hourly["section_total"]
    hourly_path = METRICS_DIR / "hourly_demand_distribution.csv"
    hourly.to_csv(hourly_path, index=False)
    print(f"Saved: {hourly_path}")

    pivot = hourly[hourly["restaurant_type"].ne("Overall")].pivot(
        index="hour", columns="restaurant_type", values="section_share"
    )
    selected = [s for s in ["Cafe", "Steakhouse", "Italian", "Japanese"] if s in pivot.columns]

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    axes[0].bar(overall["hour"], overall["order_count"], color="#4c78a8")
    axes[0].set_title("Overall Orders by Hour")
    axes[0].set_xlabel("Hour")
    axes[0].set_ylabel("Orders")
    axes[0].set_xticks(range(0, 24, 2))

    colors = ["#f58518", "#e45756", "#72b7b2", "#54a24b"]
    for idx, section_name in enumerate(selected):
        axes[1].plot(
            pivot.index,
            pivot[section_name],
            marker="o",
            linewidth=2.2,
            color=colors[idx],
            label=section_name,
        )
    axes[1].set_title("Hourly Shape by Section")
    axes[1].set_xlabel("Hour")
    axes[1].set_ylabel("Share of section orders")
    axes[1].set_xticks(range(0, 24, 2))
    axes[1].yaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    axes[1].legend()
    fig.suptitle("Generated Hourly Demand Distribution", fontsize=14, fontweight="bold")
    fig.tight_layout()
    savefig(fig, "hourly_demand_distribution.png")

    cafe_peak = int(pivot["Cafe"].idxmax()) if "Cafe" in pivot else -1
    steak_peak = int(pivot["Steakhouse"].idxmax()) if "Steakhouse" in pivot else -1
    return {
        "metric_csv": str(hourly_path),
        "summary": f"Cafe peaks at {cafe_peak}:00, while Steakhouse peaks at {steak_peak}:00, matching the morning vs dinner demand structure.",
    }


def plot_item_seasonality(data: DataBundle) -> dict[str, str]:
    chosen_items = ["Iced Latte", "Espresso", "14oz Ribeye"]
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
        full_grid["month"].map(dict(enumerate(MONTHS, start=1))), categories=MONTHS, ordered=True
    )
    seasonality = full_grid.merge(
        seasonality[["item_name", "month", "line_count"]],
        on=["item_name", "month"],
        how="left",
    ).fillna({"line_count": 0})
    seasonality["month_name"] = pd.Categorical(
        seasonality["month"].map(dict(enumerate(MONTHS, start=1))), categories=MONTHS, ordered=True
    )
    seasonality_path = METRICS_DIR / "item_seasonality_summer_vs_winter.csv"
    seasonality.to_csv(seasonality_path, index=False)
    print(f"Saved: {seasonality_path}")

    fig, ax = plt.subplots(figsize=(10.5, 5))
    colors = {"Iced Latte": "#4c78a8", "Espresso": "#8c564b", "14oz Ribeye": "#e45756"}
    for item in chosen_items:
        item_curve = seasonality[seasonality["item_name"].eq(item)]
        ax.plot(
            item_curve["month_name"].astype(str),
            item_curve["line_count"],
            marker="o",
            linewidth=2.3,
            label=item,
            color=colors[item],
        )
    ax.set_title("Item Seasonality Across Calendar Months")
    ax.set_xlabel("Month")
    ax.set_ylabel("Order lines across 2023-2025")
    ax.legend()
    fig.tight_layout()
    savefig(fig, "item_seasonality_summer_vs_winter.png")

    peaks = (
        seasonality.sort_values("line_count")
        .groupby("item_name", observed=True)
        .tail(1)
        .set_index("item_name")["month_name"]
        .astype(str)
        .to_dict()
    )
    return {
        "metric_csv": str(seasonality_path),
        "summary": "Selected items show distinct monthly curves: "
        + ", ".join(f"{item} peaks in {month}" for item, month in peaks.items())
        + ".",
    }


def build_ramadan_daily(data: DataBundle) -> tuple[pd.DataFrame, pd.DataFrame]:
    date_range = pd.date_range(data.active_orders["order_date"].min(), data.active_orders["order_date"].max())
    groups = {
        "Cafe daytime": data.active_orders[
            data.active_orders["restaurant_type"].eq("Cafe") & data.active_orders["hour"].between(6, 17)
        ],
        "Steakhouse dinner": data.active_orders[
            data.active_orders["restaurant_type"].eq("Steakhouse") & data.active_orders["hour"].between(17, 23)
        ],
    }
    rows = []
    for group_name, frame in groups.items():
        counts = frame.groupby("order_date").size().reindex(date_range, fill_value=0)
        group_df = counts.reset_index()
        group_df.columns = ["order_date", "order_count"]
        group_df["group"] = group_name
        group_df["rolling_7d"] = group_df["order_count"].rolling(7, center=True, min_periods=1).mean()
        rows.append(group_df)
    daily = pd.concat(rows, ignore_index=True)
    daily["is_ramadan"] = False
    for _, start, end in RAMADAN_PERIODS:
        daily.loc[daily["order_date"].between(start, end), "is_ramadan"] = True

    summary_rows = []
    for year, start, end in RAMADAN_PERIODS:
        before_start = start - pd.Timedelta(days=30)
        after_end = end + pd.Timedelta(days=30)
        for group_name in groups:
            gd = daily[daily["group"].eq(group_name)]
            ramadan_avg = gd[gd["order_date"].between(start, end)]["order_count"].mean()
            baseline = gd[
                gd["order_date"].between(before_start, start - pd.Timedelta(days=1))
                | gd["order_date"].between(end + pd.Timedelta(days=1), after_end)
            ]["order_count"].mean()
            pct_change = (ramadan_avg - baseline) / baseline if baseline else np.nan
            summary_rows.append(
                {
                    "year": year,
                    "group": group_name,
                    "ramadan_start": start.date().isoformat(),
                    "ramadan_end": end.date().isoformat(),
                    "ramadan_avg_daily_orders": ramadan_avg,
                    "adjacent_baseline_avg_daily_orders": baseline,
                    "pct_change_vs_adjacent_baseline": pct_change,
                }
            )
    period_summary = pd.DataFrame(summary_rows)
    return daily, period_summary


def plot_ramadan_effect(data: DataBundle) -> dict[str, str]:
    daily, period_summary = build_ramadan_daily(data)
    daily_path = METRICS_DIR / "ramadan_demand_effect.csv"
    summary_path = METRICS_DIR / "ramadan_demand_effect_period_summary.csv"
    daily.to_csv(daily_path, index=False)
    period_summary.to_csv(summary_path, index=False)
    print(f"Saved: {daily_path}")
    print(f"Saved: {summary_path}")

    fig, axes = plt.subplots(2, 1, figsize=(13, 7), sharex=True)
    groups = [("Cafe daytime", "#f58518"), ("Steakhouse dinner", "#e45756")]
    for ax, (group_name, color) in zip(axes, groups):
        gd = daily[daily["group"].eq(group_name)]
        ax.plot(gd["order_date"], gd["rolling_7d"], color=color, linewidth=1.8, label="7-day rolling orders")
        ax.scatter(gd["order_date"], gd["order_count"], color=color, alpha=0.12, s=8, label="Daily orders")
        for year, start, end in RAMADAN_PERIODS:
            ax.axvspan(start, end, color="#6c757d", alpha=0.18)
            ax.text(
                start + (end - start) / 2,
                ax.get_ylim()[1] * 0.92,
                f"Ramadan {year}",
                ha="center",
                va="top",
                fontsize=8,
                color="#3a3a3a",
            )
        ax.set_title(group_name)
        ax.set_ylabel("Orders")
        ax.legend(loc="upper right")
    axes[-1].xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    axes[-1].set_xlabel("Date")
    fig.suptitle("Ramadan Demand Effect in Generated Orders", fontsize=14, fontweight="bold")
    fig.tight_layout()
    savefig(fig, "ramadan_demand_effect.png")

    cafe_change = period_summary[period_summary["group"].eq("Cafe daytime")][
        "pct_change_vs_adjacent_baseline"
    ].mean()
    steak_change = period_summary[period_summary["group"].eq("Steakhouse dinner")][
        "pct_change_vs_adjacent_baseline"
    ].mean()
    return {
        "metric_csv": f"{daily_path}; {summary_path}",
        "summary": f"Across the shaded Ramadan windows, Cafe daytime averages {cafe_change:.1%} vs adjacent periods while Steakhouse dinner averages {steak_change:.1%}.",
    }


def plot_customer_archetypes(data: DataBundle) -> dict[str, str]:
    order = ["regular", "occasional", "infrequent", "one_timer"]
    counts = data.customers["archetype"].value_counts().reindex(order).reset_index()
    counts.columns = ["archetype", "customer_count"]
    visit_counts = data.customers["actual_visits"].value_counts().sort_index().reset_index()
    visit_counts.columns = ["actual_visits", "customer_count"]
    combined_rows = []
    for row in counts.itertuples(index=False):
        combined_rows.append({"table": "archetype_counts", "category": row.archetype, "value": row.customer_count})
    for row in visit_counts.itertuples(index=False):
        combined_rows.append(
            {"table": "visit_distribution", "category": str(int(row.actual_visits)), "value": row.customer_count}
        )
    combined = pd.DataFrame(combined_rows)
    combined_path = METRICS_DIR / "customer_archetype_distribution.csv"
    combined.to_csv(combined_path, index=False)
    print(f"Saved: {combined_path}")

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    axes[0].bar(counts["archetype"], counts["customer_count"], color=["#4c78a8", "#72b7b2", "#f58518", "#e45756"])
    axes[0].set_title("Customers by Archetype")
    axes[0].set_xlabel("Archetype")
    axes[0].set_ylabel("Customers")
    axes[0].tick_params(axis="x", rotation=20)

    axes[1].bar(visit_counts["actual_visits"], visit_counts["customer_count"], color="#4c78a8")
    axes[1].set_title("Visits per Customer")
    axes[1].set_xlabel("Actual visits")
    axes[1].set_ylabel("Customers (log scale)")
    axes[1].set_yscale("log")
    fig.suptitle("Generated Customer Engagement Structure", fontsize=14, fontweight="bold")
    fig.tight_layout()
    savefig(fig, "customer_archetype_distribution.png")

    infrequent_share = counts[counts["archetype"].isin(["infrequent", "one_timer"])]["customer_count"].sum() / counts[
        "customer_count"
    ].sum()
    return {
        "metric_csv": str(combined_path),
        "summary": f"Infrequent and one-time customers account for {infrequent_share:.1%} of customers, and visits show a long right tail.",
    }


def plot_anomaly_distribution(data: DataBundle) -> dict[str, str]:
    anomaly_counts = (
        data.anomalies["anomaly_type"].value_counts().rename_axis("category").reset_index(name="count")
    )
    total_orders = data.orders["order_id"].nunique()
    anomaly_orders = data.anomalies["order_id"].nunique()
    normal_orders = total_orders - anomaly_orders
    rate_rows = pd.DataFrame(
        [
            {"category": "normal_orders", "count": normal_orders},
            {"category": "injected_anomaly_orders", "count": anomaly_orders},
        ]
    )
    combined = pd.concat(
        [
            anomaly_counts.assign(table="anomaly_type_counts"),
            rate_rows.assign(table="overall_rate"),
        ],
        ignore_index=True,
    )
    combined = combined[["table", "category", "count"]]
    combined_path = METRICS_DIR / "anomaly_type_distribution.csv"
    combined.to_csv(combined_path, index=False)
    print(f"Saved: {combined_path}")

    anomaly_rate = anomaly_orders / total_orders
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    sorted_counts = anomaly_counts.sort_values("count")
    axes[0].barh(sorted_counts["category"], sorted_counts["count"], color="#e45756")
    axes[0].set_title("Injected Anomaly Type Counts")
    axes[0].set_xlabel("Orders")
    axes[0].set_ylabel("Anomaly type")

    axes[1].bar(["Normal", "Injected anomaly"], [normal_orders, anomaly_orders], color=["#4c78a8", "#e45756"])
    axes[1].set_yscale("log")
    axes[1].set_title("Overall Order-Level Rate")
    axes[1].set_ylabel("Orders (log scale)")
    axes[1].text(
        1,
        anomaly_orders,
        f"{anomaly_rate:.2%}\ninjected/illustrative",
        ha="center",
        va="bottom",
        fontsize=10,
        color="#3a3a3a",
    )
    fig.suptitle("Generated Anomaly Labels Are Rare and Class-Imbalanced", fontsize=14, fontweight="bold")
    fig.tight_layout()
    savefig(fig, "anomaly_type_distribution.png")
    return {
        "metric_csv": str(combined_path),
        "summary": f"The ground-truth file contains {anomaly_orders:,} injected anomaly orders out of {total_orders:,} total orders ({anomaly_rate:.2%}).",
    }


def plot_revenue_growth(data: DataBundle) -> dict[str, str]:
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
    monthly_path = METRICS_DIR / "revenue_growth_trend.csv"
    monthly.to_csv(monthly_path, index=False)
    print(f"Saved: {monthly_path}")

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(monthly["year_month"], monthly["total_revenue"], marker="o", linewidth=1.8, color="#4c78a8", label="Monthly revenue")
    ax.plot(monthly["year_month"], monthly["trend_revenue"], linewidth=2.4, color="#e45756", label="Linear trend")
    ax.set_title("Monthly Revenue Trend in Generated Data")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.legend()
    ax.text(
        0.02,
        0.93,
        f"Fitted trend growth: {trend_growth:.1%}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#cccccc"},
    )
    fig.tight_layout()
    savefig(fig, "revenue_growth_trend.png")
    return {
        "metric_csv": str(monthly_path),
        "summary": f"Monthly revenue has a positive fitted trend of {trend_growth:.1%} from Jan 2023 to Dec 2025.",
    }


def write_summary(results: dict[str, dict[str, str]]) -> None:
    rows = [
        (
            "Weekday demand pattern",
            "figures/weekday_demand_pattern.png",
            results["weekday"]["summary"],
        ),
        (
            "Meal-period / hourly demand",
            "figures/hourly_demand_distribution.png",
            results["hourly"]["summary"],
        ),
        (
            "Item seasonality",
            "figures/item_seasonality_summer_vs_winter.png",
            results["seasonality"]["summary"],
        ),
        (
            "Ramadan effect",
            "figures/ramadan_demand_effect.png",
            results["ramadan"]["summary"],
        ),
        (
            "Customer archetype distribution",
            "figures/customer_archetype_distribution.png",
            results["customers"]["summary"],
        ),
        (
            "Anomaly type breakdown",
            "figures/anomaly_type_distribution.png",
            results["anomalies"]["summary"] + " Rates are injected/illustrative, not empirical fraud statistics.",
        ),
        (
            "Growth trend",
            "figures/revenue_growth_trend.png",
            results["growth"]["summary"],
        ),
        (
            "Product affinity recovery",
            "Existing Module 1/01_fp_growth.ipynb, section 'Validation against injected affinities'",
            "Not duplicated here; the FP-Growth notebook already checks recovered association rules against the injected affinity pairs.",
        ),
    ]
    lines = [
        "# Generator Validation Summary",
        "",
        "All validation plots are computed from generated output CSV files only: `enterprise_pos_dataset.csv`, `customers.csv`, and `anomalies_ground_truth.csv`. The generator script was not read for parameter constants and the dataset was not regenerated.",
        "",
        "| Assumption | Plot or output | What the generated data shows | External citation placeholder |",
        "|---|---|---|---|",
    ]
    for assumption, plot, statement in rows:
        lines.append(f"| {assumption} | `{plot}` | {statement} |  |")
    lines.append("")
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved: {SUMMARY_PATH}")


def main() -> None:
    ensure_dirs()
    set_style()
    data = load_data()
    results = {
        "weekday": plot_weekday_demand(data),
        "hourly": plot_hourly_demand(data),
        "seasonality": plot_item_seasonality(data),
        "ramadan": plot_ramadan_effect(data),
        "customers": plot_customer_archetypes(data),
        "anomalies": plot_anomaly_distribution(data),
        "growth": plot_revenue_growth(data),
    }
    write_summary(results)
    print("\nGenerated files:")
    for path in sorted(FIGURES_DIR.glob("*.png")):
        print(path)
    for path in sorted(METRICS_DIR.glob("*.csv")):
        print(path)
    print(SUMMARY_PATH)


if __name__ == "__main__":
    main()
