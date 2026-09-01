#!/usr/bin/env python3
"""Static PNG renders of artifact_appeal_arc.html, from data/appeal_arc_data.json.

Same color language as charts.py and the published artifact:
  Pathos = orange, Logos = blue, Ethos = aqua
  Rubric dimensions (Airbnb only) = yellow / magenta / green / violet / red
"""
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "appeal_arc_data.json"
CHARTS_DIR = ROOT / "charts"

APPEAL_COLORS = {"pathos": "#eb6834", "logos": "#2a78d6", "ethos": "#1baf7a"}
DIM_COLORS = {
    "problem_fit": "#eda100",
    "tech": "#e87ba4",
    "impact_evidence": "#008300",
    "scale_sustainability": "#4a3aa7",
    "team": "#e34948",
}
DIM_LABELS = {
    "problem_fit": "Problem & Fit",
    "tech": "Tech",
    "impact_evidence": "Evidence of Impact",
    "scale_sustainability": "Scale & Sustainability",
    "team": "Team",
}
EMPTY = "#e1e0d9"


def fmt_time(s: float) -> str:
    s = max(0, round(s))
    return f"{s // 60}:{s % 60:02d}"


def render_intensity_chart(panel: dict, out_name: str) -> None:
    duration = panel["duration"]
    fig, ax = plt.subplots(figsize=(11, 3.2))
    for w in panel["windows"]:
        x0 = w["start"] / duration
        width = max((w["end"] - w["start"]) / duration, 0.0005)
        height = 0.1 + (w.get("intensity") or 0.3) * 0.85
        ax.add_patch(Rectangle((x0, 0), width, height, facecolor=APPEAL_COLORS[w["appeal"]], edgecolor="none"))
    for h in panel.get("highlights", []):
        ax.plot(h["start"] / duration, 1.03, marker="o", color=APPEAL_COLORS[h["appeal"]],
                markeredgecolor="white", markeredgewidth=1, markersize=7, clip_on=False)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.1)
    ticks = [0, 0.25, 0.5, 0.75, 1.0]
    ax.set_xticks(ticks)
    ax.set_xticklabels([fmt_time(t * duration) for t in ticks])
    ax.set_yticks([])
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.set_title(panel["label"] + "  ·  " + panel["outcome"], fontsize=11, loc="left")
    handles = [plt.Line2D([0], [0], color=c, lw=6, label=k.capitalize()) for k, c in APPEAL_COLORS.items()]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=3, frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / out_name, dpi=160)
    plt.close(fig)


def render_scored_strip(scored: dict, out_name: str) -> None:
    """Appeal band on top, five thinner rubric-dimension bands below it, per pitch —
    same time axis throughout, so a column always means the same window in every band."""
    n = len(scored)
    dims = list(DIM_COLORS)
    fig, axes = plt.subplots(n, 1, figsize=(11, 1.9 * n))
    if n == 1:
        axes = [axes]
    for ax, panel in zip(axes, scored.values()):
        duration = panel["duration"]
        for w in panel["windows"]:
            x0 = w["start"] / duration
            width = max((w["end"] - w["start"]) / duration, 0.0005)
            ax.add_patch(Rectangle((x0, 0.55), width, 0.45, facecolor=APPEAL_COLORS[w["appeal"]], edgecolor="white", linewidth=0.5))
            for i, dim in enumerate(dims):
                present = dim in w.get("rubric_dims", [])
                color = DIM_COLORS[dim] if present else EMPTY
                y0 = 0.5 - (i + 1) * 0.1
                ax.add_patch(Rectangle((x0, y0), width, 0.095, facecolor=color, edgecolor="white", linewidth=0.4))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_yticks([])
        ax.set_xticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_ylabel(panel["label"].split(" — ")[0], rotation=0, ha="right", va="center", fontsize=9)

    appeal_handles = [plt.Line2D([0], [0], color=c, lw=6, label=k.capitalize()) for k, c in APPEAL_COLORS.items()]
    dim_handles = [plt.Line2D([0], [0], color=c, lw=6, label=DIM_LABELS[k]) for k, c in DIM_COLORS.items()]
    appeal_legend = axes[0].legend(handles=appeal_handles, loc="lower left", bbox_to_anchor=(0, 1.2), ncol=3, frameon=False, fontsize=9, title="Appeal")
    axes[0].add_artist(appeal_legend)
    axes[0].legend(handles=dim_handles, loc="lower right", bbox_to_anchor=(1, 1.2), ncol=1, frameon=False, fontsize=8, title="Rubric dims")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / out_name, dpi=160)
    plt.close(fig)


def render_deck_matrix(deck: dict, out_name: str) -> None:
    slides = deck["slides"]
    n = len(slides)
    dims = list(DIM_COLORS)
    rows = ["Dominant appeal"] + [DIM_LABELS[d] for d in dims]

    fig, ax = plt.subplots(figsize=(11, 0.5 * len(rows) + 1.5))
    for col, s in enumerate(slides):
        ax.add_patch(Rectangle((col, len(rows) - 1), 1, 1, facecolor=APPEAL_COLORS[s["dominant_appeal"]], edgecolor="white"))
        for r, dim in enumerate(dims):
            present = dim in s["rubric_dims"]
            color = DIM_COLORS[dim] if present else EMPTY
            ax.add_patch(Rectangle((col, len(rows) - 2 - r), 1, 1, facecolor=color, edgecolor="white"))

    ax.set_xlim(0, n)
    ax.set_ylim(0, len(rows))
    ax.set_xticks([i + 0.5 for i in range(n)])
    ax.set_xticklabels([f"{i+1}. {s['slide']}" for i, s in enumerate(slides)], rotation=45, ha="right", fontsize=8)
    ax.set_yticks([len(rows) - 0.5 - i for i in range(len(rows))])
    ax.set_yticklabels(rows, fontsize=9)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title(deck["title"], fontsize=11, loc="left")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / out_name, dpi=160)
    plt.close(fig)


def main() -> None:
    CHARTS_DIR.mkdir(exist_ok=True)
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    for pid, panel in data["feature"].items():
        render_intensity_chart(panel, f"appeal_arc_{pid}.png")
    render_scored_strip(data["scored"], "appeal_arc_scored_strips.png")
    for deck_id, deck in data["decks"].items():
        render_deck_matrix(deck, f"appeal_arc_{deck_id}_matrix.png")

    print(f"Charts written to {CHARTS_DIR}")


if __name__ == "__main__":
    main()
