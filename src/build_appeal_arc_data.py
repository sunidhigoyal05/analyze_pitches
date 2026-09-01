#!/usr/bin/env python3
"""Build the combined dataset behind artifact_appeal_arc.html.

Fully driven by data/corpus.json — add a pitch there (see README.md) and it
flows into the artifact automatically, no code edits needed. Reads:
  - "scored"   entries -> data/coded/<id>.json + data/transcripts/<id>*.json
  - "exemplar" + medium "video"/"text" entries -> data/coded_exemplars/<id>.json +
    data/exemplars/<id>.json (highlights) + data/transcripts/<id>*.json
  - "exemplar" + medium "deck"  entries -> data/exemplars/<id>.json as-is
  - "excluded" entries are skipped

Writes data/appeal_arc_data.json — the exact blob embedded (minified) into
artifact_appeal_arc.html's `const DATA = ...` line. Re-run this after
re-coding any source, then run inject_appeal_arc_data.py to update the
artifact file, then render_appeal_arc_charts.py for the static PNGs.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPTS_DIR = ROOT / "data" / "transcripts"
CODED_DIR = ROOT / "data" / "coded"
CODED_EXEMPLARS_DIR = ROOT / "data" / "coded_exemplars"
EXEMPLARS_DIR = ROOT / "data" / "exemplars"
CORPUS_PATH = ROOT / "data" / "corpus.json"
OUT_PATH = ROOT / "data" / "appeal_arc_data.json"

SNIPPET_LEN = 110


def dedup_repeat(text: str) -> str:
    """Collapse the immediate repeated-phrase runs from YouTube rolling captions."""
    return re.sub(r"\b(.{12,}?)\s+\1\b", r"\1", text, flags=re.IGNORECASE)


def fix_caps(text: str) -> str:
    """Sentence-case any ALL-CAPS words from news-style caption emphasis, keeping 'I'."""
    def fix_word(m: re.Match) -> str:
        w = m.group(0)
        if w == "I":
            return w
        if len(w) >= 2 and w.isupper():
            return w.capitalize()
        return w
    return re.sub(r"[A-Za-z']+", fix_word, text)


def snippet(text: str, n: int = SNIPPET_LEN) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = dedup_repeat(dedup_repeat(text))
    text = re.sub(r"&gt;&gt;\s*", "", text).strip()
    text = fix_caps(text)
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + "…"


def build_feature_panel(entry: dict) -> dict:
    """Dense intensity timeline + highlight quotes for a video exemplar (non-pitch control case).

    Requires data/coded_exemplars/<id>.json (dense, per-window intensity coding
    — see code_transcript.py --mode exemplar), not just the sparse highlights
    file in data/exemplars/. Raises FileNotFoundError if that's missing, caught
    by the caller so one under-coded exemplar doesn't break the whole build.
    """
    pid = entry["id"]
    coded = json.loads((CODED_EXEMPLARS_DIR / f"{pid}.json").read_text(encoding="utf-8"))
    seg = json.loads((TRANSCRIPTS_DIR / f"{pid}.segmented.json").read_text(encoding="utf-8"))["windows"]
    ex = json.loads((EXEMPLARS_DIR / f"{pid}.json").read_text(encoding="utf-8"))

    windows = [
        {
            "start": round(c["start"], 1),
            "end": round(c["end"], 1),
            "appeal": c["dominant_appeal"],
            "intensity": c["intensity"],
            "text": snippet(w["text"]),
        }
        for c, w in zip(coded, seg)
    ]
    highlights = [{**h, "quote": fix_caps(h["quote"])} for h in ex["highlights"]]

    return {
        "label": entry["title"],
        "outcome": entry.get("outcome_detail") or "Exemplar, not a pitch",
        "duration": coded[-1]["end"],
        "appeal_share": ex["appeal_share"],
        "windows": windows,
        "highlights": highlights,
    }


def build_scored_panel(entry: dict) -> dict:
    """Appeal strip + rubric-dimension coverage rows for a real, judged, coded pitch."""
    pid = entry["id"]
    coded = json.loads((CODED_DIR / f"{pid}.json").read_text(encoding="utf-8"))
    transcript = json.loads((TRANSCRIPTS_DIR / f"{pid}.json").read_text(encoding="utf-8"))
    seg = json.loads((TRANSCRIPTS_DIR / f"{pid}.segmented.json").read_text(encoding="utf-8"))["windows"]

    windows = []
    counts: dict[str, int] = {}
    for c, w in zip(coded, seg):
        windows.append({
            "start": round(c["start"], 1),
            "end": round(c["end"], 1),
            "appeal": c["dominant_appeal"],
            "rubric_dims": c.get("rubric_dims", []),
            "text": snippet(w["text"]),
        })
        counts[c["dominant_appeal"]] = counts.get(c["dominant_appeal"], 0) + 1
    total = sum(counts.values())
    appeal_share = {k: round(v / total, 3) for k, v in counts.items()}

    return {
        "label": entry["title"],
        "outcome": entry.get("outcome_detail") or entry.get("outcome_tier") or "",
        "duration": transcript["duration_seconds"],
        "appeal_share": appeal_share,
        "windows": windows,
    }


def main() -> None:
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))

    feature = {}
    scored = {}
    decks = {}

    for entry in corpus:
        category = entry.get("category")
        medium = entry.get("medium")
        pid = entry["id"]

        if category == "excluded":
            continue
        elif category == "scored":
            scored[pid] = build_scored_panel(entry)
        elif category == "exemplar" and medium in ("video", "text"):
            try:
                feature[pid] = build_feature_panel(entry)
            except FileNotFoundError:
                print(
                    f"SKIPPING {pid!r}: no dense per-window coding at "
                    f"data/coded_exemplars/{pid}.json — run "
                    f"`python3 src/code_transcript.py {pid} --mode exemplar` first."
                )
        elif category == "exemplar" and medium == "deck":
            decks[pid] = json.loads((EXEMPLARS_DIR / f"{pid}.json").read_text(encoding="utf-8"))
        else:
            print(f"WARNING: skipping {pid!r} — unrecognized category/medium ({category!r}/{medium!r})")

    combined = {"feature": feature, "scored": scored, "decks": decks}
    OUT_PATH.write_text(json.dumps(combined, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    print(
        f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size} bytes): "
        f"{len(feature)} video exemplars, {len(scored)} scored pitches, {len(decks)} decks"
    )


if __name__ == "__main__":
    main()
