"""
build_viz_dataset.py
====================
Rebuilds Aggregated_combined_data.csv with the following fixes:

  1. recency_days = NULL for non-spenders (was 999)
  2. is_esports_watcher / is_cross_platform stored as "Yes"/"No" (was 0/1)
  3. has_purchased column added ("Yes"/"No")
  4. avg_retention renamed to pct_seasons_retained (clearer meaning)
  5. first_spend_year column added (needed for Q1 viz)
  6. peak_rank stored as label string, e.g. "Diamond" (alongside numeric score)

Run from your project folder:
    python build_viz_dataset.py
"""

import pandas as pd
import numpy as np
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TXN_FILE = os.path.join(SCRIPT_DIR, "synthetic_player_segmentation_data_2025.csv")
BEH_FILE = os.path.join(SCRIPT_DIR, "valorant_player_behavior.csv")
OUT_FILE = os.path.join(SCRIPT_DIR, "Aggregated_combined_data.csv")
REF_DATE = pd.Timestamp("2025-12-31")

# Rank label → numeric score mapping (matches EDA SQL CASE statement)
RANK_SCORE = {
    "Iron": 1, "Bronze": 2, "Silver": 3, "Gold": 4,
    "Platinum": 5, "Diamond": 6, "Ascendant": 7, "Immortal": 8, "Radiant": 9,
}
SCORE_RANK = {v: k for k, v in RANK_SCORE.items()}

# ── Load ───────────────────────────────────────────────────────────────────
print("Loading source files...")
txn = pd.read_csv(TXN_FILE, parse_dates=["transaction_date"])
beh = pd.read_csv(BEH_FILE)
print(f"  Transactions : {len(txn):,} rows | {txn['user_id'].nunique():,} unique users")
print(f"  Behavior     : {len(beh):,} rows | {beh['user_id'].nunique():,} unique users")

# ── Aggregate behavior (one row per user) ──────────────────────────────────
beh["rank_score"] = beh["rank"].map(RANK_SCORE)

beh_agg = beh.groupby("user_id").agg(
    cohort_year           = ("season", "min"),
    seasons_active        = ("season", "nunique"),
    avg_rank_score        = ("rank_score", "mean"),
    peak_rank_score       = ("rank_score", "max"),
    avg_session_mins      = ("avg_session_mins", "mean"),
    avg_sessions_per_week = ("sessions_per_week", "mean"),
    avg_esports_watch_hrs = ("esports_watch_hrs", "mean"),
    is_esports_watcher    = ("is_esports_watcher", "max"),   # ever watched
    avg_agent_diversity   = ("agent_diversity", "mean"),
    avg_cross_platform_hrs= ("cross_platform_hrs", "mean"),
    is_cross_platform     = ("is_cross_platform", "max"),    # ever cross-platform
    account_age_days      = ("account_age_days", "max"),
    pct_seasons_retained  = ("retained_30d", "mean"),
).reset_index()

# Peak rank as readable label
beh_agg["peak_rank"] = beh_agg["peak_rank_score"].map(SCORE_RANK)

# Round numeric columns
beh_agg["avg_rank_score"]         = beh_agg["avg_rank_score"].round(2)
beh_agg["avg_session_mins"]       = beh_agg["avg_session_mins"].round(2)
beh_agg["avg_sessions_per_week"]  = beh_agg["avg_sessions_per_week"].round(2)
beh_agg["avg_esports_watch_hrs"]  = beh_agg["avg_esports_watch_hrs"].round(2)
beh_agg["avg_agent_diversity"]    = beh_agg["avg_agent_diversity"].round(2)
beh_agg["avg_cross_platform_hrs"] = beh_agg["avg_cross_platform_hrs"].round(2)
beh_agg["pct_seasons_retained"]   = beh_agg["pct_seasons_retained"].round(4)

# Fix #2 — booleans as Yes/No strings
beh_agg["is_esports_watcher"] = beh_agg["is_esports_watcher"].map({1: "Yes", 0: "No"})
beh_agg["is_cross_platform"]  = beh_agg["is_cross_platform"].map({1: "Yes", 0: "No"})

# ── Aggregate transactions (one row per user) ──────────────────────────────
txn_agg = txn.groupby("user_id").agg(
    transaction_count  = ("amount", "count"),
    total_spend        = ("amount", "sum"),
    avg_spend_per_txn  = ("amount", "mean"),
    max_single_txn     = ("amount", "max"),
    last_purchase_date = ("transaction_date", "max"),
    first_spend_year   = ("transaction_date", lambda x: x.min().year),  # Fix #5
).reset_index()

txn_agg["recency_days"]      = (REF_DATE - txn_agg["last_purchase_date"]).dt.days
txn_agg["total_spend"]       = txn_agg["total_spend"].round(2)
txn_agg["avg_spend_per_txn"] = txn_agg["avg_spend_per_txn"].round(2)
txn_agg["max_single_txn"]    = txn_agg["max_single_txn"].round(2)
txn_agg = txn_agg.drop(columns=["last_purchase_date"])

# ── Join ───────────────────────────────────────────────────────────────────
df = beh_agg.merge(txn_agg, on="user_id", how="left")

# Non-spenders: zero out spend columns, leave recency + first_spend_year as NULL
df["transaction_count"] = df["transaction_count"].fillna(0).astype(int)
df["total_spend"]       = df["total_spend"].fillna(0.0)
df["avg_spend_per_txn"] = df["avg_spend_per_txn"].fillna(0.0)
df["max_single_txn"]    = df["max_single_txn"].fillna(0.0)
# recency_days and first_spend_year intentionally left NULL for non-spenders (Fix #1)

# Fix #3 — has_purchased flag
df["has_purchased"] = (df["transaction_count"] > 0).map({True: "Yes", False: "No"})

# ── Column order ───────────────────────────────────────────────────────────
df = df[[
    "user_id", "cohort_year", "seasons_active",
    "avg_rank_score", "peak_rank_score", "peak_rank",
    "avg_session_mins", "avg_sessions_per_week",
    "avg_esports_watch_hrs", "is_esports_watcher",
    "avg_agent_diversity", "avg_cross_platform_hrs", "is_cross_platform",
    "account_age_days", "pct_seasons_retained",
    "has_purchased", "first_spend_year",
    "transaction_count", "total_spend", "avg_spend_per_txn", "max_single_txn",
    "recency_days",
]]

# ── Save ───────────────────────────────────────────────────────────────────
df.to_csv(OUT_FILE, index=False)
print(f"\n✓ Saved {len(df):,} rows → {OUT_FILE}")

# ── Validation ─────────────────────────────────────────────────────────────
print("\n=== VALIDATION ===")
print(f"Total users         : {len(df):,}")
print(f"Spenders            : {(df['has_purchased'] == 'Yes').sum():,}")
print(f"Non-spenders        : {(df['has_purchased'] == 'No').sum():,}")
print(f"recency_days NULLs  : {df['recency_days'].isna().sum():,}  ← should equal non-spenders")
print(f"first_spend_year NULLs: {df['first_spend_year'].isna().sum():,}  ← should equal non-spenders")
print(f"\nis_esports_watcher values : {df['is_esports_watcher'].value_counts().to_dict()}")
print(f"is_cross_platform values  : {df['is_cross_platform'].value_counts().to_dict()}")
print(f"peak_rank sample          : {df['peak_rank'].value_counts().head(4).to_dict()}")
print(f"\nColumns:\n{list(df.columns)}")
