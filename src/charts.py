#!/usr/bin/env python3
"""Render static charts from the aggregated coding in data/*.csv (aggregate.py).

Uses the same Pathos/Logos/Ethos colors as artifact_framework.html so the
static charts and the published diagram read as one system.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CHARTS_DIR = ROOT / "charts"

COLORS = {"pathos": "#eb6834", "logos": "#2a78d6", "ethos": "#1baf7a"}
APPEAL_ORDER = ["pathos", "logos", "ethos"]


def appeal_by_dimension_chart() -> None:
    path = DATA_DIR / "appeal_by_dimension.csv"
    if not path.exists():
        return
    df = pd.read_csv(path, index_col=0)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bottom = None
    for appeal in APPEAL_ORDER:
        if appeal not in df.columns:
            continue
        ax.bar(df.index, df[appeal], bottom=bottom, label=appeal.capitalize(), color=COLORS[appeal])
        bottom = df[appeal] if bottom is None else bottom + df[appeal]

    ax.set_ylabel("Share of coded segments")
    ax.set_title("Rhetorical appeal by rubric dimension — real coded pitches")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=3, frameon=False)
    fig.autofmt_xdate(rotation=20)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "appeal_by_dimension.png", dpi=160)
    plt.close(fig)


def timeline_heatmap() -> None:
    path = DATA_DIR / "timeline_by_dimension.csv"
    if not path.exists():
        return
    df = pd.read_csv(path, index_col=0)

    fig, ax = plt.subplots(figsize=(9, 4))
    im = ax.imshow(df.T.values, aspect="auto", cmap="Blues", vmin=0)
    ax.set_yticks(range(len(df.columns)))
    ax.set_yticklabels(df.columns)
    n = len(df.index)
    ax.set_xticks(range(n))
    ax.set_xticklabels([f"{round(i / n * 12, 1)}m" for i in df.index])
    ax.set_title("Rubric dimension coverage across pitch runtime — real coded pitches")
    fig.colorbar(im, ax=ax, label="Share of segments")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "timeline_heatmap.png", dpi=160)
    plt.close(fig)


def main() -> None:
    CHARTS_DIR.mkdir(exist_ok=True)
    appeal_by_dimension_chart()
    timeline_heatmap()
    print(f"Charts written to {CHARTS_DIR}")


if __name__ == "__main__":
    main()
