-- Week-by-week cost per conversion per platform, with the change versus the
-- previous week. Partial weeks (fewer than 7 days of data) are excluded so a
-- short week is never compared against a full one.
WITH weekly AS (
    SELECT
        platform,
        DATE(date, 'weekday 0', '-6 days') AS week_start,   -- Monday of that week
        COUNT(DISTINCT date)               AS days_with_data,
        SUM(spend_mxn)                     AS spend_mxn,
        SUM(conversions)                   AS conversions
    FROM ads
    GROUP BY platform, week_start
),
full_weeks AS (
    SELECT *, spend_mxn / NULLIF(conversions, 0) AS cpa_mxn
    FROM weekly
    WHERE days_with_data = 7
)
SELECT
    platform,
    week_start,
    ROUND(spend_mxn, 2) AS spend_mxn,
    conversions,
    ROUND(cpa_mxn, 2)   AS cpa_mxn,
    ROUND(
        100.0 * (cpa_mxn - LAG(cpa_mxn) OVER (PARTITION BY platform ORDER BY week_start))
        / LAG(cpa_mxn) OVER (PARTITION BY platform ORDER BY week_start), 1
    )                   AS cpa_change_vs_prev_week_pct
FROM full_weeks
ORDER BY platform, week_start;
