-- =============================================================================
-- HEATMAP FOLLOW-UP QUERIES
-- Each query answers a specific business question surfaced by the correlation
-- heatmap. Run them in order — they build on each other narratively.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- Q1: Does early spending predict future retention?
-- Heatmap signal: transaction variables correlated with retention & account age
-- Business question: Do players who spend in their first season retain better
--                    in the seasons that follow?
-- -----------------------------------------------------------------------------
WITH first_txn AS (
    SELECT
        user_id,
        MIN(YEAR(transaction_date))     AS first_spend_year
    FROM transactions
    GROUP BY user_id
),
first_season_spend AS (
    SELECT
        b.user_id,
        b.season,
        b.retained_30d,
        CASE WHEN f.first_spend_year = b.season THEN 1 ELSE 0 END AS spent_this_season,
        CASE WHEN f.first_spend_year < b.season  THEN 1 ELSE 0 END AS spent_prior_season
    FROM valorant_player_behavior b
    LEFT JOIN first_txn f ON b.user_id = f.user_id
)
SELECT
    spent_prior_season                          AS had_prior_spend,
    COUNT(*)                                    AS player_count,
    ROUND(AVG(retained_30d) * 100, 1)          AS retention_pct
FROM first_season_spend
WHERE season > 2021   -- need at least one prior season to compare
GROUP BY spent_prior_season
ORDER BY spent_prior_season;

#Players who spend prior are 78.9-67.5 = 11.4% more likely to be retained
-- -----------------------------------------------------------------------------
-- Q2: Do esports watchers spend more despite similar session times?
-- Heatmap signal: is_esports_watcher correlated with seasons_active but
--                 esports_watch_hrs shows near-zero spend correlation
-- Business question: Is watching esports a spend signal, or just an
--                    engagement signal?
-- -----------------------------------------------------------------------------
WITH player_summary AS (
    SELECT
        b.user_id,
        MAX(b.is_esports_watcher)               AS is_esports_watcher,
        ROUND(AVG(b.avg_session_mins), 1)        AS avg_session_mins,
        COUNT(DISTINCT b.season)                 AS seasons_active,
        COALESCE(SUM(t.amount), 0)              AS total_spend,
        COUNT(t.transaction_date)               AS transaction_count
    FROM valorant_player_behavior b
    LEFT JOIN transactions t ON b.user_id = t.user_id
    GROUP BY b.user_id
)
SELECT
    is_esports_watcher,
    COUNT(*)                                    AS players,
    ROUND(AVG(avg_session_mins), 1)             AS avg_session_mins,
    ROUND(AVG(seasons_active), 1)               AS avg_seasons_active,
    ROUND(AVG(total_spend), 2)                  AS avg_spend_all_users,
    ROUND(AVG(CASE WHEN total_spend > 0
              THEN total_spend END), 2)         AS avg_spend_among_spenders,
    ROUND(SUM(CASE WHEN total_spend > 0
              THEN 1 ELSE 0 END) * 100.0
              / COUNT(*), 1)                    AS pct_who_spend
FROM player_summary
GROUP BY is_esports_watcher;
-- -----------------------------------------------------------------------------
-- Q2b: Esports watchers — spend per season (controls for longevity)
-- Business question: Do watchers spend more per season, or just because
--                    they stick around longer?
-- This version divides spend by seasons_active so both groups are compared
-- on a level playing field regardless of how long they've been active.
-- -----------------------------------------------------------------------------
WITH player_summary AS (
    SELECT
        b.user_id,
        MAX(b.is_esports_watcher)               AS is_esports_watcher,
        ROUND(AVG(b.avg_session_mins), 1)        AS avg_session_mins,
        COUNT(DISTINCT b.season)                 AS seasons_active,
        COALESCE(SUM(t.amount), 0)              AS total_spend
    FROM valorant_player_behavior b
    LEFT JOIN transactions t ON b.user_id = t.user_id
    GROUP BY b.user_id
)
SELECT
    is_esports_watcher,
    COUNT(*)                                            AS players,
    ROUND(AVG(seasons_active), 1)                       AS avg_seasons_active,
    ROUND(AVG(total_spend), 2)                          AS avg_lifetime_spend,
    -- Spend per season — the controlled metric
    ROUND(AVG(total_spend / seasons_active), 2)         AS avg_spend_per_season,
    ROUND(AVG(CASE WHEN total_spend > 0
              THEN total_spend / seasons_active END), 2) AS avg_spend_per_season_spenders_only,
    ROUND(SUM(CASE WHEN total_spend > 0
              THEN 1 ELSE 0 END) * 100.0
              / COUNT(*), 1)                            AS pct_who_spend
FROM player_summary
GROUP BY is_esports_watcher;
 

