-- =============================================================================
-- 03_sql_queries.sql
-- A/B Testing Campaign — Production SQL Queries
-- Compatible with: SQLite and PostgreSQL
-- Table: campaign_data
-- =============================================================================


-- -----------------------------------------------------------------------------
-- Query 1 — Campaign Performance Summary (CTE)
-- Computes impressions, clicks, conversions, revenue, cost, CTR, CVR,
-- revenue_per_user for every campaign.
-- -----------------------------------------------------------------------------
WITH campaign_stats AS (
    SELECT
        campaign_id,
        variant,
        COUNT(user_id)              AS impressions,
        SUM(clicked)                AS clicks,
        SUM(converted)              AS conversions,
        SUM(revenue)                AS total_revenue,
        SUM(marketing_cost)         AS total_cost
    FROM campaign_data
    GROUP BY campaign_id, variant
)
SELECT
    campaign_id,
    variant,
    impressions,
    clicks,
    conversions,
    ROUND(total_revenue, 2)                                              AS total_revenue,
    ROUND(total_cost, 2)                                                 AS total_cost,
    ROUND(CAST(clicks AS REAL) / impressions * 100, 2)                  AS ctr_pct,
    ROUND(CAST(conversions AS REAL) / impressions * 100, 2)             AS cvr_pct,
    ROUND(total_revenue / impressions, 2)                               AS revenue_per_user
FROM campaign_stats
ORDER BY campaign_id;


-- -----------------------------------------------------------------------------
-- Query 2 — Conversion Rate with Running Totals (Window Function)
-- Uses OVER() to add cumulative and campaign-level stats alongside row data.
-- -----------------------------------------------------------------------------
SELECT
    campaign_id,
    user_id,
    clicked,
    converted,
    revenue,
    -- Campaign-level aggregates via window
    SUM(clicked)    OVER (PARTITION BY campaign_id)   AS campaign_total_clicks,
    SUM(converted)  OVER (PARTITION BY campaign_id)   AS campaign_total_conversions,
    COUNT(user_id)  OVER (PARTITION BY campaign_id)   AS campaign_impressions,
    ROUND(
        CAST(SUM(converted) OVER (PARTITION BY campaign_id) AS REAL)
        / COUNT(user_id)  OVER (PARTITION BY campaign_id) * 100,
        2
    )                                                 AS campaign_cvr_pct,
    -- Running conversion count within campaign ordered by impression_date
    SUM(converted)  OVER (
        PARTITION BY campaign_id
        ORDER BY impression_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )                                                 AS running_conversions
FROM campaign_data
ORDER BY campaign_id, impression_date;


-- -----------------------------------------------------------------------------
-- Query 3 — Revenue per User RANK (Window Function)
-- Ranks campaigns by revenue_per_user descending.
-- -----------------------------------------------------------------------------
WITH rev_per_user AS (
    SELECT
        campaign_id,
        ROUND(SUM(revenue) / COUNT(user_id), 2) AS revenue_per_user,
        ROUND(SUM(revenue), 2)                  AS total_revenue,
        COUNT(user_id)                          AS impressions
    FROM campaign_data
    GROUP BY campaign_id
)
SELECT
    campaign_id,
    impressions,
    total_revenue,
    revenue_per_user,
    RANK() OVER (ORDER BY revenue_per_user DESC) AS revenue_rank
FROM rev_per_user
ORDER BY revenue_rank;


-- -----------------------------------------------------------------------------
-- Query 4 — Month-over-Month Campaign Performance (LAG)
-- Compares each month's CTR and CVR to the previous month per campaign.
-- -----------------------------------------------------------------------------
WITH monthly AS (
    SELECT
        campaign_id,
        -- SQLite: strftime; PostgreSQL: TO_CHAR or DATE_TRUNC
        STRFTIME('%Y-%m', impression_date)      AS month,
        COUNT(user_id)                          AS impressions,
        SUM(clicked)                            AS clicks,
        SUM(converted)                          AS conversions,
        ROUND(CAST(SUM(clicked)    AS REAL) / COUNT(user_id) * 100, 2) AS ctr_pct,
        ROUND(CAST(SUM(converted)  AS REAL) / COUNT(user_id) * 100, 2) AS cvr_pct
    FROM campaign_data
    GROUP BY campaign_id, month
)
SELECT
    campaign_id,
    month,
    impressions,
    ctr_pct,
    cvr_pct,
    LAG(ctr_pct) OVER (PARTITION BY campaign_id ORDER BY month) AS prev_month_ctr,
    LAG(cvr_pct) OVER (PARTITION BY campaign_id ORDER BY month) AS prev_month_cvr,
    ROUND(ctr_pct - LAG(ctr_pct) OVER (PARTITION BY campaign_id ORDER BY month), 2) AS ctr_mom_delta,
    ROUND(cvr_pct - LAG(cvr_pct) OVER (PARTITION BY campaign_id ORDER BY month), 2) AS cvr_mom_delta
