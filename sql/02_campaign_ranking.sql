-- Rank every campaign x platform combination by cost per conversion.
-- rank_in_campaign = 1 marks the cheapest platform for that campaign.
WITH totals AS (
    SELECT
        campaign_key,
        platform,
        SUM(spend_mxn)   AS spend_mxn,
        SUM(conversions) AS conversions
    FROM ads
    GROUP BY campaign_key, platform
)
SELECT
    campaign_key,
    platform,
    ROUND(spend_mxn, 2)                          AS spend_mxn,
    conversions,
    ROUND(spend_mxn / NULLIF(conversions, 0), 2) AS cpa_mxn,
    RANK() OVER (
        PARTITION BY campaign_key
        ORDER BY spend_mxn / NULLIF(conversions, 0)
    )                                            AS rank_in_campaign
FROM totals
ORDER BY campaign_key, rank_in_campaign;
