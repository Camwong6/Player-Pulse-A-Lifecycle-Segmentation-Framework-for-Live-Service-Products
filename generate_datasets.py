"""
generate_datasets.py
====================
Regenerates both synthetic datasets with matching user_ids.

Run from your project folder:
    python generate_datasets.py

Outputs:
    - synthetic_player_segmentation_data_2025.csv  (~500,500 rows, 5 years)
    - valorant_player_behavior.csv                 (109,000 rows, 1 per user)
"""

import pandas as pd
import numpy as np
from datetime import date, timedelta
import random
import os

# Always save next to this script regardless of where Python is run from
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

SEED = 67
np.random.seed(SEED)
random.seed(SEED)

TOTAL_USERS = 109_000
USER_IDS = [f"U{str(i).zfill(5)}" for i in range(1, TOTAL_USERS + 1)]

# ─────────────────────────────────────────────────────────────────────────────
# TIER ASSIGNMENTS  (same users referenced by both datasets)
# ─────────────────────────────────────────────────────────────────────────────
tier_choices = np.random.choice(
    ["non_spender", "casual", "mid_tier", "whale"],
    size=TOTAL_USERS,
    p=[0.40, 0.35, 0.20, 0.05]
)
tier_map = dict(zip(USER_IDS, tier_choices))


# =============================================================================
# DATASET 1 — TRANSACTIONS
# =============================================================================
print("Generating transaction dataset...")

YEARS = [2021, 2022, 2023, 2024, 2025]

# Cohort year: the year a spending user first appears
cohort_map = {}
for uid in USER_IDS:
    if tier_map[uid] != "non_spender":
        cohort_map[uid] = np.random.choice(YEARS[:-1])  # cohorts 2021–2024

# Churn: users stop transacting after a random number of active years
# Probabilities skewed toward longer survival so 2025 revenue keeps growing
churn_years_map = {}
for uid in USER_IDS:
    if tier_map[uid] == "casual":
        churn_years_map[uid] = np.random.choice([1, 2, 3, 4, 5], p=[0.15, 0.20, 0.25, 0.20, 0.20])
    elif tier_map[uid] == "mid_tier":
        churn_years_map[uid] = np.random.choice([1, 2, 3, 4, 5], p=[0.05, 0.10, 0.20, 0.30, 0.35])
    elif tier_map[uid] == "whale":
        churn_years_map[uid] = np.random.choice([2, 3, 4, 5],     p=[0.05, 0.10, 0.15, 0.70])

# YoY growth multiplier (~10% more revenue each year)
yoy_growth = {2021: 1.00, 2022: 1.10, 2023: 1.21, 2024: 1.33, 2025: 1.46}

# Seasonal weight per month (Sep–Dec ~35% heavier)
monthly_weights = [1, 1, 1, 1, 1, 1, 1, 1, 1.35, 1.35, 1.35, 1.35]
monthly_weights = np.array(monthly_weights)
monthly_weights = monthly_weights / monthly_weights.sum()

def random_date_in_year(year):
    month = np.random.choice(range(1, 13), p=monthly_weights)
    max_day = [31,28,31,30,31,30,31,31,30,31,30,31][month - 1]
    day = np.random.randint(1, max_day + 1)
    return date(year, month, day)

tier_txn_config = {
    "casual":   {"txns_per_year": (1, 2),  "amount": (0.99,  9.99)},
    "mid_tier": {"txns_per_year": (2, 4),  "amount": (4.99,  49.99)},
    "whale":    {"txns_per_year": (6, 15), "amount": (19.99, 199.99)},
}

rows = []
for uid in USER_IDS:
    tier = tier_map[uid]
    if tier == "non_spender":
        continue

    cohort = cohort_map[uid]
    active_years = churn_years_map[uid]
    cfg = tier_txn_config[tier]

    for i, year in enumerate(YEARS):
        if year < cohort:
            continue
        if i - (cohort - 2021) >= active_years:
            continue

        n_txns = np.random.randint(cfg["txns_per_year"][0], cfg["txns_per_year"][1] + 1)
        growth = yoy_growth[year]

        for _ in range(n_txns):
            base_amount = np.random.uniform(*cfg["amount"])
            amount = round(base_amount * growth, 2)
            txn_date = random_date_in_year(year)
            rows.append((uid, txn_date, amount))