FROM monthly
ORDER BY campaign_id, month;


-- -----------------------------------------------------------------------------
-- Query 5 — Campaign vs Control Uplift (CTE + Self-Join)
-- Computes CVR uplift of each treatment campaign vs Campaign_A (Control).
-- -----------------------------------------------------------------------------
WITH campaign_cvr AS (
    SELECT
        campaign_id,
        variant,
        COUNT(user_id)                                                   AS impressions,
        SUM(converted)                                                   AS conversions,
        ROUND(CAST(SUM(converted) AS REAL) / COUNT(user_id) * 100, 4)   AS cvr_pct
    FROM campaign_data
    GROUP BY campaign_id, variant
),
control AS (
    SELECT cvr_pct AS control_cvr
    FROM campaign_cvr
    WHERE campaign_id = 'Campaign_A'
)
SELECT
    t.campaign_id,
    t.variant,
    t.impressions,
    t.conversions,
    t.cvr_pct                                                        AS treatment_cvr,
    c.control_cvr,
    ROUND((t.cvr_pct - c.control_cvr) / c.control_cvr * 100, 2)    AS uplift_pct
FROM campaign_cvr t
CROSS JOIN control c
ORDER BY uplift_pct DESC;


-- -----------------------------------------------------------------------------
-- Query 6 — Top Converting Channel per Campaign (RANK + PARTITION)
-- Finds the best-performing channel per campaign by conversion rate.
-- Returns only RANK = 1 (top channel per campaign).
-- -----------------------------------------------------------------------------
WITH channel_stats AS (
    SELECT
        campaign_id,
        channel,
        COUNT(user_id)                                                   AS impressions,
        SUM(converted)                                                   AS conversions,
        ROUND(CAST(SUM(converted) AS REAL) / COUNT(user_id) * 100, 2)   AS cvr_pct,
        RANK() OVER (
            PARTITION BY campaign_id
            ORDER BY CAST(SUM(converted) AS REAL) / COUNT(user_id) DESC
        )                                                                AS channel_rank
    FROM campaign_data
    GROUP BY campaign_id, channel
)
SELECT
    campaign_id,
    channel,
    impressions,
    conversions,
    cvr_pct,
    channel_rank
FROM channel_stats
WHERE channel_rank = 1
ORDER BY campaign_id;


-- -----------------------------------------------------------------------------
-- Query 7 — ROI Analysis by Campaign (CTE)
-- ROI = (revenue - cost) / cost * 100. Campaigns ranked by ROI.
-- -----------------------------------------------------------------------------
WITH roi_calc AS (
    SELECT
        campaign_id,
        variant,
        ROUND(SUM(revenue), 2)          AS total_revenue,
        ROUND(SUM(marketing_cost), 2)   AS total_cost,
        ROUND(
            (SUM(revenue) - SUM(marketing_cost)) / SUM(marketing_cost) * 100,
            2
        )                               AS roi_pct
    FROM campaign_data
    GROUP BY campaign_id, variant
)
SELECT
    campaign_id,
    variant,
    total_revenue,
    total_cost,
    roi_pct,
    RANK() OVER (ORDER BY roi_pct DESC) AS roi_rank
FROM roi_calc
ORDER BY roi_rank;


-- -----------------------------------------------------------------------------
-- Query 8 — Device Performance Analysis (Pivot-style with CASE)
-- Shows conversion rate for mobile, desktop, and tablet as separate columns
-- per campaign.
-- -----------------------------------------------------------------------------
SELECT
    campaign_id,
    COUNT(user_id)                                              AS total_impressions,
    -- Mobile
    ROUND(
        CAST(SUM(CASE WHEN device = 'mobile'  THEN converted ELSE 0 END) AS REAL)
        / NULLIF(SUM(CASE WHEN device = 'mobile'  THEN 1 ELSE 0 END), 0) * 100,
        2
    )                                                           AS mobile_cvr_pct,
    -- Desktop
    ROUND(
        CAST(SUM(CASE WHEN device = 'desktop' THEN converted ELSE 0 END) AS REAL)
        / NULLIF(SUM(CASE WHEN device = 'desktop' THEN 1 ELSE 0 END), 0) * 100,
        2
    )                                                           AS desktop_cvr_pct,
    -- Tablet
    ROUND(
        CAST(SUM(CASE WHEN device = 'tablet'  THEN converted ELSE 0 END) AS REAL)
        / NULLIF(SUM(CASE WHEN device = 'tablet'  THEN 1 ELSE 0 END), 0) * 100,
        2
    )                                                           AS tablet_cvr_pct
FROM campaign_data
GROUP BY campaign_id
ORDER BY campaign_id;
