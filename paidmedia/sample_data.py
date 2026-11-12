"""Generate SYNTHETIC exports that look like real Meta / Google / TikTok downloads.

Nothing here is real campaign data. The scenario is a fictional food bank
("Banco de Alimentos Ejemplo") recruiting volunteers and donors. The files are
deliberately messy (total rows, duplicates, currency symbols, blank lines,
inconsistent campaign names) so the cleaning step has real work to do.

    python -m paidmedia.sample_data
"""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

START, DAYS = date(2026, 9, 1), 61  # 1 Sep - 31 Oct 2026

# Daily budget in MXN for each campaign.
CAMPAIGNS = {
    "Voluntarios Sept-Oct": 450,
    "Donativos Recurrentes": 700,
    "Colecta Dia Mundial de la Alimentacion": 300,
}
# Per platform: cost per 1000 impressions, click rate, conversion rate.
PLATFORM_PROFILE = {
    "meta": {"cpm": 38.0, "ctr": 0.012, "cvr": 0.045},
    "google": {"cpm": 95.0, "ctr": 0.034, "cvr": 0.060},
    "tiktok": {"cpm": 22.0, "ctr": 0.008, "cvr": 0.018},
}
# The same campaign is written differently on each platform, as happens in real accounts.
NAME_STYLE = {
    "meta": lambda name: name,
    "google": lambda name: name.replace(" ", "_").replace("-", "_"),
    "tiktok": lambda name: f" {name.lower()} ",
}
ENGLISH_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
COLLECTION_START, COLLECTION_END = date(2026, 10, 5), date(2026, 10, 20)


def _daily_rows(platform: str, rng: random.Random) -> list[dict]:
    profile = PLATFORM_PROFILE[platform]
    rows = []
    for campaign, budget in CAMPAIGNS.items():
        for offset in range(DAYS):
            day = START + timedelta(days=offset)
            # The World Food Day collection only runs 5-20 October.
            if "Colecta" in campaign and not (COLLECTION_START <= day <= COLLECTION_END):
                continue
            weekend_boost = 1.15 if day.weekday() >= 5 else 1.0
            spend = budget * rng.uniform(0.8, 1.1)
            impressions = int(spend / profile["cpm"] * 1000 * rng.uniform(0.85, 1.15))
            clicks = int(impressions * profile["ctr"] * weekend_boost * rng.uniform(0.8, 1.2))
            conversions = int(clicks * profile["cvr"] * rng.uniform(0.6, 1.4))
            rows.append({"day": day, "campaign": campaign, "spend": spend,
                         "impressions": impressions, "clicks": clicks,
                         "conversions": conversions})
    return rows


def _write(path: Path, header: list[str], rows: list[list]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def generate(folder: Path, seed: int = 42) -> None:
    rng = random.Random(seed)
    folder.mkdir(parents=True, exist_ok=True)

    # --- Meta: ISO dates, plain numbers, a duplicated block and a total row ---
    data = _daily_rows("meta", rng)
    rows = [[r["day"].isoformat(), NAME_STYLE["meta"](r["campaign"]), f"{r['spend']:.2f}",
             r["impressions"], int(r["impressions"] * 0.82), r["clicks"], r["conversions"]]
            for r in data]
    rows += rows[10:15]  # an export pasted twice
    rows.append(["", "Total", f"{sum(r['spend'] for r in data):.2f}", "", "", "", ""])
    _write(folder / "meta_ads.csv",
           ["Day", "Campaign name", "Amount spent (MXN)", "Impressions", "Reach",
            "Link clicks", "Results"], rows)

    # --- Google: 'Sep 7, 2026' dates, 'MX$1,234.50' costs, '--' for no data ---
    data = _daily_rows("google", rng)
    rows = []
    for r in data:
        day = f"{ENGLISH_MONTHS[r['day'].month - 1]} {r['day'].day}, {r['day'].year}"
        conversions = "--" if r["conversions"] == 0 else f"{r['conversions']:.2f}"
        rows.append([day, NAME_STYLE["google"](r["campaign"]), "MXN", f"MX${r['spend']:,.2f}",
                     f"{r['impressions']:,}", f"{r['clicks']:,}", conversions])
    total_cost = sum(r["spend"] for r in data)
    rows.append(["Total: Account", "", "MXN", f"MX${total_cost:,.2f}", "", "", ""])
    _write(folder / "google_ads.csv",
           ["Day", "Campaign", "Currency code", "Cost", "Impr.", "Clicks", "Conversions"], rows)

    # --- TikTok: day/month/year dates, padded lowercase names, blank lines ---
    data = _daily_rows("tiktok", rng)
    rows = [[r["day"].strftime("%d/%m/%Y"), NAME_STYLE["tiktok"](r["campaign"]),
             f"{r['spend']:.2f}", r["impressions"], r["clicks"], r["conversions"]]
            for r in data]
    rows.insert(20, ["", "", "", "", "", ""])
    rows.insert(75, ["", "", "", "", "", ""])
    _write(folder / "tiktok_ads.csv",
           ["By Day", "Campaign name", "Cost", "Impressions", "Clicks (destination)",
            "Conversions"], rows)


if __name__ == "__main__":
    target = Path(__file__).resolve().parent.parent / "data" / "sample"
    generate(target)
    print(f"Synthetic exports written to {target}")
