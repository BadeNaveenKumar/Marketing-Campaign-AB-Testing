"""
generate_campaign_data.py
--------------------------
Generates a realistic 50,000-row A/B testing dataset for four e-commerce
promotional campaigns and saves it to data/raw/campaign_data.csv.

Also saves a pre-aggregated summary to data/raw/ab_test_results_summary.csv.

Usage:
    python data/generate_campaign_data.py
"""

import os
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
np.random.seed(42)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CAMPAIGN_CONFIG = {
    "Campaign_A": {
        "n": 15000,
        "variant": "Control",
        "ctr": 0.15,
        "cvr": 0.08,
        "revenue_mean": 100.0,
        "marketing_cost": 0.80,
    },
    "Campaign_B": {
        "n": 14000,
        "variant": "Treatment",
        "ctr": 0.22,
        "cvr": 0.095,
        "revenue_mean": 110.0,  # ~10% higher mean than Campaign_A
        "marketing_cost": 1.20,
    },
    "Campaign_C": {
        "n": 12000,
        "variant": "Treatment",
        "ctr": 0.17,
        "cvr": 0.085,
        "revenue_mean": 100.0,
        "marketing_cost": 1.00,
    },
    "Campaign_D": {
        "n": 9000,
        "variant": "Treatment",
        "ctr": 0.14,
        "cvr": 0.075,
        "revenue_mean": 100.0,
        "marketing_cost": 0.75,
    },
}

CHANNELS = ["email", "social_media", "paid_search", "organic"]
CHANNEL_WEIGHTS = [0.35, 0.30, 0.20, 0.15]

AGE_GROUPS = ["18-24", "25-34", "35-44", "45-54", "55+"]
AGE_WEIGHTS = [0.15, 0.30, 0.25, 0.20, 0.10]

DEVICES = ["mobile", "desktop", "tablet"]
DEVICE_WEIGHTS = [0.55, 0.35, 0.10]

# ---------------------------------------------------------------------------
# Dataset generation
# ---------------------------------------------------------------------------

def generate_campaign_rows(campaign_id: str, config: dict, user_id_offset: int) -> pd.DataFrame:
    """Generate rows for a single campaign."""
    n = config["n"]
    ctr = config["ctr"]
    cvr = config["cvr"]
    revenue_mean = config["revenue_mean"]

    user_ids = [f"USER_{i:05d}" for i in range(user_id_offset + 1, user_id_offset + n + 1)]

    channels = np.random.choice(CHANNELS, size=n, p=CHANNEL_WEIGHTS)
    age_groups = np.random.choice(AGE_GROUPS, size=n, p=AGE_WEIGHTS)
    devices = np.random.choice(DEVICES, size=n, p=DEVICE_WEIGHTS)

    # Impression dates: 2024-01-01 to 2024-06-30 (181 days)
    start_date = pd.Timestamp("2024-01-01")
    day_offsets = np.random.randint(0, 181, size=n)
    impression_dates = [start_date + pd.Timedelta(days=int(d)) for d in day_offsets]

    clicked = (np.random.rand(n) < ctr).astype(int)

    # Conversions only possible when clicked (CVR = per-click conversion rate)
    converted = np.zeros(n, dtype=int)
    clicked_mask = clicked == 1
    n_clicked = clicked_mask.sum()
    converted[clicked_mask] = (np.random.rand(n_clicked) < cvr).astype(int)

    # Revenue: $25–$250, centred on revenue_mean (clipped to valid range)
    revenue = np.zeros(n)
    converted_mask = converted == 1
    n_converted = converted_mask.sum()
    if n_converted > 0:
        raw_revenue = np.random.normal(loc=revenue_mean, scale=40, size=n_converted)
        revenue[converted_mask] = np.clip(raw_revenue, 25, 250)

    session_duration = np.random.randint(30, 601, size=n)

    df = pd.DataFrame(
        {
            "user_id": user_ids,
            "campaign_id": campaign_id,
            "variant": config["variant"],
            "channel": channels,
            "age_group": age_groups,
            "device": devices,
            "impression_date": impression_dates,
            "clicked": clicked,
            "converted": converted,
            "revenue": np.round(revenue, 2),
            "marketing_cost": config["marketing_cost"],
            "session_duration_sec": session_duration,
        }
    )
    return df


def generate_full_dataset() -> pd.DataFrame:
    """Combine all campaign dataframes into one 50,000-row dataset."""
    frames = []
    offset = 0
    for campaign_id, config in CAMPAIGN_CONFIG.items():
        frame = generate_campaign_rows(campaign_id, config, offset)
        frames.append(frame)
        offset += config["n"]
    return pd.concat(frames, ignore_index=True)


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Build a pre-aggregated results summary."""
    summary = (
        df.groupby("campaign_id")
        .agg(
            impressions=("user_id", "count"),
            clicks=("clicked", "sum"),
            conversions=("converted", "sum"),
            total_revenue=("revenue", "sum"),
            total_cost=("marketing_cost", "sum"),
        )
        .reset_index()
    )
    summary["CTR"] = (summary["clicks"] / summary["impressions"] * 100).round(2)
    summary["CVR"] = (summary["conversions"] / summary["impressions"] * 100).round(2)
    summary["revenue_per_user"] = (summary["total_revenue"] / summary["impressions"]).round(2)
    summary["ROI_pct"] = (
        (summary["total_revenue"] - summary["total_cost"]) / summary["total_cost"] * 100
    ).round(2)
    return summary


def print_summary(df: pd.DataFrame) -> None:
    """Print key stats to the console."""
    print("=" * 70)
    print("DATASET SUMMARY")
    print("=" * 70)
    print(f"Total rows : {len(df):,}")
    print(f"Date range : {df['impression_date'].min().date()} → {df['impression_date'].max().date()}")
    print()

    for campaign in CAMPAIGN_CONFIG:
        sub = df[df["campaign_id"] == campaign]
        n = len(sub)
        ctr = sub["clicked"].mean() * 100
        cvr = sub["converted"].mean() * 100
        avg_rev_converted = sub.loc[sub["converted"] == 1, "revenue"].mean()
        avg_rev_all = sub["revenue"].mean()
        print(f"  {campaign}")
        print(f"    Users              : {n:,}")
        print(f"    CTR                : {ctr:.2f}%")
        print(f"    CVR (of impressions): {cvr:.2f}%")
        print(f"    Avg revenue (converted): ${avg_rev_converted:.2f}")
        print(f"    Avg revenue (all users): ${avg_rev_all:.2f}")
        print()
    print("=" * 70)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Resolve paths relative to the script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(script_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    print("Generating dataset …")
    df = generate_full_dataset()

    # Save main dataset
    main_path = os.path.join(raw_dir, "campaign_data.csv")
    df.to_csv(main_path, index=False)
    print(f"Saved campaign_data.csv → {main_path}")

    # Save summary
    summary = build_summary(df)
    summary_path = os.path.join(raw_dir, "ab_test_results_summary.csv")
    summary.to_csv(summary_path, index=False)
    print(f"Saved ab_test_results_summary.csv → {summary_path}")

    print_summary(df)
