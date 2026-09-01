#!/usr/bin/env python3
"""Aggregate per-segment rubric/appeal coding into the two summary tables the
charts are built from.

Reads data/coded/<id>.json (one array of coded windows per pitch, matching
SEGMENT_CODING_SCHEMA in rubric_schema.py) plus data/corpus.json for each
pitch's duration and outcome, and writes:
  - data/segments_long.csv         one row per (pitch, segment, rubric_dim)
  - data/timeline_by_dimension.csv share of each rubric dimension, by decile of pitch runtime
  - data/appeal_by_dimension.csv   share of each dominant appeal, by rubric dimension
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CODED_DIR = ROOT / "data" / "coded"
CORPUS_PATH = ROOT / "data" / "corpus.json"
TRANSCRIPTS_DIR = ROOT / "data" / "transcripts"
OUT_DIR = ROOT / "data"

APPEALS = ["pathos", "logos", "ethos"]


def load_corpus() -> dict:
    return {p["id"]: p for p in json.loads(CORPUS_PATH.read_text(encoding="utf-8"))}


def load_rows() -> pd.DataFrame:
    corpus = load_corpus()
    rows = []
    for path in sorted(CODED_DIR.glob("*.json")):
        pid = path.stem
        meta = corpus.get(pid, {})
        transcript_path = TRANSCRIPTS_DIR / f"{pid}.json"
        duration_seconds = None
        if transcript_path.exists():
            duration_seconds = json.loads(transcript_path.read_text(encoding="utf-8")).get("duration_seconds")
        segments = json.loads(path.read_text(encoding="utf-8"))
        for seg in segments:
            pct = seg["start"] / duration_seconds if duration_seconds else None
            for dim in seg.get("rubric_dims", []):
                rows.append(
                    {
                        "pitch_id": pid,
                        "competition": meta.get("competition"),
                        "outcome_tier": meta.get("outcome_tier"),
                        "start_seconds": seg["start"],
                        "pct_of_pitch": pct,
                        "rubric_dim": dim,
                        "dominant_appeal": seg.get("dominant_appeal"),
                        "confidence": seg.get("confidence"),
                    }
                )
    return pd.DataFrame(rows)


def timeline_by_dimension(df: pd.DataFrame, bins: int = 12) -> pd.DataFrame:
    timed = df.dropna(subset=["pct_of_pitch"]).copy()
    timed["decile"] = (timed["pct_of_pitch"] * bins).clip(0, bins - 1).astype(int)
    counts = timed.groupby(["decile", "rubric_dim"]).size().unstack(fill_value=0)
    return counts.div(counts.sum(axis=1), axis=0).reindex(range(bins), fill_value=0)


def appeal_by_dimension(df: pd.DataFrame) -> pd.DataFrame:
    counts = df.groupby(["rubric_dim", "dominant_appeal"]).size().unstack(fill_value=0)
    return counts.div(counts.sum(axis=1), axis=0).reindex(columns=APPEALS, fill_value=0)


def main() -> None:
    df = load_rows()
    if df.empty:
        print("No coded segments found in data/coded/ yet — run the coding step first.")
        return

    df.to_csv(OUT_DIR / "segments_long.csv", index=False)
    timeline_by_dimension(df).to_csv(OUT_DIR / "timeline_by_dimension.csv")
    appeal_by_dimension(df).to_csv(OUT_DIR / "appeal_by_dimension.csv")
    print(f"Wrote {len(df)} coded rows -> segments_long.csv, timeline_by_dimension.csv, appeal_by_dimension.csv")


if __name__ == "__main__":
    main()