txn_df = pd.DataFrame(rows, columns=["user_id", "transaction_date", "amount"])
txn_df = txn_df.sort_values(["user_id", "transaction_date"]).reset_index(drop=True)

txn_df.to_csv(os.path.join(SCRIPT_DIR, "synthetic_player_segmentation_data_2025.csv"), index=False)

# Validation summary
print("\n=== TRANSACTION DATASET VALIDATION ===")
print(f"Total rows:         {len(txn_df):,}")
print(f"Unique users:       {txn_df['user_id'].nunique():,}")

user_spend = txn_df.groupby("user_id")["amount"].sum()
print(f"Mean spend/user:    ${user_spend.mean():,.2f}")
print(f"Median spend/user:  ${user_spend.median():,.2f}")

whale_users = [u for u, t in tier_map.items() if t == "whale"]
whale_rev = txn_df[txn_df["user_id"].isin(whale_users)]["amount"].sum()
total_rev = txn_df["amount"].sum()
print(f"Total revenue:      ${total_rev:,.2f}")
print(f"Whale revenue share:{whale_rev / total_rev * 100:.1f}%")

print("\nRevenue by year:")
txn_df["year"] = pd.to_datetime(txn_df["transaction_date"]).dt.year
print(txn_df.groupby("year")["amount"].sum().apply(lambda x: f"${x:,.2f}").to_string())

tier_labels = txn_df["user_id"].map(tier_map)
print("\nRows by tier:")
print(txn_df.groupby(tier_labels).size().to_string())


# =============================================================================
# DATASET 2 — VALORANT PLAYER BEHAVIOR  (one row per user per active season)
# =============================================================================
print("\n\nGenerating valorant player behavior dataset...")

agents = {
    "Duelist":    ["Reyna", "Jett", "Raze", "Phoenix", "Yoru", "Neon", "Iso"],
    "Controller": ["Brimstone", "Omen", "Viper", "Astra", "Harbor", "Clove"],
    "Initiator":  ["Sova", "Breach", "Skye", "KAY/O", "Fade", "Gekko"],
    "Sentinel":   ["Sage", "Cypher", "Killjoy", "Chamber", "Deadlock", "Vyse"],
}
all_agents = [(agent, role) for role, ags in agents.items() for agent in ags]
agent_names = [a[0] for a in all_agents]
agent_roles = [a[1] for a in all_agents]

