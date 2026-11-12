"""Standard performance KPIs, computed the same way for every platform."""
from __future__ import annotations

import pandas as pd

RAW_METRICS = ["spend_mxn", "impressions", "clicks", "conversions"]


def _ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Division that returns NaN (not an error or infinity) when the denominator is 0."""
    safe = denominator.where(denominator != 0)
    return numerator / safe


def summarize(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Add up the raw metrics for each group, then compute KPIs on the totals.

    KPIs are always computed from summed metrics. Averaging daily CTRs or CPAs
    gives the wrong answer because small days weigh as much as big days.
    """
    totals = df.groupby(by, as_index=False)[RAW_METRICS].sum()
    totals["ctr_pct"] = _ratio(totals["clicks"], totals["impressions"]) * 100
    totals["cpc_mxn"] = _ratio(totals["spend_mxn"], totals["clicks"])
    totals["cpm_mxn"] = _ratio(totals["spend_mxn"], totals["impressions"]) * 1000
    totals["cvr_pct"] = _ratio(totals["conversions"], totals["clicks"]) * 100
    totals["cpa_mxn"] = _ratio(totals["spend_mxn"], totals["conversions"])
    return totals.round(
        {"spend_mxn": 2, "ctr_pct": 2, "cpc_mxn": 2, "cpm_mxn": 2, "cvr_pct": 2, "cpa_mxn": 2}
    )
