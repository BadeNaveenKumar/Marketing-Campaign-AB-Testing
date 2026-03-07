"""
01_eda.py
----------
Exploratory Data Analysis for the A/B Testing Campaign dataset.

Generates 6 charts saved to the outputs/ folder and prints summary statistics.

Usage (from repo root):
    python ab_testing_campaign/analysis/01_eda.py
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for saving files
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_PATH = os.path.join(PROJECT_DIR, "data", "raw", "campaign_data.csv")
OUTPUTS_DIR = os.path.join(PROJECT_DIR, "outputs")
os.makedirs(OUTPUTS_DIR, exist_ok=True)

plt.style.use("dark_background")
DPI = 150

CAMPAIGN_ORDER = ["Campaign_A", "Campaign_B", "Campaign_C", "Campaign_D"]
PALETTE = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]  # distinct colours
WINNER_COLOR = "#DD8452"  # highlight Campaign_B


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_data() -> pd.DataFrame:
    """Load the campaign dataset; generate it if not present."""
    if not os.path.exists(DATA_PATH):
        print(f"Data file not found at {DATA_PATH}.")
        print("Run  python data/generate_campaign_data.py  first.")
        sys.exit(1)
    df = pd.read_csv(DATA_PATH, parse_dates=["impression_date"])
    return df


# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------

def print_summary(df: pd.DataFrame) -> None:
    """Print key metrics per campaign to console."""
    print("\n" + "=" * 70)
    print("EDA SUMMARY STATISTICS")
    print("=" * 70)

    grp = df.groupby("campaign_id")
    for campaign in CAMPAIGN_ORDER:
        sub = grp.get_group(campaign)
        n = len(sub)
        ctr = sub["clicked"].mean() * 100
        cvr = sub["converted"].mean() * 100
        avg_rev_converted = sub.loc[sub["converted"] == 1, "revenue"].mean()
        avg_rev_all = sub["revenue"].mean()
        print(f"\n  {campaign}  (n={n:,})")
        print(f"    CTR                      : {ctr:.2f}%")
        print(f"    Conversion rate          : {cvr:.2f}%")
        print(f"    Avg revenue (converted)  : ${avg_rev_converted:.2f}")
        print(f"    Avg revenue (all users)  : ${avg_rev_all:.2f}")
    print("\n" + "=" * 70 + "\n")


# ---------------------------------------------------------------------------
# Chart helpers
# ---------------------------------------------------------------------------

def save_fig(filename: str) -> None:
    path = os.path.join(OUTPUTS_DIR, filename)
    plt.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close()
    print(f"Saved: {path}")


# ---------------------------------------------------------------------------
# Chart 1 — Campaign size distribution
# ---------------------------------------------------------------------------

def chart_campaign_size(df: pd.DataFrame) -> None:
    counts = df.groupby("campaign_id").size().reindex(CAMPAIGN_ORDER)
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(CAMPAIGN_ORDER, counts.values, color=PALETTE, edgecolor="white", linewidth=0.5)
    for bar, val in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 100,
                f"{val:,}", ha="center", va="bottom", fontsize=10)
    ax.set_title("Users per Campaign", fontsize=14, pad=12)
    ax.set_xlabel("Campaign")
    ax.set_ylabel("Number of Users")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{int(x):,}"))
    plt.tight_layout()
    save_fig("01_campaign_size_distribution.png")


# ---------------------------------------------------------------------------
# Chart 2 — CTR by campaign with error bars
# ---------------------------------------------------------------------------

def chart_ctr(df: pd.DataFrame) -> None:
    stats = []
    for campaign in CAMPAIGN_ORDER:
        sub = df[df["campaign_id"] == campaign]["clicked"]
        n = len(sub)
        p = sub.mean()
        se = np.sqrt(p * (1 - p) / n)
        stats.append({"campaign": campaign, "ctr": p * 100, "se": se * 100})
    stats_df = pd.DataFrame(stats)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(stats_df["campaign"], stats_df["ctr"], color=PALETTE, edgecolor="white",
           linewidth=0.5, yerr=stats_df["se"] * 1.96, capsize=5, error_kw={"ecolor": "white"})
    ax.set_title("Click-Through Rate (CTR) by Campaign with 95% CI", fontsize=14, pad=12)
    ax.set_xlabel("Campaign")
    ax.set_ylabel("CTR (%)")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    plt.tight_layout()
    save_fig("02_ctr_by_campaign.png")


# ---------------------------------------------------------------------------
# Chart 3 — Conversion rate by campaign (Campaign_B highlighted)
# ---------------------------------------------------------------------------

def chart_cvr(df: pd.DataFrame) -> None:
    cvrs = df.groupby("campaign_id")["converted"].mean().reindex(CAMPAIGN_ORDER) * 100
    colors = [WINNER_COLOR if c == "Campaign_B" else PALETTE[0] for c in CAMPAIGN_ORDER]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(CAMPAIGN_ORDER, cvrs.values, color=colors, edgecolor="white", linewidth=0.5)
    for bar, val in zip(bars, cvrs.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                f"{val:.2f}%", ha="center", va="bottom", fontsize=10)
    ax.set_title("Conversion Rate by Campaign (Campaign_B highlighted as winner)", fontsize=13, pad=12)
    ax.set_xlabel("Campaign")
    ax.set_ylabel("Conversion Rate (%)")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    plt.tight_layout()
    save_fig("03_conversion_rate_by_campaign.png")


# ---------------------------------------------------------------------------
# Chart 4 — Revenue distribution (box plot)
# ---------------------------------------------------------------------------

def chart_revenue_dist(df: pd.DataFrame) -> None:
    converted = df[df["converted"] == 1].copy()
    fig, ax = plt.subplots(figsize=(9, 5))
    data = [converted.loc[converted["campaign_id"] == c, "revenue"].values for c in CAMPAIGN_ORDER]
    bp = ax.boxplot(data, patch_artist=True, notch=False,
                    boxprops=dict(linewidth=1.2),
                    medianprops=dict(color="yellow", linewidth=2),
                    whiskerprops=dict(linewidth=1),
                    capprops=dict(linewidth=1),
                    flierprops=dict(marker="o", markersize=2, alpha=0.3))
    for patch, color in zip(bp["boxes"], PALETTE):
        patch.set_facecolor(color)
        patch.set_alpha(0.8)
    ax.set_xticklabels(CAMPAIGN_ORDER)
    ax.set_title("Revenue Distribution per Converted User by Campaign", fontsize=13, pad=12)
    ax.set_xlabel("Campaign")
    ax.set_ylabel("Revenue ($)")
    plt.tight_layout()
    save_fig("04_revenue_distribution.png")


# ---------------------------------------------------------------------------
# Chart 5 — Channel breakdown (stacked bar)
# ---------------------------------------------------------------------------

def chart_channel_breakdown(df: pd.DataFrame) -> None:
    channels = ["email", "social_media", "paid_search", "organic"]
    ct = (
        df.groupby(["campaign_id", "channel"])["user_id"]
        .count()
        .unstack("channel")
        .reindex(CAMPAIGN_ORDER)[channels]
    )
    ct_pct = ct.div(ct.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(9, 5))
    channel_colors = ["#5B9BD5", "#ED7D31", "#70AD47", "#FFC000"]
    bottom = np.zeros(len(CAMPAIGN_ORDER))
    for i, ch in enumerate(channels):
        ax.bar(CAMPAIGN_ORDER, ct_pct[ch].values, bottom=bottom,
               color=channel_colors[i], label=ch, edgecolor="white", linewidth=0.3)
        bottom += ct_pct[ch].values
    ax.set_title("Channel Distribution Across Campaigns", fontsize=13, pad=12)
    ax.set_xlabel("Campaign")
    ax.set_ylabel("Share of Users (%)")
    ax.legend(title="Channel", bbox_to_anchor=(1.01, 1), loc="upper left")
    plt.tight_layout()
    save_fig("05_channel_breakdown.png")


# ---------------------------------------------------------------------------
# Chart 6 — Device vs conversion rate (grouped bar)
# ---------------------------------------------------------------------------

def chart_device_conversion(df: pd.DataFrame) -> None:
    devices = ["mobile", "desktop", "tablet"]
    device_colors = ["#5B9BD5", "#ED7D31", "#70AD47"]
    x = np.arange(len(CAMPAIGN_ORDER))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, device in enumerate(devices):
        rates = [
            df.loc[(df["campaign_id"] == c) & (df["device"] == device), "converted"].mean() * 100
            for c in CAMPAIGN_ORDER
        ]
        ax.bar(x + i * width, rates, width, label=device, color=device_colors[i],
               edgecolor="white", linewidth=0.4)
    ax.set_xticks(x + width)
    ax.set_xticklabels(CAMPAIGN_ORDER)
    ax.set_title("Conversion Rate by Device Across Campaigns", fontsize=13, pad=12)
    ax.set_xlabel("Campaign")
    ax.set_ylabel("Conversion Rate (%)")
    ax.legend(title="Device")
    plt.tight_layout()
    save_fig("06_device_vs_conversion.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    df = load_data()
    print_summary(df)
    chart_campaign_size(df)
    chart_ctr(df)
    chart_cvr(df)
    chart_revenue_dist(df)
    chart_channel_breakdown(df)
    chart_device_conversion(df)
    print("\nAll charts saved to outputs/")
