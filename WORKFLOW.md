# Player Pulse — Project Workflow
**End-to-end gaming analytics pipeline: Python → SQL → Live Dashboard → Portfolio Write-Up**

---

## Project Goal

Demonstrate the complete analyst skill set — data engineering, statistical analysis, SQL fluency, and BI dashboarding — within a gaming context. The final deliverable is a portfolio page that tells a clean story:

> **Problem → Method → Insight → Recommendation**

This is the personal project that signals genuine curiosity in the gaming industry. Every phase produces a concrete, linkable artifact.

---

## Portfolio Story Arc

| Stage | Question |
|-------|----------|
| **Problem** | Live-service games lose players silently — by the time a player churns, the window for intervention has closed. How do we identify who's at risk *before* they leave, and what actions maximize reactivation ROI? |
| **Method** | Build a realistic synthetic player dataset → RFM lifecycle segmentation → behavioral analysis → SQL KPI layer → live dashboard for monitoring |
| **Insight** | Champions (21.9% of users) drive 73.2% of revenue. 798 At-Risk players have average historical spend of $457/user but haven't engaged in ~261 days — the highest ROI reactivation target. Cross-platform players retain at a significantly higher rate (χ² confirmed). |
| **Recommendation** | Segment-specific playbooks with projected impact: prioritize At-Risk reactivation over Lost suppression, invest in cross-platform bridge content as a retention lever, use esports event windows as re-engagement moments. |

---

## Phase 0 — Repo & Project Hygiene
**Purpose:** Make the project credible before a hiring manager clicks a single link.

- [ ] Initialize public GitHub repo: `player-pulse-gaming-analytics`
- [ ] Write `README.md` with project overview, tech stack, and links to each deliverable (notebook → SQL → dashboard)
- [ ] Add `.gitignore` for notebook checkpoints, `.DS_Store`, `__pycache__`
- [ ] Commit all existing notebooks with a clean history
- [ ] Add a `requirements.txt` so anyone can reproduce the environment

**Why this matters:** The portfolio feedback specifically flagged "no GitHub links on project pages." Not linking code raises the question of whether the technical work is yours. Fix this before anything else.

---

## Phase 1 — Python: Data Foundation & Behavioral Analysis
**Status:** Largely complete. Gaps to close below.

### 1A — Master Joined Dataset
The two notebooks generate separate datasets that share `user_id` as a primary key. Create a single joined master dataset and export it as `player_pulse_master.csv`. This CSV feeds Phases 2 and 3.

**Columns to include:**
- From `rfm_segmentation.ipynb`: `user_id`, `recency`, `frequency`, `monetary`, `R_score`, `F_score`, `M_score`, `RFM_score`, `segment`
- From `valorant_player_behavior.ipynb`: `rank`, `account_age_days`, `avg_session_mins`, `sessions_per_week`, `esports_watch_hrs`, `is_esports_watcher`, `primary_agent`, `primary_role`, `agent_diversity`, `cross_platform_hrs`, `is_cross_platform`, `retained_30d`

**Tasks:**
- [ ] Run `rfm_segmentation.ipynb` end-to-end → confirms `rfm_segments_output.csv` exists
- [ ] Run `valorant_player_behavior.ipynb` end-to-end → confirms `valorant_player_behavior.csv` exists
- [ ] Merge on `user_id` → export `player_pulse_master.csv`

### 1B — Cross-Notebook Analysis (New Notebook: `player_pulse_combined.ipynb`)
This is the analytical payoff that neither notebook delivers alone. Creates the most compelling visuals for the portfolio.

**Analysis to add:**
- [ ] **Segment × Behavioral Profile Table**: Mean session duration, sessions/week, watch time, cross-platform hours, and retention rate broken out by RFM segment (Champions through Lost). This directly answers "what do our best players look like behaviorally?"
- [ ] **Retention Rate by RFM Segment**: Bar chart showing 30-day retention by segment — confirms the segmentation framework has real predictive value
- [ ] **Churn Risk Score per User**: Use the GBM model from `valorant_player_behavior.ipynb` to score all 5,000 users. Output a ranked "intervention list" of At-Risk users sorted by churn probability × historical monetary value (expected ROI of reactivating them)
- [ ] **Cohort Retention Curve**: Simulate D1, D7, D30 retention using `account_age_days` and `recency` as proxies. Classic gaming KPI that any hiring manager will recognize.
- [ ] **Revenue Concentration (Pareto)**: Show that the top 20% of users by monetary value drive ~80% of revenue. Quantify this exactly and put the number in the write-up.

**Deliverable:** One polished notebook with a clear narrative, clean markdown headers for each section, and every chart saved to `/figures/` for the portfolio page.

### 1C — Specific Numbers to Capture for Write-Up
Pull these during Phase 1 and document them — they go directly into the portfolio page and resume bullets:

