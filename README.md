# Player Pulse: A Lifecycle Segmentation Framework for Live-Service Products

A portfolio project simulating a real-world player analytics pipeline for a free-to-play FPS (modeled after Valorant). The project spans data generation, exploratory analysis, SQL-driven segmentation, and Random Forest modeling — all built around the question: **what behavioral signals predict monetization in a live-service game?**

---

## Dataset

Synthetic data covering 100,000 players across 2025, generating over 35 million in revenue from more than 500,000 transactions. Designed to reflect realistic spending distribution patterns in free-to-play titles, where most players never spend and a small group drives most revenue.

---

## Exploratory Data Analysis

A correlation heatmap was run across all features to surface initial relationships.

**Key positive correlations:**
- Transaction variables correlated with retention and account age — players who spend have more investment in the game and stay longer
- Agent diversity correlated with seasons active — players who experiment with more agents show stronger long-term engagement
- Esports watcher status correlated with seasons active, sessions per week, and account age
- Cross-platform play correlated with seasons active and account age

**Key negative correlations:**
- Recency days negatively correlated with all spend metrics — high spenders have purchased more recently, making high-recency/high-spend players the clearest churn risk signal
- Cohort year negatively correlated with seasons active and account age (expected by construction — players who joined in 2021 have had more time to accumulate both)

**Notable finding:** `avg_rank_score` and `avg_session_mins` correlated at 0.74. Higher-ranked players play significantly longer sessions, and combined with moderate spend correlation, rank + session depth together are stronger spend predictors than either variable alone.

---

## SQL Segmentation

Five questions were built from the heatmap findings to validate and quantify the patterns in SQL.

**Q1 — Does early spending predict future retention?**
Players who spend in their first season are significantly more likely to be retained across future seasons. Retention here is defined as being active in more than one season.

**Q2 — Do esports watchers spend more despite similar session times?**
Esports watchers are approximately twice as active and about 19.2 percentage points more likely to spend (60.9% vs. 41.7%). When controlling for longevity (spend per season), the difference in lifetime spend remains significant — the gap is not purely a function of how long they've been active.

**Q3 — Does agent diversity predict long-term engagement?**
Players using only 1–2 agents ("one-tricks") burn out more quickly and spend significantly less. Most players use 3+ agents, but the low-diversity segment is a targeting opportunity — analogous to Riot's ban mechanic in League of Legends, which forces players to expand their champion pool.

**Q4 — Who are the at-risk high-value players?**
Active players who spend do so at much higher rates than churned players. The average churned spender completed around 5 transactions — roughly matching the number of primary weapon categories in the game (rifles, snipers, shotguns, pistols). A potential retention lever: expanding the competitive meta by adding weapons, which would create new cosmetic purchase opportunities and re-engage churned players.

**Q5 — Does rank + session depth together predict spend better than either alone?**
High-rank players with medium or long sessions are the biggest spenders in the dataset. High-rank/short-session players show a slight retention dip — likely players from other FPS titles (Overwatch, CS:GO) who enjoy Valorant casually but use another game as their primary competitive outlet. Players with more active seasons spend more across all rank tiers except low rank, where spending is lower regardless — consistent with newer or less invested players prioritizing gameplay over cosmetics.

---

## Random Forest Modeling

Two models were built to test whether behavioral data could predict monetization outcomes and to weight the SQL findings under a unified model.

### Model 1: Spend Propensity (Classification)

**Target:** `is_spender` (total_spend > 0)  
Spend-derived variables (transaction count, recency, avg spend per transaction, max single transaction) were excluded to prevent data leakage. The model learns from behavior only.

**ROC-AUC: 0.7316**

| Rank | Feature |
|------|---------|
| 1 | avg_retention |
| 2 | account_age_days |
| 3 | seasons_active |
| 4 | cohort_year |
| 5 | avg_session_mins |

Retention ranked first. Players who stay engaged convert at higher rates. Account age and seasons active followed — tying monetization to long-term engagement rather than short-term spikes.

`is_esports_watcher` ranked low in feature importance despite SQL showing watchers have higher spend rates. This suggests esports watching predicts spending indirectly through retention, account age, and seasons active — not independently. Watchers may spend more because they're more engaged overall, not because watching triggers purchases.

### Model 2: Spend Amount (Regression)

**Target:** `total_spend` among spenders only  
Same leakage exclusions applied.

**R²: 0.1079 | MAE: $695 | RMSE: $1,361**

| Rank | Feature |
|------|---------|
| 1 | account_age_days |
| 2 | avg_retention |
| 3 | avg_esports_watch_hrs |
| 4 | avg_session_mins |
| 5 | avg_rank_score |
| 6 | avg_sessions_per_week |

Account age ranked first. `avg_esports_watch_hrs` ranked third — a shift from Model 1 where binary watcher status ranked low. Hours watched predicts spend depth among players who already convert. Deeper ecosystem involvement correlates with higher player value.

The low R² is expected. Spend amount in free-to-play depends on cosmetic preferences, bundle pricing, limited-time offers, personal income, and emotional attachment to specific skins — none of which appear in behavioral logs.

### Interpretation

Classification outperformed regression. Identifying likely spenders is tractable; predicting exact dollar amounts is not. The model is useful for targeting monetization-ready users, not for individual revenue forecasting.

Esports engagement functions as an ecosystem signal, not a purchase trigger. SQL showed watchers convert more; the Random Forest showed other engagement variables explain most of that conversion. Among spenders, watch hours predict spend depth. Esports engagement identifies high-value players better than it identifies first-time buyers.

---

## Business Recommendations

**High-retention non-spenders**
Retention is the strongest conversion predictor. Players who are highly retained but haven't purchased yet are the most actionable segment. Target with first-purchase campaigns: beginner bundles, personalized store offers, limited-time discounts.

**Esports-engaged spenders**
Players with high watch hours who already spend show higher revenue potential. VCT-themed cosmetics, team bundles, and event-based exclusives map directly to what this group values.

**Long-tenure, high-engagement players**
Old accounts with strong retention, multiple active seasons, and long sessions represent the highest-value tier. Loyalty programs, premium cosmetics, and reactivation campaigns are the right tools if purchase frequency starts declining.

---

## Limitations

- The dataset is synthetic. Treat these results as a portfolio-level business simulation, not a model of real Riot player behavior.
- Behavioral features miss significant spend drivers: cosmetic preferences, income, store rotation, battle pass ownership, discount history. The regression's low R² reflects those gaps directly.
- Retention, account age, and seasons active are correlated with each other. Random Forest splits importance across related features, so the exact feature ranking is less meaningful than the cluster it represents.

---

## Conclusion

Behavioral data predicts conversion better than it predicts spend amount. Retention, account age, and seasons active are the strongest signals across both models. Esports watch hours matter more for spend depth than for initial conversion.

The central finding: **monetization is a function of engagement.** Players who stay active longer, play across more seasons, and participate more in the game ecosystem become the most valuable customers. For a live-service title, retention strategy and monetization strategy are the same thing.

---

## Tools & Stack

- **Python** — data generation, EDA, Random Forest modeling (scikit-learn, pandas, seaborn)
- **SQL** — player segmentation and behavioral analysis
- **Tableau** — dashboard and visualization
- **Jupyter Notebook** — heatmap analysis and exploration
