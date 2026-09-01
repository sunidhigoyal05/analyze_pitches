#!/usr/bin/env python3
"""Merge raw caption cues into ~45s windows, the unit the coding step reads.

Reads data/transcripts/<id>.json (written by fetch_transcripts.py) and writes
data/transcripts/<id>.segmented.json with a "windows" list added.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPTS_DIR = ROOT / "data" / "transcripts"
WINDOW_SECONDS = 45


def windows_for(cues: list[dict], window: float = WINDOW_SECONDS) -> list[dict]:
    if not cues:
        return []
    windows = []
    current = {"start": cues[0]["start"], "end": cues[0]["end"], "text": []}
    for cue in cues:
        if cue["start"] - current["start"] >= window and current["text"]:
            windows.append(current)
            current = {"start": cue["start"], "end": cue["end"], "text": []}
        current["end"] = cue["end"]
        current["text"].append(cue["text"])
    if current["text"]:
        windows.append(current)
    return [{"start": round(w["start"], 2), "end": round(w["end"], 2), "text": " ".join(w["text"])} for w in windows]


def segment_one(pid: str) -> int:
    src = TRANSCRIPTS_DIR / f"{pid}.json"
    record = json.loads(src.read_text(encoding="utf-8"))
    record["windows"] = windows_for(record["cues"])
    (TRANSCRIPTS_DIR / f"{pid}.segmented.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return len(record["windows"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", help="Only segment this pitch id")
    args = parser.parse_args()

    if args.id:
        ids = [args.id]
    else:
        ids = sorted(p.stem for p in TRANSCRIPTS_DIR.glob("*.json") if not p.stem.endswith(".segmented"))

    for pid in ids:
        try:
            n = segment_one(pid)
            print(f"[OK] {pid}: {n} windows")
        except FileNotFoundError:
            print(f"[SKIP] {pid}: no transcript found — run fetch_transcripts.py first")


if __name__ == "__main__":
    main()
