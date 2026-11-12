"""Turn raw ad-platform exports (Meta, Google, TikTok) into one tidy table.

Every platform names its columns differently, formats dates differently and
sprinkles the file with currency symbols, thousands separators, total rows and
duplicates. This module hides all of that behind a single function:

    unified = normalize(raw_dataframe, platform="meta")
"""
from __future__ import annotations

import re

import pandas as pd

UNIFIED_COLUMNS = [
    "date", "platform", "campaign", "campaign_key",
    "spend_mxn", "impressions", "clicks", "conversions",
]
METRICS = ["spend_mxn", "impressions", "clicks", "conversions"]

# How each platform names the things we care about, and how it writes dates.
PLATFORMS: dict[str, dict] = {
    "meta": {
        "columns": {
            "Day": "date",
            "Campaign name": "campaign",
            "Amount spent (MXN)": "spend_mxn",
            "Impressions": "impressions",
            "Link clicks": "clicks",
            "Results": "conversions",
        },
        "date_format": "%Y-%m-%d",
    },
    "google": {
        "columns": {
            "Day": "date",
            "Campaign": "campaign",
            "Cost": "spend_mxn",
            "Impr.": "impressions",
            "Clicks": "clicks",
            "Conversions": "conversions",
        },
        "date_format": "%b %d, %Y",
    },
    "tiktok": {
        "columns": {
            "By Day": "date",
            "Campaign name": "campaign",
            "Cost": "spend_mxn",
            "Impressions": "impressions",
            "Clicks (destination)": "clicks",
            "Conversions": "conversions",
        },
        "date_format": "%d/%m/%Y",
    },
}


def clean_number(value) -> float:
    """'MX$1,234.50' -> 1234.5 ; '--' or '' -> 0.0 ; 87 -> 87.0"""
    if value is None or (isinstance(value, float) and pd.isna(value)) or value is pd.NA:
        return 0.0
    text = re.sub(r"[^0-9.\-]", "", str(value))
    if text in ("", "-", "--", "."):
        return 0.0
    return float(text)


def campaign_key(name: str) -> str:
    """'  Voluntarios - Sept ' and 'voluntarios_sept' become the same key."""
    key = re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower())
    return key.strip("_")


def normalize(raw: pd.DataFrame, platform: str) -> pd.DataFrame:
    """Return the export in the unified schema, cleaned and de-duplicated."""
    if platform not in PLATFORMS:
        raise ValueError(f"Unknown platform '{platform}'. Use one of {sorted(PLATFORMS)}.")
    spec = PLATFORMS[platform]

    missing = [col for col in spec["columns"] if col not in raw.columns]
    if missing:
        raise ValueError(f"The {platform} export is missing columns: {missing}")

    df = raw[list(spec["columns"])].rename(columns=spec["columns"]).copy()

    # Total/summary rows and blank lines have no parseable date: drop them.
    df["date"] = pd.to_datetime(
        df["date"].astype("string").str.strip(), format=spec["date_format"], errors="coerce"
    )
    df = df[df["date"].notna()]

    df["campaign"] = (
        df["campaign"].astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    )
    df = df[df["campaign"].notna() & (df["campaign"] != "")]
    df["campaign_key"] = df["campaign"].map(campaign_key)

    for metric in METRICS:
        df[metric] = df[metric].map(clean_number).astype("float64")
    for metric in ("impressions", "clicks"):
        df[metric] = df[metric].round().astype("int64")

    df["platform"] = platform
    df = df.drop_duplicates(subset=["date", "campaign_key"], keep="first")
    return df[UNIFIED_COLUMNS].sort_values(["date", "campaign_key"]).reset_index(drop=True)


def quality_issues(df: pd.DataFrame) -> list[str]:
    """Plain-language list of things an analyst should look at before trusting the data."""
    issues = []
    for metric in METRICS:
        negatives = int((df[metric] < 0).sum())
        if negatives:
            issues.append(f"{negatives} rows with negative {metric}")
    impossible = int((df["clicks"] > df["impressions"]).sum())
    if impossible:
        issues.append(f"{impossible} rows with more clicks than impressions")
    free_conversions = int(((df["conversions"] > 0) & (df["spend_mxn"] == 0)).sum())
    if free_conversions:
        issues.append(f"{free_conversions} rows with conversions but zero spend")
    return issues
