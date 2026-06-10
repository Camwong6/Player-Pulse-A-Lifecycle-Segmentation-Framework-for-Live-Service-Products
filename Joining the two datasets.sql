-- =============================================================================
-- HEATMAP JOIN QUERY
-- Aggregates both tables to one row per user, then joins them.
-- Export this result as CSV and feed it directly into the Python heatmap.
--
-- To export in Workbench:
--   Run the query → click the Export button above the result grid
--   → Save as heatmap_data.csv in your project folder
-- =============================================================================

WITH behavior_agg AS (
    SELECT
        user_id,

        -- How many seasons was this user active
        COUNT(DISTINCT season)                          AS seasons_active,
        MIN(season)                                     AS cohort_year,
        MAX(season)                                     AS last_active_season,

        -- Session behavior averaged across all seasons
        ROUND(AVG(avg_session_mins), 2)                 AS avg_session_mins,
        ROUND(AVG(sessions_per_week), 2)                AS avg_sessions_per_week,
        ROUND(AVG(esports_watch_hrs), 2)                AS avg_esports_watch_hrs,
        ROUND(AVG(agent_diversity), 2)                  AS avg_agent_diversity,
        ROUND(AVG(cross_platform_hrs), 2)               AS avg_cross_platform_hrs,

        -- Flags — take the max so if it was ever 1 it counts
        MAX(is_esports_watcher)                         AS is_esports_watcher,
        MAX(is_cross_platform)                          AS is_cross_platform,

        -- Retention — average across seasons (% of seasons they were retained)
        ROUND(AVG(retained_30d), 4)                     AS avg_retention,

        -- Rank progression — convert rank to a numeric scale so it's usable
        ROUND(AVG(
            CASE `rank`
                WHEN 'Iron'      THEN 1
                WHEN 'Bronze'    THEN 2
                WHEN 'Silver'    THEN 3
                WHEN 'Gold'      THEN 4
                WHEN 'Platinum'  THEN 5
                WHEN 'Diamond'   THEN 6
                WHEN 'Ascendant' THEN 7
                WHEN 'Immortal'  THEN 8
                WHEN 'Radiant'   THEN 9
            END
        ), 2)                                           AS avg_rank_score,

        -- Peak rank reached
        MAX(CASE `rank`
                WHEN 'Iron'      THEN 1
                WHEN 'Bronze'    THEN 2
                WHEN 'Silver'    THEN 3
                WHEN 'Gold'      THEN 4
                WHEN 'Platinum'  THEN 5
                WHEN 'Diamond'   THEN 6
                WHEN 'Ascendant' THEN 7
                WHEN 'Immortal'  THEN 8
                WHEN 'Radiant'   THEN 9
            END)                                        AS peak_rank_score,

        -- Account age from most recent season row
        MAX(account_age_days)                           AS account_age_days

    FROM valorant_player_behavior
    GROUP BY user_id
),

transaction_agg AS (
    SELECT
        user_id,
        COUNT(*)                                        AS transaction_count,
        ROUND(SUM(amount), 2)                           AS total_spend,
        ROUND(AVG(amount), 2)                           AS avg_spend_per_txn,
        ROUND(MAX(amount), 2)                           AS max_single_txn,
        DATEDIFF('2025-12-31', MAX(transaction_date))   AS recency_days
    FROM transactions
    GROUP BY user_id
)

SELECT
    b.user_id,
    b.cohort_year,
    b.seasons_active,
    b.avg_rank_score,
    b.peak_rank_score,
    b.avg_session_mins,
    b.avg_sessions_per_week,
    b.avg_esports_watch_hrs,
    b.is_esports_watcher,
    b.avg_agent_diversity,
    b.avg_cross_platform_hrs,
    b.is_cross_platform,
    b.account_age_days,
    b.avg_retention,
    -- Transaction columns (0 for non-spenders)
    COALESCE(t.transaction_count, 0)    AS transaction_count,
    COALESCE(t.total_spend, 0)          AS total_spend,
    COALESCE(t.avg_spend_per_txn, 0)    AS avg_spend_per_txn,
    COALESCE(t.max_single_txn, 0)       AS max_single_txn,
    COALESCE(t.recency_days, 999)       AS recency_days

FROM behavior_agg b
LEFT JOIN transaction_agg t ON b.user_id = t.user_id
ORDER BY b.user_id;
