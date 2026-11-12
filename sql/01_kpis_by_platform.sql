-- Which platform turns budget into results most efficiently?
-- KPIs are computed on summed metrics, never as an average of daily ratios.
SELECT
    platform,
    ROUND(SUM(spend_mxn), 2)                                           AS spend_mxn,
    SUM(impressions)                                                   AS impressions,
    SUM(clicks)                                                        AS clicks,
    SUM(conversions)                                                   AS conversions,
    ROUND(100.0 * SUM(clicks) / NULLIF(SUM(impressions), 0), 2)        AS ctr_pct,
    ROUND(SUM(spend_mxn) / NULLIF(SUM(clicks), 0), 2)                  AS cpc_mxn,
    ROUND(1000.0 * SUM(spend_mxn) / NULLIF(SUM(impressions), 0), 2)    AS cpm_mxn,
    ROUND(SUM(spend_mxn) / NULLIF(SUM(conversions), 0), 2)             AS cpa_mxn,
    ROUND(100.0 * SUM(spend_mxn) / SUM(SUM(spend_mxn)) OVER (), 1)     AS share_of_spend_pct,
    ROUND(100.0 * SUM(conversions) / SUM(SUM(conversions)) OVER (), 1) AS share_of_conversions_pct
FROM ads
GROUP BY platform
ORDER BY cpa_mxn;