| Metric | Where | Use |
|--------|-------|-----|
| % of revenue from top 20% of users | Pareto analysis | Resume bullet, write-up |
| At-Risk segment avg. monetary value | Segment summary | Write-up recommendation |
| Churn model AUC | GBM model output | Portfolio metrics (like Airbnb's 93.28% accuracy) |
| Retention lift: cross-platform vs. single | Chi-square result | Insight section |
| Esports watcher session frequency delta | t-test result | Insight section |
| Silhouette score at k=5 | Clustering output | Methodology credibility |

---

## Phase 2 — SQL: KPI Layer
**Purpose:** Prove SQL depth with complex queries. SQL fluency is expected at every analytics role — this phase makes it visible.

### 2A — Database Setup
- [ ] Load `player_pulse_master.csv` into **SQLite** (no server needed) or **DuckDB** (faster, better for analytics)
- [ ] Create a `queries/` folder in the repo
- [ ] Each query saved as its own `.sql` file with a comment block explaining the business question

**Tables to create:**
```sql
-- players: one row per user, all behavioral and RFM features
-- transactions: raw transaction log from rfm_segmentation data generation
-- sessions: derived session-level data (user_id, date, session_mins)
```

### 2B — Queries to Write (8 Core KPIs)
Each demonstrates a different SQL concept. These are the queries a gaming analyst writes every week.

**1. DAU/MAU Ratio (Rolling 28-Day Active Users)**
```sql
-- Window function: COUNT(DISTINCT user_id) over rolling 28-day window
-- Business question: Is engagement growing or shrinking month-over-month?
```

**2. D1 / D7 / D30 Retention Cohort**
```sql
-- Self-join on transactions table, grouped by acquisition week
-- Business question: What % of new users return after 1, 7, and 30 days?
-- SQL concepts: CTE, self-join, DATE arithmetic, CASE WHEN
```

**3. Revenue Concentration (Pareto)**
```sql
-- NTILE(10) to bucket users by spend, then cumulative revenue share
-- Business question: What % of users drive 80% of revenue?
-- SQL concepts: Window functions (NTILE, SUM OVER), running totals
```

**4. ARPU and ARPPU by Segment**
```sql
-- Total revenue / total users vs. total revenue / paying users only
-- Business question: Which segments are monetizing efficiently?
-- SQL concepts: FILTER, conditional aggregation
```

**5. At-Risk Early Warning Query (Production-Ready)**
```sql
-- Identifies users who: were in top 2 spend quintiles historically,
-- AND have not transacted in the last 30 days
-- Business question: Which high-value users should the CRM team contact this week?
-- SQL concepts: Subquery, HAVING, date filtering
```

**6. Segment Health Monitor**
```sql
-- Count of users per segment and % change week-over-week
-- Business question: Is the Champions segment growing or shrinking?
-- SQL concepts: LAG(), percent change calculation
```

**7. Cross-Platform Retention Lift**
```sql
-- Compare 30-day retention rate for cross-platform vs. single-platform users
-- Segment the result by RFM segment to find where the lift is strongest
-- SQL concepts: GROUP BY multi-column, CASE WHEN, ratio calculation
```

**8. Esports Watcher Engagement Analysis**
```sql
-- Average sessions/week for watchers vs. non-watchers, broken out by rank tier
-- Business question: Is esports engagement a meaningful signal by competitive tier?
-- SQL concepts: Multi-level GROUP BY, CASE WHEN bucketing
```

**Tasks:**
- [ ] Write and test all 8 queries
- [ ] Add a `SQL_README.md` in the `queries/` folder explaining the business question each query answers
- [ ] Take clean screenshots of query results for the portfolio page
- [ ] Export one or two query results as CSVs for the dashboard

---

## Phase 3 — Live Dashboard
**Purpose:** This is the #1 gap in the portfolio. Every competitor lists Power BI and Tableau — a live embedded dashboard is the proof. One dashboard here does more than a dozen bullet points.

### 3A — Tool Selection
**Recommended: Tableau Public** (free, shareable link, embeddable)
- Tableau is listed as a core skill but never appears in a work bullet — this directly fixes that gap
- Tableau Public generates a live URL to embed or screenshot for the portfolio
- Alternative: Power BI Service (also free, also embeddable, also acceptable)

### 3B — Dashboard Structure (3 Pages / Views)

**Page 1: Executive Overview**
- KPI cards: Total Users, Total Revenue, Avg. Session Duration, 30-Day Retention Rate
- Line chart: Weekly transaction volume over time
- Bar chart: Revenue by month

**Page 2: Player Segmentation Deep-Dive**
- Segment breakdown: Users and revenue share by Champions / Loyal / At Risk / Dormant / Lost
- RFM heatmap: Mean R, F, M score per segment
- Scatter: Recency vs. Frequency colored by segment
- Filter: Clickable segment selector that drives all other views

**Page 3: At-Risk Monitor / Action Board**
- Table: Top 50 At-Risk users ranked by churn probability × historical spend (expected reactivation value)
- Bar: Churn model feature importances (sessions/week, cross-platform hours, rank)
- Metric: Estimated revenue at risk if no action taken (sum of At-Risk segment monetary values)

### 3C — Tasks
- [ ] Connect Tableau / Power BI to `player_pulse_master.csv` and SQL query exports
- [ ] Build all 3 dashboard pages
- [ ] Publish to Tableau Public or Power BI Service
- [ ] Get the shareable URL → add to portfolio page and GitHub README
- [ ] Take a high-quality screenshot for the portfolio card image

---

## Phase 4 — Write-Up & Portfolio Page
**Purpose:** The Airbnb project is the only one in the current portfolio that follows the full problem → method → insight → recommendation arc. This project matches that standard.

### 4A — Write-Up Structure

```
Header: Player Pulse — Gaming Player Lifecycle Analytics
Subtitle: Python · SQL · Tableau · Machine Learning

[1] Problem
Live-service games lose players silently. By the time a player churns,
reactivation costs 5-10x more than retention. The question isn't "how do
we win them back?" — it's "which players are showing early warning signs,
and what do we do about it right now?"

[2] Dataset
Synthetic dataset of 5,000 players across 12 months, designed to mirror
real game telemetry: transaction logs, session metrics, competitive rank,
esports engagement, and cross-platform activity. Schema maps directly to
common data warehouse event-log patterns.

[3] Method
→ RFM segmentation: K-Means clustering on quintile-scored Recency,
  Frequency, and Monetary dimensions. k=5 validated by elbow method
  (silhouette = X.XXX).
→ Behavioral analysis: t-tests and chi-square tests to confirm statistical
  significance of esports watch time and cross-platform engagement as
  retention signals.
→ Churn prediction: Gradient Boosting classifier (AUC = X.XX) using
  session metrics, engagement flags, and RFM scores as features.
→ SQL KPI layer: 8 production-style queries in SQLite covering DAU/MAU,
  cohort retention, revenue concentration, and at-risk identification.
→ Live dashboard: Tableau Public dashboard with 3 pages — executive view,
  segmentation deep-dive, and at-risk action board.

[4] Key Insights
1. Champions (21.9% of users) drive 73.2% of revenue — the top X% drive
   ~80% (Pareto confirmed). Protecting this segment is the highest-value
   retention action.
2. 798 At-Risk players show average historical spend of $457/user but
   haven't engaged in ~261 days. Reactivating even 20% represents ~$XX,XXX
   in recovered revenue.
3. Cross-platform players retain at significantly higher 30-day rates
   (χ²=XX.X, p<0.001). Cross-promotion of other Riot titles is a
   measurable retention lever.
4. Esports watchers play X more sessions/week than non-watchers (t-test
   significant). VCT event windows are high-value re-engagement moments.

[5] Recommendations
→ Champions: VIP program, early content access, protect LTV — avoid
  over-monetizing this segment.
→ At Risk (immediate priority): Targeted re-engagement campaign during
  next patch or content drop. Estimated reactivation value: $XX,XXX.
→ Cross-platform bridge content: In-client promotion of TFT/LoL for
  players showing declining session frequency. Highest ROI retention lever.
→ Esports integration: Watch-reward mechanics during VCT events to
  reactivate Dormant segment.

[GitHub] [Live Dashboard] [SQL Queries]
```

### 4B — Tasks
- [ ] Write the portfolio page in the format above (all numbers filled in from Phase 1 outputs)
- [ ] Add the live dashboard URL
- [ ] Link the GitHub repo
- [ ] Add the dashboard screenshot as the project card image (replaces the WIP placeholder)
- [ ] Write all bullets in past tense, confident language ("Built," "Identified," "Demonstrated" — not "developing" or "will be designed")

---

## Deliverable Checklist — What a Hiring Manager Sees

| Artifact | Location | Gap it Closes |
|----------|----------|---------------|
| Python notebooks (3) | GitHub repo | Code credibility, technical proof |
| SQL queries folder | GitHub repo | SQL depth beyond bullet points |
| Live dashboard | Tableau Public / Power BI Service URL | #1 portfolio gap — no live dashboards |
| Portfolio write-up | Portfolio site | Complete story: problem → insight → recommendation |
| GitHub README | Repo root | Navigation, reproducibility, professionalism |

---

## Tech Stack

| Tool | Phase | Skill Demonstrated |
|------|-------|--------------------|
| Python (pandas, scikit-learn, matplotlib, seaborn) | 1 | Data engineering, ML, visualization |
| SQLite / DuckDB | 2 | SQL — CTEs, window functions, joins |
| Tableau Public or Power BI | 3 | BI dashboarding (proves the skill, not just lists it) |
| GitHub | All | Version control, portfolio presentation |

---

## Estimated Effort

| Phase | Tasks Remaining | Effort |
|-------|----------------|--------|
| Phase 0 | GitHub setup, README | ~1 hour |
| Phase 1 | Combined notebook, metrics capture | ~3–4 hours |
| Phase 2 | 8 SQL queries + setup | ~3–4 hours |
| Phase 3 | Dashboard build + publish | ~4–6 hours |
| Phase 4 | Write-up + portfolio update | ~2–3 hours |
| **Total** | | **~13–18 hours** |