ranks = ["Iron", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Ascendant", "Immortal", "Radiant"]

other_platforms = ["None", "Wild Rift", "Legends of Runeterra", "TFT", "League of Legends", "None", "None"]

# All 109k users get a cohort year (including non-spenders — they play, just don't buy)
player_cohort = {}
player_active_seasons = {}
for uid in USER_IDS:
    tier = tier_map[uid]
    player_cohort[uid] = np.random.choice(YEARS[:-1])  # joined 2021–2024
    if tier == "non_spender":
        player_active_seasons[uid] = np.random.choice([1, 2, 3, 4, 5], p=[0.30, 0.25, 0.20, 0.15, 0.10])
    elif tier == "casual":
        player_active_seasons[uid] = np.random.choice([1, 2, 3, 4, 5], p=[0.15, 0.20, 0.25, 0.20, 0.20])
    elif tier == "mid_tier":
        player_active_seasons[uid] = np.random.choice([1, 2, 3, 4, 5], p=[0.05, 0.10, 0.20, 0.30, 0.35])
    else:  # whale
        player_active_seasons[uid] = np.random.choice([2, 3, 4, 5],    p=[0.05, 0.10, 0.15, 0.70])

# Starting rank per player — assigned once, then allowed to progress year over year
def starting_rank(tier):
    if tier == "whale":
        return np.random.choice(ranks, p=[0.02, 0.05, 0.10, 0.15, 0.20, 0.22, 0.13, 0.10, 0.03])
    elif tier == "mid_tier":
        return np.random.choice(ranks, p=[0.05, 0.10, 0.18, 0.22, 0.20, 0.13, 0.07, 0.04, 0.01])
    else:
        return np.random.choice(ranks, p=[0.10, 0.15, 0.20, 0.20, 0.15, 0.10, 0.05, 0.04, 0.01])

player_start_rank = {uid: starting_rank(tier_map[uid]) for uid in USER_IDS}
player_start_agent = {uid: np.random.randint(0, len(agent_names)) for uid in USER_IDS}

behavior_rows = []
for uid in USER_IDS:
    tier      = tier_map[uid]
    cohort    = player_cohort[uid]
    seasons   = player_active_seasons[uid]
    rank_idx  = ranks.index(player_start_rank[uid])
    agent_idx = player_start_agent[uid]

    for i, year in enumerate(YEARS):
        if year < cohort:
            continue
        years_active = year - cohort
        if years_active >= seasons:
            continue

        # Rank can improve by 1 tier per year with 30% chance (capped at Radiant)
        if years_active > 0 and np.random.random() < 0.30:
            rank_idx = min(rank_idx + 1, len(ranks) - 1)

        # Agent can shift ~15% chance per year
        if years_active > 0 and np.random.random() < 0.15:
            agent_idx = np.random.randint(0, len(agent_names))

        rank = ranks[rank_idx]
        account_age_days = int(years_active * 365 + np.random.randint(1, 365))

        avg_session_mins  = round(float(np.clip(np.random.normal(30 + rank_idx * 4, 10), 10, 120)), 1)
        sessions_per_week = round(float(np.clip(np.random.normal(4 + rank_idx * 0.4, 2), 1, 20)), 1)

        esports_watch_hrs  = round(float(np.clip(np.random.exponential(5), 0, 60)), 2)
        is_esports_watcher = 1 if esports_watch_hrs > 1 else 0

        primary_agent = agent_names[agent_idx]
        primary_role  = agent_roles[agent_idx]
        agent_diversity = int(np.clip(np.random.randint(1, 8) + years_active, 1, 14))

        is_cross_platform      = int(np.random.random() < 0.35)
        cross_platform_hrs     = round(float(np.clip(np.random.exponential(8), 0, 60)), 2) if is_cross_platform else 0.0
        primary_other_platform = np.random.choice(other_platforms) if is_cross_platform else "None"

        base_retention = 0.60
        if tier == "whale":      base_retention = 0.92
        elif tier == "mid_tier": base_retention = 0.82
        elif tier == "casual":   base_retention = 0.74
        retained_30d = int(np.random.random() < base_retention)

        behavior_rows.append([
            uid, year, rank, account_age_days, avg_session_mins, sessions_per_week,
            esports_watch_hrs, is_esports_watcher, primary_agent, primary_role,
            agent_diversity, cross_platform_hrs, is_cross_platform,
            primary_other_platform, retained_30d
        ])

behavior_df = pd.DataFrame(behavior_rows, columns=[
    "user_id", "season", "rank", "account_age_days", "avg_session_mins",
    "sessions_per_week", "esports_watch_hrs", "is_esports_watcher", "primary_agent",
    "primary_role", "agent_diversity", "cross_platform_hrs", "is_cross_platform",
    "primary_other_platform", "retained_30d"
])

behavior_df = behavior_df.sort_values(["user_id", "season"]).reset_index(drop=True)
behavior_df.to_csv(os.path.join(SCRIPT_DIR, "valorant_player_behavior.csv"), index=False)

print("\n=== VALORANT BEHAVIOR DATASET VALIDATION ===")
print(f"Total rows:      {len(behavior_df):,}")
print(f"Unique users:    {behavior_df['user_id'].nunique():,}")
print(f"Years covered:   {behavior_df['season'].min()}–{behavior_df['season'].max()}")
print(f"\nRetention rate:  {behavior_df['retained_30d'].mean()*100:.1f}%")
print(f"Cross-platform:  {behavior_df['is_cross_platform'].mean()*100:.1f}%")
print("\nRows per season:")
print(behavior_df["season"].value_counts().sort_index().to_string())
print("\nRank distribution:")
print(behavior_df["rank"].value_counts().reindex(ranks).to_string())
print("\nRole distribution:")
print(behavior_df["primary_role"].value_counts().to_string())

print("\n✓ Both files saved to:", SCRIPT_DIR)
print("  → synthetic_player_segmentation_data_2025.csv")
print("  → valorant_player_behavior.csv")
