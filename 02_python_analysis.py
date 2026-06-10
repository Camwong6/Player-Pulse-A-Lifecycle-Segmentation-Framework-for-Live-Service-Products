"""
STEP 2: Python — RFM Segmentation & Enriched Player Analysis
=============================================================
Builds directly on the SQL exploration from Step 1.

Step 1 (SQL) showed us:
  - Which ranks retain best
  - Monthly revenue trends
  - Who the top spenders are

Step 2 (Python) formalizes this into:
  - RFM (Recency, Frequency, Monetary) scores for every player
  - Named player segments (Champions, Loyal, At Risk, etc.)
  - A merged dataset combining behavior + RFM

OUTPUT → player_segments.csv  (used by Step 3 Excel and Step 4 Tableau)

Requirements:
    pip install pandas numpy matplotlib seaborn
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

# =============================================================================
# 1. LOAD DATA
# =============================================================================

behavior_df = pd.read_csv("valorant_player_behavior.csv")
transactions_df = pd.read_csv("synthetic_player_segmentation_data_2025.csv",
                              parse_dates=["transaction_date"])

print("=== DATA LOADED ===")
print(f"Players:      {len(behavior_df):,}")
print(f"Transactions: {len(transactions_df):,}")
print(f"Date range:   {transactions_df['transaction_date'].min().date()} → "
      f"{transactions_df['transaction_date'].max().date()}")
print()

# =============================================================================
# 2. RFM CALCULATION
# =============================================================================
# Recency  = days since last purchase (lower = better)
# Frequency = number of transactions
# Monetary  = total amount spent

# Use the day after the last transaction as "today" (snapshot date)
snapshot_date = transactions_df["transaction_date"].max() + timedelta(days=1)
print(f"RFM snapshot date: {snapshot_date.date()}")

rfm = transactions_df.groupby("user_id").agg(
    last_purchase   = ("transaction_date", "max"),
    frequency       = ("transaction_date", "count"),
    monetary        = ("amount", "sum")
).reset_index()

rfm["recency"] = (snapshot_date - rfm["last_purchase"]).dt.days
rfm["monetary"] = rfm["monetary"].round(2)

print("\n=== RFM SUMMARY ===")
print(rfm[["recency", "frequency", "monetary"]].describe().round(2))

# =============================================================================
# 3. SCORE EACH RFM DIMENSION (1–5 scale, 5 = best)
# =============================================================================
# Recency:  5 = very recent (low recency days), 1 = churned long ago
# Frequency: 5 = buys often
# Monetary:  5 = highest spender

def rfm_score(series, ascending=True):
    """Assign 1–5 score using quintiles."""
    labels = [1, 2, 3, 4, 5] if ascending else [5, 4, 3, 2, 1]
    return pd.qcut(series, q=5, labels=labels, duplicates="drop").astype(int)

rfm["R"] = rfm_score(rfm["recency"],   ascending=False)  # low recency = recent = high score
rfm["F"] = rfm_score(rfm["frequency"], ascending=True)
rfm["M"] = rfm_score(rfm["monetary"],  ascending=True)

rfm["RFM_score"] = rfm["R"].astype(str) + rfm["F"].astype(str) + rfm["M"].astype(str)
rfm["RFM_total"] = rfm["R"] + rfm["F"] + rfm["M"]

# =============================================================================
# 4. SEGMENT ASSIGNMENT
# =============================================================================
# Rules map RFM scores to business-meaningful player tiers.

def assign_segment(row):
    r, f, m = row["R"], row["F"], row["M"]
    if r >= 4 and f >= 4 and m >= 4:
        return "Champion"
    elif r >= 3 and f >= 3 and m >= 3:
        return "Loyal Player"
    elif r >= 4 and f <= 2:
        return "New Player"
    elif r <= 2 and f >= 3 and m >= 3:
        return "At Risk"
    elif r <= 2 and f >= 2:
        return "Lapsing"
    elif r >= 3 and m >= 4:
        return "High Spender"
    elif r <= 1:
        return "Churned"
    else:
        return "Casual"

rfm["segment"] = rfm.apply(assign_segment, axis=1)

segment_summary = rfm.groupby("segment").agg(
    players         = ("user_id", "count"),
    avg_recency     = ("recency", "mean"),
    avg_frequency   = ("frequency", "mean"),
    avg_monetary    = ("monetary", "mean"),
    total_revenue   = ("monetary", "sum")
).round(2).sort_values("total_revenue", ascending=False)

print("\n=== SEGMENT BREAKDOWN ===")
print(segment_summary.to_string())

# =============================================================================
# 5. MERGE WITH BEHAVIOR DATA
# =============================================================================

merged = behavior_df.merge(rfm, on="user_id", how="left")

# Players with no transactions get segment = "Non-Spender"
merged["segment"] = merged["segment"].fillna("Non-Spender")
merged["monetary"] = merged["monetary"].fillna(0)
merged["frequency"] = merged["frequency"].fillna(0)
merged["recency"] = merged["recency"].fillna(999)

# Rank ordering for plots
rank_order = ["Iron", "Bronze", "Silver", "Gold", "Platinum",
              "Diamond", "Ascendant", "Immortal", "Radiant"]

print(f"\n=== MERGED DATASET: {len(merged):,} players ===")
print(merged[["user_id", "rank", "segment", "monetary", "retained_30d"]].head(10).to_string(index=False))

# =============================================================================
# 6. ANALYSIS — Key Insights
# =============================================================================

print("\n=== RETENTION RATE BY SEGMENT ===")
retention_by_segment = merged.groupby("segment").agg(
    players         = ("user_id", "count"),
    retention_rate  = ("retained_30d", "mean"),
    avg_spend       = ("monetary", "mean")
).round(3)
retention_by_segment["retention_pct"] = (retention_by_segment["retention_rate"] * 100).round(1)
print(retention_by_segment[["players", "retention_pct", "avg_spend"]].sort_values("retention_pct", ascending=False).to_string())

print("\n=== AVG SPEND BY RANK ===")
spend_by_rank = merged[merged["monetary"] > 0].groupby("rank").agg(
    players     = ("user_id", "count"),
    avg_spend   = ("monetary", "mean"),
    median_spend= ("monetary", "median")
).round(2)
spend_by_rank = spend_by_rank.reindex([r for r in rank_order if r in spend_by_rank.index])
print(spend_by_rank.to_string())

# =============================================================================
# 7. VISUALIZATIONS
# =============================================================================

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("Valorant Player KPI Analysis", fontsize=16, fontweight="bold", y=1.01)

palette = {
    "Champion":     "#FFD700",
    "Loyal Player": "#4CAF50",
    "High Spender": "#2196F3",
    "New Player":   "#9C27B0",
    "At Risk":      "#FF5722",
    "Lapsing":      "#FF9800",
    "Churned":      "#9E9E9E",
    "Casual":       "#78909C",
    "Non-Spender":  "#B0BEC5",
}

# Plot 1: Player count by segment
ax1 = axes[0, 0]
seg_counts = merged["segment"].value_counts()
colors = [palette.get(s, "#90A4AE") for s in seg_counts.index]
bars = ax1.bar(seg_counts.index, seg_counts.values, color=colors, edgecolor="white")
ax1.set_title("Players by Segment", fontweight="bold")
ax1.set_xlabel("Segment")
ax1.set_ylabel("Player Count")
ax1.tick_params(axis="x", rotation=35)
for bar, count in zip(bars, seg_counts.values):
    ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
             str(count), ha="center", va="bottom", fontsize=8)

# Plot 2: Revenue by segment
ax2 = axes[0, 1]
rev_by_seg = merged.groupby("segment")["monetary"].sum().sort_values(ascending=False)
colors2 = [palette.get(s, "#90A4AE") for s in rev_by_seg.index]
ax2.bar(rev_by_seg.index, rev_by_seg.values, color=colors2, edgecolor="white")
ax2.set_title("Total Revenue by Segment", fontweight="bold")
ax2.set_xlabel("Segment")
ax2.set_ylabel("Total Revenue ($)")
ax2.tick_params(axis="x", rotation=35)
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))

# Plot 3: Retention rate by rank
ax3 = axes[1, 0]
ret_by_rank = merged.groupby("rank")["retained_30d"].mean().reindex(
    [r for r in rank_order if r in merged["rank"].unique()])
ax3.bar(ret_by_rank.index, ret_by_rank.values * 100,
        color="#5C6BC0", edgecolor="white")
ax3.set_title("30-Day Retention Rate by Rank", fontweight="bold")
ax3.set_xlabel("Rank")
ax3.set_ylabel("Retention Rate (%)")
ax3.set_ylim(0, 110)
ax3.tick_params(axis="x", rotation=30)
ax3.axhline(y=merged["retained_30d"].mean() * 100, color="red",
            linestyle="--", linewidth=1.2, label=f'Overall avg: {merged["retained_30d"].mean()*100:.1f}%')
ax3.legend(fontsize=8)

# Plot 4: RFM scatter — Frequency vs Monetary colored by segment
ax4 = axes[1, 1]
spenders = merged[merged["monetary"] > 0].copy()
for seg, color in palette.items():
    subset = spenders[spenders["segment"] == seg]
    if len(subset) > 0:
        ax4.scatter(subset["frequency"], subset["monetary"],
                    alpha=0.6, s=20, label=seg, color=color)
ax4.set_title("Frequency vs. Total Spend (by Segment)", fontweight="bold")
ax4.set_xlabel("Transaction Count (Frequency)")
ax4.set_ylabel("Total Spend ($) (Monetary)")
ax4.legend(loc="upper left", fontsize=7, markerscale=1.5)

plt.tight_layout()
plt.savefig("player_kpi_analysis.png", dpi=150, bbox_inches="tight")
plt.show()
print("\nChart saved → player_kpi_analysis.png")

# =============================================================================
# 8. EXPORT player_segments.csv  (used by Step 3 Excel & Step 4 Tableau)
# =============================================================================

export_cols = [
    "user_id", "rank", "account_age_days", "avg_session_mins",
    "sessions_per_week", "esports_watch_hrs", "is_esports_watcher",
    "primary_agent", "primary_role", "agent_diversity",
    "cross_platform_hrs", "is_cross_platform", "primary_other_platform",
    "retained_30d", "recency", "frequency", "monetary",
    "R", "F", "M", "RFM_total", "segment"
]

# Only include columns that exist (R/F/M may be NaN for non-spenders)
export_cols = [c for c in export_cols if c in merged.columns]
merged[export_cols].to_csv("player_segments.csv", index=False)

print(f"\nExported player_segments.csv — {len(merged):,} rows, {len(export_cols)} columns")
print("Columns:", ", ".join(export_cols))
print("\n>>> NEXT STEP: Open 03_excel_report.py to generate the Excel KPI workbook.")
