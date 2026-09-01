#!/usr/bin/env python3
"""Turn a plain-text pitch script into the same transcript format
fetch_transcripts.py produces, so the rest of the pipeline (segment.py,
code_transcript.py, ...) runs on it completely unchanged — no video needed.

No real recording exists for a text-only pitch, so timing is estimated from
a reading pace (default 140 words/minute, a typical spoken-pitch pace). This
places moments proportionally through the pitch; it is not a claim about
actual delivery timing. Pass --wpm to match your own pace if you know it.

Usage:
    python3 src/text_to_transcript.py my_pitch.txt --id my_pitch_2026 --title "My Pitch"
    python3 src/text_to_transcript.py my_pitch.txt --id my_pitch_2026 --title "My Pitch" --wpm 150

Then run the rest of the pipeline exactly as for a video pitch, just skip
the fetch step (there's nothing to download):
    python3 src/pipeline.py my_pitch_2026 --mode scored --skip-fetch
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPTS_DIR = ROOT / "data" / "transcripts"


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def build_cues(text: str, wpm: float) -> list[dict]:
    """One cue per sentence, with start/end estimated from word count at the given pace."""
    t = 0.0
    cues = []
    for sentence in split_sentences(text):
        n_words = max(len(sentence.split()), 1)
        duration = (n_words / wpm) * 60.0
        cues.append({"start": round(t, 2), "end": round(t + duration, 2), "text": sentence})
        t += duration
    return cues


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("text_file", help="Plain-text file containing the pitch script (one pitch, plain prose)")
    parser.add_argument("--id", required=True, help='Pitch id — written as data/transcripts/<id>.json, must match the "id" you use in corpus.json')
    parser.add_argument("--title", required=True, help="Display title shown in the artifact")
    parser.add_argument("--competition", default="", help="Competition/context string shown in the artifact")
    parser.add_argument("--wpm", type=float, default=140.0, help="Assumed reading pace, words/minute (default 140)")
    args = parser.parse_args()

    text = Path(args.text_file).read_text(encoding="utf-8")
    cues = build_cues(text, args.wpm)
    if not cues:
        raise SystemExit(f"No sentences found in {args.text_file} — check the file has plain prose text.")

    record = {
        "id": args.id,
        "title": args.title,
        "youtube_url": None,
        "competition": args.competition,
        "duration_seconds": round(cues[-1]["end"], 1),
        "cues": cues,
        "timing_note": f"Estimated from a {args.wpm:.0f} wpm reading pace — no real recording exists for this pitch.",
    }

    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TRANSCRIPTS_DIR / f"{args.id}.json"
    out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"Wrote {out_path} ({len(cues)} cues, ~{record['duration_seconds']/60:.1f} min at {args.wpm:.0f} wpm)")


if __name__ == "__main__":
    main()
