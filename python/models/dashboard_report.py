"""
dashboard_report.py
Generates comprehensive KPI reports and visualizations
Exports data summaries ready for Power BI and Excel ingestion
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import os
import warnings
warnings.filterwarnings("ignore")

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({"figure.dpi": 150, "font.size": 10})

PROCESSED_DIR = "../../data/processed"
EXPORTS_DIR = "../../data/exports"
REPORTS_DIR = "../../reports"

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)


def load_all():
    customers = pd.read_csv(f"{PROCESSED_DIR}/customers_cleaned.csv", parse_dates=["join_date"])
    transactions = pd.read_csv(f"{PROCESSED_DIR}/transactions_cleaned.csv",
                               parse_dates=["transaction_date"])
    rfm = pd.read_csv(f"{PROCESSED_DIR}/rfm_scores.csv")
    customer_360 = pd.read_csv(f"{PROCESSED_DIR}/customer_360.csv")
    return customers, transactions, rfm, customer_360


def compute_kpis(customers, transactions):
    kpis = {
        "Total Customers": len(customers),
        "Total Transactions": len(transactions),
        "Total Revenue": round(transactions["revenue"].sum(), 2),
        "Avg Order Value": round(transactions["final_amount"].mean(), 2),
        "Avg Transactions/Customer": round(len(transactions) / len(customers), 1),
        "Return Rate (%)": round(transactions["is_returned"].mean() * 100, 2),
        "Avg Customer Rating": round(transactions["rating"].mean(), 2),
        "Churn Rate (%)": round(customers["is_churned"].mean() * 100, 2),
        "Active Customers": int(customers["is_churned"].eq(0).sum()),
        "Premium Customers": int((customers["segment"] == "Premium").sum())
    }
    kpi_df = pd.DataFrame.from_dict(kpis, orient="index", columns=["Value"])
    kpi_df.index.name = "KPI"
    kpi_df.to_csv(f"{EXPORTS_DIR}/kpi_summary.csv")
    print("KPI Summary:")
    for k, v in kpis.items():
        print(f"  {k:35s}: {v:,.2f}" if isinstance(v, float) else f"  {k:35s}: {v:,}")
    return kpis


def plot_revenue_trend(transactions):
    monthly = transactions.groupby(
        transactions["transaction_date"].dt.to_period("M")
    )["revenue"].sum().reset_index()
    monthly["transaction_date"] = monthly["transaction_date"].astype(str)

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.fill_between(range(len(monthly)), monthly["revenue"], alpha=0.3, color="#2980b9")
    ax.plot(range(len(monthly)), monthly["revenue"], color="#2980b9", lw=2)
    ax.set_xticks(range(0, len(monthly), 3))
    ax.set_xticklabels(monthly["transaction_date"].iloc[::3], rotation=45, ha="right")
    ax.set_title("Monthly Revenue Trend (2022–2024)", fontsize=14, fontweight="bold")
    ax.set_ylabel("Revenue ($)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{REPORTS_DIR}/revenue_trend.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: revenue_trend.png")


def plot_category_performance(transactions):
    cat_perf = transactions.groupby("product_category").agg(
        revenue=("revenue", "sum"),
        transactions=("transaction_id", "count"),
        avg_rating=("rating", "mean"),
        return_rate=("is_returned", "mean")
    ).sort_values("revenue", ascending=False)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Revenue by category
    colors = sns.color_palette("Blues_r", len(cat_perf))
    axes[0].barh(cat_perf.index, cat_perf["revenue"], color=colors)
    axes[0].set_title("Revenue by Product Category", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Total Revenue ($)")
    axes[0].xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x/1e6:.1f}M"))

    # Rating vs Return Rate scatter
    axes[1].scatter(cat_perf["avg_rating"], cat_perf["return_rate"] * 100,
                    s=cat_perf["revenue"] / 10000, alpha=0.7,
                    c=range(len(cat_perf)), cmap="RdYlGn_r")
    for i, cat in enumerate(cat_perf.index):
        axes[1].annotate(cat, (cat_perf.loc[cat, "avg_rating"],
                                cat_perf.loc[cat, "return_rate"] * 100),
                          fontsize=7, ha="center", va="bottom")
    axes[1].set_title("Avg Rating vs Return Rate by Category", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Average Customer Rating")
    axes[1].set_ylabel("Return Rate (%)")

    plt.tight_layout()
    plt.savefig(f"{REPORTS_DIR}/category_performance.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: category_performance.png")


def plot_channel_analysis(transactions):
    channel = transactions.groupby("channel").agg(
        revenue=("revenue", "sum"),
        count=("transaction_id", "count"),
        avg_value=("final_amount", "mean")
    )

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    colors = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12"]

    axes[0].pie(channel["revenue"], labels=channel.index, autopct="%1.1f%%",
                colors=colors, startangle=90)
    axes[0].set_title("Revenue Share by Channel", fontsize=12, fontweight="bold")

    axes[1].bar(channel.index, channel["count"], color=colors)
    axes[1].set_title("Transaction Volume by Channel", fontsize=12, fontweight="bold")
    axes[1].set_ylabel("Transactions")
    axes[1].tick_params(axis="x", rotation=15)

    axes[2].bar(channel.index, channel["avg_value"], color=colors)
    axes[2].set_title("Average Order Value by Channel", fontsize=12, fontweight="bold")
    axes[2].set_ylabel("Avg Value ($)")
    axes[2].tick_params(axis="x", rotation=15)

    plt.tight_layout()
    plt.savefig(f"{REPORTS_DIR}/channel_analysis.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: channel_analysis.png")


def plot_rfm_distribution(rfm):
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    metrics = [("recency", "Recency (days since last purchase)", "#e74c3c"),
               ("frequency", "Frequency (# of transactions)", "#2980b9"),
               ("monetary", "Monetary (total spend $)", "#27ae60")]

    for ax, (col, title, color) in zip(axes, metrics):
        ax.hist(rfm[col], bins=40, color=color, alpha=0.8, edgecolor="white")
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_ylabel("Customer Count")
        ax.axvline(rfm[col].median(), color="black", lw=1.5, linestyle="--", label="Median")
        ax.legend()

    plt.suptitle("RFM Metric Distributions", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(f"{REPORTS_DIR}/rfm_distributions.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: rfm_distributions.png")


def plot_customer_segments(customers):
    seg = customers["segment"].value_counts()
    churn_by_seg = customers.groupby("segment")["is_churned"].mean() * 100

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    colors = sns.color_palette("Set2", len(seg))

    axes[0].pie(seg, labels=seg.index, autopct="%1.1f%%", colors=colors, startangle=90,
                wedgeprops={"edgecolor": "white", "linewidth": 2})
    axes[0].set_title("Customer Segment Distribution", fontsize=12, fontweight="bold")

    bars = axes[1].bar(churn_by_seg.index, churn_by_seg.values, color=colors, edgecolor="white", lw=1.5)
    for bar, val in zip(bars, churn_by_seg.values):
        axes[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                     f"{val:.1f}%", ha="center", fontsize=10, fontweight="bold")
    axes[1].set_title("Churn Rate by Segment", fontsize=12, fontweight="bold")
    axes[1].set_ylabel("Churn Rate (%)")
    axes[1].set_ylim(0, churn_by_seg.max() * 1.2)

    plt.tight_layout()
    plt.savefig(f"{REPORTS_DIR}/customer_segments.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: customer_segments.png")


def export_powerbi_ready(transactions, customers, rfm):
    """Export flat, Power BI-ready datasets."""
    # Daily revenue by category
    daily = transactions.groupby(
        ["transaction_date", "product_category", "channel"]
    ).agg(
        revenue=("revenue", "sum"),
        transactions=("transaction_id", "count"),
        avg_value=("final_amount", "mean")
    ).reset_index()
    daily.to_csv(f"{EXPORTS_DIR}/powerbi_daily_revenue.csv", index=False)

    # Customer full profile
    full = customers.merge(rfm, on="customer_id", how="left")
    full.to_csv(f"{EXPORTS_DIR}/powerbi_customer_profile.csv", index=False)

    print(f"  ✅ Power BI exports saved to {EXPORTS_DIR}/")


def run_dashboard():
    print("=" * 60)
    print("  DASHBOARD REPORT GENERATOR")
    print("=" * 60)

    customers, transactions, rfm, customer_360 = load_all()

    print("\n📊 Computing KPIs...")
    compute_kpis(customers, transactions)

    print("\n📈 Generating visualizations...")
    plot_revenue_trend(transactions)
    plot_category_performance(transactions)
    plot_channel_analysis(transactions)
    plot_rfm_distribution(rfm)
    plot_customer_segments(customers)

    print("\n📤 Exporting Power BI datasets...")
    export_powerbi_ready(transactions, customers, rfm)

    print("\n" + "=" * 60)
    print("  ALL REPORTS GENERATED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    run_dashboard()
