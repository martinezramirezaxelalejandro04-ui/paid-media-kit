import pandas as pd
import pytest

from paidmedia.normalize import campaign_key, clean_number, normalize, quality_issues


@pytest.mark.parametrize("raw, expected", [
    ("MX$1,234.50", 1234.5),
    ("$ 87", 87.0),
    ("12,000", 12000.0),
    ("--", 0.0),
    ("", 0.0),
    (None, 0.0),
    (float("nan"), 0.0),
    (45, 45.0),
])
def test_clean_number(raw, expected):
    assert clean_number(raw) == expected


def test_campaign_key_matches_across_platform_naming_styles():
    assert (
        campaign_key("Voluntarios Sept-Oct")
        == campaign_key("Voluntarios_Sept_Oct")
        == campaign_key("  voluntarios sept-oct ")
        == "voluntarios_sept_oct"
    )


def _meta_export(rows):
    columns = ["Day", "Campaign name", "Amount spent (MXN)", "Impressions", "Reach",
               "Link clicks", "Results"]
    return pd.DataFrame(rows, columns=columns, dtype=str)


def test_total_rows_and_blank_rows_are_dropped():
    raw = _meta_export([
        ["2026-09-01", "Voluntarios", "100.00", "1000", "800", "10", "1"],
        [None, "Total", "100.00", None, None, None, None],
        [None, None, None, None, None, None, None],
    ])
    assert len(normalize(raw, "meta")) == 1


def test_duplicated_rows_are_kept_once():
    row = ["2026-09-01", "Voluntarios", "100.00", "1000", "800", "10", "1"]
    clean = normalize(_meta_export([row, row]), "meta")
    assert len(clean) == 1
    assert clean.loc[0, "spend_mxn"] == 100.0


def test_each_platform_date_format_lands_on_the_same_day():
    meta = _meta_export([["2026-09-07", "A", "1", "1", "1", "1", "1"]])
    google = pd.DataFrame(
        [["Sep 7, 2026", "A", "MX$1.00", "1", "1", "1.00"]],
        columns=["Day", "Campaign", "Cost", "Impr.", "Clicks", "Conversions"], dtype=str,
    )
    tiktok = pd.DataFrame(
        [["07/09/2026", "A", "1.00", "1", "1", "1"]],
        columns=["By Day", "Campaign name", "Cost", "Impressions", "Clicks (destination)",
                 "Conversions"], dtype=str,
    )
    days = {normalize(frame, name).loc[0, "date"]
            for frame, name in [(meta, "meta"), (google, "google"), (tiktok, "tiktok")]}
    assert days == {pd.Timestamp("2026-09-07")}


def test_missing_column_is_reported_by_name():
    raw = _meta_export([["2026-09-01", "A", "1", "1", "1", "1", "1"]]).drop(columns="Results")
    with pytest.raises(ValueError, match="Results"):
        normalize(raw, "meta")


def test_unknown_platform_is_rejected():
    with pytest.raises(ValueError, match="Unknown platform"):
        normalize(pd.DataFrame(), "linkedin")


def test_quality_issues_flags_more_clicks_than_impressions():
    raw = _meta_export([["2026-09-01", "A", "10", "5", "5", "9", "0"]])
    assert quality_issues(normalize(raw, "meta")) == ["1 rows with more clicks than impressions"]
