import math
from pathlib import Path

import pandas as pd

from paidmedia.kpis import summarize
from paidmedia.pipeline import ROOT, detect_platform, run, unify
from paidmedia.sample_data import generate


def _ads(rows):
    return pd.DataFrame(rows, columns=["platform", "spend_mxn", "impressions", "clicks",
                                       "conversions"])


def test_kpis_are_computed_on_totals_not_averaged():
    # Day 1: CPA 100. Day 2: CPA 10. The true CPA is 200/11, not the average of 100 and 10.
    ads = _ads([["meta", 100.0, 1000, 10, 1], ["meta", 100.0, 1000, 10, 10]])
    result = summarize(ads, by=["platform"]).iloc[0]
    assert result["cpa_mxn"] == round(200 / 11, 2)
    assert result["ctr_pct"] == 1.0
    assert result["cpm_mxn"] == 100.0


def test_zero_conversions_gives_empty_cpa_not_a_crash():
    result = summarize(_ads([["tiktok", 50.0, 500, 0, 0]]), by=["platform"]).iloc[0]
    assert math.isnan(result["cpa_mxn"])
    assert math.isnan(result["cpc_mxn"])


def test_detect_platform_from_file_name():
    assert detect_platform("Meta_ads_october.csv") == "meta"


def test_clean_spend_reconciles_with_each_platform_total_row(tmp_path: Path):
    """After cleaning, spend per platform must match the total the platform itself reports."""
    generate(tmp_path)
    unified = unify(tmp_path)
    cleaned = unified.groupby("platform")["spend_mxn"].sum()

    meta_total = float(pd.read_csv(tmp_path / "meta_ads.csv", dtype=str)
                       .iloc[-1]["Amount spent (MXN)"])
    google_total = float(pd.read_csv(tmp_path / "google_ads.csv", dtype=str)
                         .iloc[-1]["Cost"].replace("MX$", "").replace(",", ""))
    assert abs(cleaned["meta"] - meta_total) < 1
    assert abs(cleaned["google"] - google_total) < 1


def test_pipeline_end_to_end_writes_reports_and_charts(tmp_path: Path):
    generate(tmp_path / "exports")
    reports = run(tmp_path / "exports", tmp_path / "out", ROOT / "sql")

    assert set(reports["01_kpis_by_platform"]["platform"]) == {"meta", "google", "tiktok"}
    assert reports["02_campaign_ranking"]["rank_in_campaign"].min() == 1
    for name in ["paid_media_unified.csv", "01_kpis_by_platform.csv",
                 "charts/cpa_by_platform.png", "charts/weekly_cpa.png"]:
        assert (tmp_path / "out" / name).stat().st_size > 0