-- -----------------------------------------------------------------------------
-- Q3: Does agent diversity predict long-term engagement?
-- Heatmap signal: avg_agent_diversity correlated with seasons_active (0.37)
-- Business question: Do players who experiment with more agents stay longer,
--                    and does this hold across rank tiers?
-- -----------------------------------------------------------------------------
SELECT
    CASE
        WHEN avg_agent_diversity <= 2  THEN '1-2 agents (one-trick)'
        WHEN avg_agent_diversity <= 5  THEN '3-5 agents (flexible)'
        WHEN avg_agent_diversity <= 9  THEN '6-9 agents (experimental)'
        ELSE '10+ agents (explorer)'
    END                                         AS diversity_bucket,
    COUNT(DISTINCT user_id)                     AS players,
    ROUND(AVG(seasons_active), 2)               AS avg_seasons_active,
    ROUND(AVG(avg_retention) * 100, 1)         AS avg_retention_pct,
    ROUND(AVG(total_spend), 2)                  AS avg_total_spend
FROM (
    SELECT
        b.user_id,
        AVG(b.agent_diversity)                  AS avg_agent_diversity,
        COUNT(DISTINCT b.season)                AS seasons_active,
        AVG(b.retained_30d)                     AS avg_retention,
        COALESCE(SUM(t.amount), 0)             AS total_spend
    FROM valorant_player_behavior b
    LEFT JOIN transactions t ON b.user_id = t.user_id
    GROUP BY b.user_id
) player_agg
GROUP BY diversity_bucket
ORDER BY MIN(avg_agent_diversity);


-- -----------------------------------------------------------------------------
-- Q4: Who are the at-risk high-value players?
-- Heatmap signal: days_since_last_purchase negatively correlated with all spend metrics
-- Business question: Which previously high-spending players haven't purchased
--                    recently — and how much revenue is at risk?
-- -----------------------------------------------------------------------------
WITH player_spend AS (
    SELECT
        user_id,
        COUNT(*)                                AS transaction_count,
        ROUND(SUM(amount), 2)                   AS total_spend,
        MAX(transaction_date)                   AS last_purchase,
        DATEDIFF('2025-12-31', MAX(transaction_date)) AS days_since_last_purchase
    FROM transactions
    GROUP BY user_id
)
SELECT
    CASE
        WHEN days_since_last_purchase <= 90  THEN 'Active (< 90 days)'
        WHEN days_since_last_purchase <= 180 THEN 'Lapsing (90–180 days)'
        WHEN days_since_last_purchase <= 365 THEN 'At Risk (180–365 days)'
        ELSE 'Churned (365+ days)'
    END                                         AS recency_segment,
    COUNT(*)                                    AS players,
    ROUND(AVG(total_spend), 2)                  AS avg_lifetime_spend,
    ROUND(SUM(total_spend), 2)                  AS total_revenue,
    ROUND(AVG(transaction_count), 1)            AS avg_transactions,
    ROUND(AVG(days_since_last_purchase), 0)                 AS avg_days_since_last_purchase
FROM player_spend
GROUP BY recency_segment
ORDER BY MIN(days_since_last_purchase);



-- -----------------------------------------------------------------------------
-- Q5: Does rank + session depth together predict spend better than either alone?
-- Heatmap signal: avg_rank_score ↔ avg_session_mins (0.74), both moderately
--                 correlated with spend
-- Business question: Is there a high-value segment defined by BOTH high rank
--                    AND long sessions that outspends all other combinations?
-- -----------------------------------------------------------------------------
SELECT
    CASE
        WHEN avg_rank_score >= 6 THEN 'High Rank (Diamond+)'
        WHEN avg_rank_score >= 4 THEN 'Mid Rank (Gold–Platinum)'
        ELSE 'Low Rank (Iron–Silver)'
    END                                         AS rank_tier,
    CASE
        WHEN avg_session_mins >= 60 THEN 'Long Sessions (60+ min)'
        WHEN avg_session_mins >= 40 THEN 'Medium Sessions (40–60 min)'
        ELSE 'Short Sessions (< 40 min)'
    END                                         AS session_tier,
    COUNT(DISTINCT user_id)                     AS players,
    ROUND(AVG(total_spend), 2)                  AS avg_total_spend,
    ROUND(AVG(avg_retention) * 100, 1)         AS avg_retention_pct,
    ROUND(AVG(seasons_active), 1)               AS avg_seasons_active
FROM (
    SELECT
        b.user_id,
        AVG(CASE `rank`
            WHEN 'Iron'      THEN 1 WHEN 'Bronze'    THEN 2
            WHEN 'Silver'    THEN 3 WHEN 'Gold'      THEN 4
            WHEN 'Platinum'  THEN 5 WHEN 'Diamond'   THEN 6
            WHEN 'Ascendant' THEN 7 WHEN 'Immortal'  THEN 8
            WHEN 'Radiant'   THEN 9
        END)                                    AS avg_rank_score,
        AVG(b.avg_session_mins)                 AS avg_session_mins,
        AVG(b.retained_30d)                     AS avg_retention,
        COUNT(DISTINCT b.season)                AS seasons_active,
        COALESCE(SUM(t.amount), 0)             AS total_spend
    FROM valorant_player_behavior b
    LEFT JOIN transactions t ON b.user_id = t.user_id
    GROUP BY b.user_id
) player_agg
GROUP BY rank_tier, session_tier
ORDER BY avg_total_spend DESC;