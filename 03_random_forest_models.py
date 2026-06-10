"""
STEP 3: Random Forest Models — Spend Propensity & Spend Amount
==============================================================
Two models built on the aggregated dataset (109,000 players):

  Model 1 — Classifier
    Question : Will a player spend at all?
    Target   : is_spender (1 if total_spend > 0, else 0)
    Note     : class_weight='balanced' corrects for the ~40% spender rate

  Model 2 — Regressor
    Question : For players who do spend, how much will they spend?
    Target   : total_spend (spenders only, ~65,409 players)

Both models use only behavioral features — spend-derived columns
(transaction_count, recency_days, avg_spend_per_txn, max_single_txn)
are excluded to prevent leakage.

Requirements:
    pip install pandas numpy matplotlib seaborn scikit-learn
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, roc_auc_score, ConfusionMatrixDisplay,
    mean_absolute_error, r2_score, mean_squared_error
)
import warnings
warnings.filterwarnings("ignore")

# =============================================================================
# 1. LOAD & PREP
# =============================================================================

df = pd.read_csv("Aggregated_combined_data.csv")
print(f"Loaded {len(df):,} players")

# Behavioral features only — no spend-derived columns
FEATURES = [
    "cohort_year",
    "seasons_active",
    "avg_rank_score",
    "peak_rank_score",
    "avg_session_mins",
    "avg_sessions_per_week",
    "avg_esports_watch_hrs",
    "is_esports_watcher",
    "avg_agent_diversity",
    "avg_cross_platform_hrs",
    "is_cross_platform",
    "account_age_days",
    "avg_retention",
]

df["is_spender"] = (df["total_spend"] > 0).astype(int)
print(f"Spenders     : {df['is_spender'].sum():,} ({df['is_spender'].mean()*100:.1f}%)")
print(f"Non-spenders : {(df['is_spender']==0).sum():,} ({(df['is_spender']==0).mean()*100:.1f}%)")

X = df[FEATURES]
y_clf = df["is_spender"]

# =============================================================================
# 2. MODEL 1 — CLASSIFIER: Will a player spend?
# =============================================================================
print("\n" + "="*60)
print("MODEL 1 — Spend Propensity Classifier")
print("="*60)

X_train, X_test, y_train, y_test = train_test_split(
    X, y_clf, test_size=0.2, random_state=42, stratify=y_clf
)

clf = RandomForestClassifier(
    n_estimators=300,
    max_depth=12,
    min_samples_leaf=20,
    class_weight="balanced",   # corrects for class imbalance flagged in EDA
    random_state=42,
    n_jobs=-1,
)
clf.fit(X_train, y_train)

y_pred_clf  = clf.predict(X_test)
y_prob_clf  = clf.predict_proba(X_test)[:, 1]
auc         = roc_auc_score(y_test, y_prob_clf)

print(f"\nROC-AUC : {auc:.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred_clf, target_names=["Non-Spender", "Spender"]))

fi_clf = pd.Series(clf.feature_importances_, index=FEATURES).sort_values(ascending=False)
print("\nFeature Importances (descending):")
for feat, imp in fi_clf.items():
    print(f"  {feat:<28} {imp:.4f}")

# =============================================================================
# 3. MODEL 2 — REGRESSOR: How much will a spender spend?
# =============================================================================
print("\n" + "="*60)
print("MODEL 2 — Total Spend Regressor (spenders only)")
print("="*60)

spenders = df[df["is_spender"] == 1].copy()
print(f"Training on {len(spenders):,} spenders")

X_sp = spenders[FEATURES]
y_reg = spenders["total_spend"]

X_tr2, X_te2, y_tr2, y_te2 = train_test_split(
    X_sp, y_reg, test_size=0.2, random_state=42
)

reg = RandomForestRegressor(
    n_estimators=300,
    max_depth=14,
    min_samples_leaf=10,
    random_state=42,
    n_jobs=-1,
)
reg.fit(X_tr2, y_tr2)

y_pred_reg = reg.predict(X_te2)
mae  = mean_absolute_error(y_te2, y_pred_reg)
rmse = np.sqrt(mean_squared_error(y_te2, y_pred_reg))
r2   = r2_score(y_te2, y_pred_reg)

print(f"\nMAE  : ${mae:,.2f}")
print(f"RMSE : ${rmse:,.2f}")
print(f"R²   : {r2:.4f}")

fi_reg = pd.Series(reg.feature_importances_, index=FEATURES).sort_values(ascending=False)
print("\nFeature Importances (descending):")
for feat, imp in fi_reg.items():
    print(f"  {feat:<28} {imp:.4f}")

# =============================================================================
# 4. VISUALIZATIONS
# =============================================================================

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle("Random Forest — Spend Propensity & Spend Amount", fontsize=15, fontweight="bold")

BLUE  = "#2196F3"
GREEN = "#4CAF50"

# --- Plot 1: Model 1 feature importances ---
ax = axes[0, 0]
fi_clf.plot(kind="barh", ax=ax, color=BLUE, edgecolor="white")
ax.invert_yaxis()
ax.set_title("Model 1 — Feature Importance\n(Will a player spend?)", fontweight="bold")
ax.set_xlabel("Mean Decrease in Impurity")
ax.axvline(x=fi_clf.mean(), color="red", linestyle="--", linewidth=1,
           label=f"Mean = {fi_clf.mean():.4f}")
ax.legend(fontsize=8)
for i, (val, name) in enumerate(zip(fi_clf.values, fi_clf.index)):
    ax.text(val + 0.001, i, f"{val:.4f}", va="center", fontsize=8)

# --- Plot 2: Model 1 confusion matrix ---
ax = axes[0, 1]
ConfusionMatrixDisplay.from_predictions(
    y_test, y_pred_clf,
    display_labels=["Non-Spender", "Spender"],
    cmap="Blues", ax=ax, colorbar=False
)
ax.set_title(f"Model 1 — Confusion Matrix\nROC-AUC: {auc:.4f}", fontweight="bold")

# --- Plot 3: Model 2 feature importances ---
ax = axes[1, 0]
fi_reg.plot(kind="barh", ax=ax, color=GREEN, edgecolor="white")
ax.invert_yaxis()
ax.set_title("Model 2 — Feature Importance\n(How much will a spender spend?)", fontweight="bold")
ax.set_xlabel("Mean Decrease in Impurity")
ax.axvline(x=fi_reg.mean(), color="red", linestyle="--", linewidth=1,
           label=f"Mean = {fi_reg.mean():.4f}")
ax.legend(fontsize=8)
for i, (val, name) in enumerate(zip(fi_reg.values, fi_reg.index)):
    ax.text(val + 0.001, i, f"{val:.4f}", va="center", fontsize=8)

# --- Plot 4: Model 2 predicted vs actual ---
ax = axes[1, 1]
ax.scatter(y_te2, y_pred_reg, alpha=0.15, s=10, color=GREEN)
lims = [min(y_te2.min(), y_pred_reg.min()), max(y_te2.max(), y_pred_reg.max())]
ax.plot(lims, lims, "r--", linewidth=1.2, label="Perfect prediction")
ax.set_xlabel("Actual Total Spend ($)")
ax.set_ylabel("Predicted Total Spend ($)")
ax.set_title(f"Model 2 — Predicted vs Actual\nR²={r2:.4f}  MAE=${mae:,.0f}  RMSE=${rmse:,.0f}",
             fontweight="bold")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
ax.legend(fontsize=8)

plt.tight_layout()
plt.savefig("random_forest_results.png", dpi=150, bbox_inches="tight")
plt.show()
print("\nChart saved -> random_forest_results.png")

# =============================================================================
# 5. SUMMARY TABLE
# =============================================================================

print("\n" + "="*60)
print("FEATURE IMPORTANCE COMPARISON")
print("="*60)
summary = pd.DataFrame({
    "Model 1 — Spend Propensity": fi_clf,
    "Model 2 — Spend Amount":     fi_reg,
}).sort_values("Model 1 — Spend Propensity", ascending=False)
print(summary.to_string(float_format="{:.4f}".format))
summary.to_csv("feature_importance_comparison.csv")
print("\nExported feature_importance_comparison.csv")
