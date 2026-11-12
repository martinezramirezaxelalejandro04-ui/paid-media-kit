"""Charts for the README, drawn in one consistent, colour-blind-safe style.

Chart text is in Spanish because the kit is made for organisations in Mexico.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # render to files, no window needed
import matplotlib.pyplot as plt
import pandas as pd

SURFACE, INK, INK_SECONDARY, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"

# Colour follows the platform, in every chart, whatever its rank.
PLATFORM_COLOR = {"meta": "#2a78d6", "google": "#eb6834", "tiktok": "#1baf7a"}
PLATFORM_LABEL = {"meta": "Meta Ads", "google": "Google Ads", "tiktok": "TikTok Ads"}


def _base_axes(title: str, subtitle: str, figsize=(8, 4.2)):
    fig, ax = plt.subplots(figsize=figsize, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    fig.text(0.02, 0.95, title, fontsize=13, fontweight="bold", color=INK, va="top")
    fig.text(0.02, 0.88, subtitle, fontsize=9.5, color=INK_SECONDARY, va="top")
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    return fig, ax


def cpa_by_platform(kpis: pd.DataFrame, path: Path) -> None:
    """Horizontal bars: cost per conversion for each platform, cheapest on top."""
    data = kpis.sort_values("cpa_mxn", ascending=False)
    fig, ax = _base_axes(
        "Costo por conversión según la plataforma",
        "Pesos gastados por cada registro o donativo. Menos es mejor. Datos sintéticos de ejemplo.",
        figsize=(8, 3.4),
    )
    labels = [PLATFORM_LABEL[p] for p in data["platform"]]
    bars = ax.barh(labels, data["cpa_mxn"], height=0.5,
                   color=[PLATFORM_COLOR[p] for p in data["platform"]])
    for bar, value in zip(bars, data["cpa_mxn"]):
        ax.text(bar.get_width() + data["cpa_mxn"].max() * 0.015,
                bar.get_y() + bar.get_height() / 2,
                f"${value:,.0f}", va="center", fontsize=10, color=INK)
    ax.set_xlim(0, data["cpa_mxn"].max() * 1.15)
    ax.xaxis.set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="y", labelsize=10, labelcolor=INK_SECONDARY)
    fig.subplots_adjust(left=0.16, right=0.97, top=0.76, bottom=0.06)
    fig.savefig(path, dpi=160, facecolor=SURFACE)
    plt.close(fig)


def weekly_cpa(weekly: pd.DataFrame, path: Path) -> None:
    """Lines: weekly cost per conversion, one line per platform."""
    fig, ax = _base_axes(
        "Costo por conversión, semana a semana",
        "Pesos por conversión, solo semanas completas (inician en lunes). "
        "Datos sintéticos de ejemplo.",
    )
    weekly = weekly.assign(week_start=pd.to_datetime(weekly["week_start"]))
    for platform, group in weekly.groupby("platform"):
        group = group.sort_values("week_start")
        ax.plot(group["week_start"], group["cpa_mxn"], color=PLATFORM_COLOR[platform],
                linewidth=2, marker="o", markersize=6, markeredgecolor=SURFACE,
                markeredgewidth=1.5, label=PLATFORM_LABEL[platform])
        last = group.iloc[-1]
        ax.annotate(f"  {PLATFORM_LABEL[platform]}  ${last['cpa_mxn']:,.0f}",
                    (last["week_start"], last["cpa_mxn"]),
                    va="center", fontsize=9, color=INK_SECONDARY)
    ax.set_ylim(0, weekly["cpa_mxn"].max() * 1.15)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(lambda value, _: f"${value:,.0f}")
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b"))
    ax.legend(loc="upper left", bbox_to_anchor=(0, 1.02), ncol=3, frameon=False,
              fontsize=9, labelcolor=INK_SECONDARY, handlelength=1.4)
    fig.subplots_adjust(left=0.08, right=0.80, top=0.74, bottom=0.10)
    fig.savefig(path, dpi=160, facecolor=SURFACE)
    plt.close(fig)
