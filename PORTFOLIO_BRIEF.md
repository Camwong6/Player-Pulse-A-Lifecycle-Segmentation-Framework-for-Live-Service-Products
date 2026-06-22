# Portfolio Brief: Player Pulse

Use this to update the portfolio page for this project. It contains the accurate, final scope — written so it can be pasted into a prompt for generating portfolio copy.

## One-line summary

A behavioral analytics case study that simulates a player monetization pipeline for a free-to-play FPS (modeled after Valorant) — combining synthetic data generation, SQL segmentation, and Random Forest modeling to answer: what behavioral signals predict monetization in a live-service game?

## Elevator pitch (2-3 sentences)

Built an end-to-end player analytics pipeline on a synthetic dataset of 100,000 Valorant-style players generating $35M+ across 500,000+ transactions. Used a correlation heatmap to surface initial signals, five targeted SQL queries to validate and quantify them, and two Random Forest models (classification + regression) to test which behaviors actually predict spend. The central finding: monetization tracks long-term engagement — retention, account age, and seasons active outperform any single "spend trigger" variable, including esports viewership.

## What I actually did (in order)

1. **Generated a synthetic dataset** of 100,000 players across 2025 with realistic free-to-play spending skew (most players spend $0, a small group drives most revenue) — `generate_datasets.py`.
2. **Ran a correlation heatmap** across all behavioral and spend features in a Jupyter notebook to find candidate relationships worth testing (`heatmap_analysis.ipynb`).
3. **Wrote 5 SQL queries** translating heatmap signals into specific, falsifiable business questions (retention vs. early spend, esports watchers vs. spend, agent diversity vs. engagement, churn risk by recency, rank+session interaction) — `EDA_SQL_QUERIES.sql`, `Joining the two datasets.sql`.
4. **Built two Random Forest models** in Python (scikit-learn) to test the SQL findings under a unified model: a classifier for spend propensity (ROC-AUC 0.7316) and a regressor for spend amount among payers (R² 0.108) — `03_random_forest_models.py`.
5. **Built a Tableau dashboard** (`Valorant_Insights_Dashboard.twb`) to visualize the segmentation and modeling results.

## Key results (use these numbers verbatim — don't round differently)

- Dataset: 100,000 players, $35M+ revenue, 500,000+ transactions
- Esports watchers: ~2x more active, 19.2 points more likely to spend (60.9% vs. 41.7%)
- `avg_rank_score` × `avg_session_mins` correlation: 0.74 (strongest non-obvious pairing)
- Model 1 (spend propensity, classification): ROC-AUC = 0.7316; top features: avg_retention, account_age_days, seasons_active
- Model 2 (spend amount, regression): R² = 0.1079, MAE = $695, RMSE = $1,361; top features: account_age_days, avg_retention, avg_esports_watch_hrs

## The interesting finding (worth leading with on a portfolio page)

SQL showed esports watchers spend more. The Random Forest showed esports-watcher status is a *weak* standalone predictor once retention/tenure/activity are in the model — meaning watching esports doesn't cause spending, it correlates with being a more engaged player overall. That reconciliation (SQL group differences vs. multivariate feature importance) is the most "senior analyst" moment in the project and is worth surfacing explicitly, since it shows the difference between a univariate finding and a controlled one.

## Tools / skills demonstrated

Python (pandas, scikit-learn, seaborn), SQL (segmentation, joins, business-question-driven queries), Tableau (dashboarding), Random Forest classification + regression, feature importance interpretation, synthetic data generation, EDA via correlation analysis.

## Honest framing for the portfolio (don't overclaim)

- This is a **synthetic dataset** built to simulate realistic F2P spending patterns — not real Riot/Valorant data. Say "modeled after Valorant" or "Valorant-style," not "Valorant player data."
- The regression model's low R² (0.108) is a legitimate, expected limitation (spend amount depends on factors not in the data — cosmetic preference, income, etc.), not a flaw to hide. It's worth stating directly: behavioral data predicts *whether* someone spends much better than *how much*.

## Suggested portfolio page structure

1. Title + one-line summary + tech stack badges (Python / SQL / Tableau / Random Forest)
2. The business question
3. Dataset description (1-2 sentences, with the headline numbers)
4. Approach: EDA → SQL → Random Forest (a simple 3-step visual works well here)
5. Headline result + the "esports watcher" reconciliation finding as the takeaway insight
6. Link to full write-up (the Word doc / README) and to the Tableau dashboard
7. Tools used

Full supporting detail (all 5 SQL questions, both models in full, limitations, business recommendations) lives in [README.md](README.md) and the companion Word report — link out rather than duplicating all of it on the portfolio page.
