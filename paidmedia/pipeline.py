"""Run the whole kit: raw exports in, clean table + KPI reports + charts out.

    python -m paidmedia.pipeline                      # uses data/sample
    python -m paidmedia.pipeline --input my_exports   # your own files

File names decide the platform: meta_*.csv, google_*.csv, tiktok_*.csv.
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

from . import charts
from .normalize import PLATFORMS, normalize, quality_issues

ROOT = Path(__file__).resolve().parent.parent


def detect_platform(filename: str) -> str:
    prefix = filename.lower().split("_")[0]
    if prefix not in PLATFORMS:
        raise ValueError(
            f"Cannot tell which platform '{filename}' comes from. "
            f"Rename it to start with one of: {', '.join(sorted(PLATFORMS))}_"
        )
    return prefix


def unify(input_dir: Path) -> pd.DataFrame:
    """Read every export in the folder and stack them in the unified schema."""
    frames = []
    for path in sorted(input_dir.glob("*.csv")):
        platform = detect_platform(path.name)
        raw = pd.read_csv(path, dtype=str)
        clean = normalize(raw, platform)
        print(f"  {path.name}: {len(raw)} raw rows -> {len(clean)} clean rows")
        frames.append(clean)
    if not frames:
        raise FileNotFoundError(f"No CSV exports found in {input_dir}")
    return pd.concat(frames, ignore_index=True)


def run_sql_reports(unified: pd.DataFrame, sql_dir: Path) -> dict[str, pd.DataFrame]:
    """Load the unified table into SQLite and run every .sql file against it."""
    reports = {}
    with sqlite3.connect(":memory:") as connection:
        unified.assign(date=unified["date"].dt.strftime("%Y-%m-%d")).to_sql(
            "ads", connection, index=False
        )
        for sql_file in sorted(sql_dir.glob("*.sql")):
            reports[sql_file.stem] = pd.read_sql_query(
                sql_file.read_text(encoding="utf-8"), connection
            )
    return reports


def run(input_dir: Path, output_dir: Path, sql_dir: Path) -> dict[str, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "charts").mkdir(exist_ok=True)

    print("1/3 Cleaning exports")
    unified = unify(input_dir)
    for issue in quality_issues(unified):
        print(f"  WARNING: {issue}")
    unified.to_csv(output_dir / "paid_media_unified.csv", index=False, date_format="%Y-%m-%d")

    print("2/3 Running SQL reports")
    reports = run_sql_reports(unified, sql_dir)
    for name, report in reports.items():
        report.to_csv(output_dir / f"{name}.csv", index=False)
        print(f"  {name}.csv ({len(report)} rows)")

    print("3/3 Drawing charts")
    charts.cpa_by_platform(reports["01_kpis_by_platform"],
                           output_dir / "charts" / "cpa_by_platform.png")
    charts.weekly_cpa(reports["03_weekly_trend"], output_dir / "charts" / "weekly_cpa.png")
    print(f"Done. Results in {output_dir}")
    return reports


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "sample")
    parser.add_argument("--output", type=Path, default=ROOT / "output")
    arguments = parser.parse_args()
    run(arguments.input, arguments.output, ROOT / "sql")


if __name__ == "__main__":
    main()
