#!/usr/bin/env python3
"""Fetch YouTube captions for every pitch listed in data/corpus.json.

Pulls existing captions (manual, falling back to auto-generated) via yt-dlp —
no video/audio download, no Whisper. Whisper transcription is a separate
fallback for entries that come back with no captions at all (rare for public
competition/interview uploads, but possible).
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yt_dlp

ROOT = Path(__file__).resolve().parent.parent
CORPUS_PATH = ROOT / "data" / "corpus.json"
TRANSCRIPTS_DIR = ROOT / "data" / "transcripts"

TIMESTAMP_RE = re.compile(r"(\d\d:\d\d:\d\d\.\d\d\d) --> (\d\d:\d\d:\d\d\.\d\d\d)")


def ts_to_seconds(ts: str) -> float:
    h, m, s = ts.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def parse_vtt(text: str) -> list[dict]:
    """Parse a WebVTT file into {start, end, text} cues.

    YouTube auto-captions render as a rolling window (each cue repeats most of
    the previous cue's words), so consecutive cues with identical text are
    collapsed into one, extending the end time.
    """
    cues = []
    for block in text.split("\n\n"):
        lines = [l for l in block.splitlines() if l.strip()]
        if not lines:
            continue
        idx = 1 if TIMESTAMP_RE.search(lines[0]) is None and len(lines) > 1 else 0
        if idx >= len(lines):
            continue
        m = TIMESTAMP_RE.search(lines[idx])
        if not m:
            continue
        start, end = ts_to_seconds(m.group(1)), ts_to_seconds(m.group(2))
        cleaned = re.sub(r"<[^>]+>", "", " ".join(lines[idx + 1:])).strip()
        if cleaned:
            cues.append({"start": start, "end": end, "text": cleaned})

    deduped: list[dict] = []
    for c in cues:
        if deduped and deduped[-1]["text"] == c["text"]:
            deduped[-1]["end"] = c["end"]
        else:
            deduped.append(c)
    return deduped


def clip_cues(cues: list[dict], clip_start: float | None, clip_end: float | None) -> list[dict]:
    """Restrict cues to a clip range, for corpus entries that point at one
    pitch inside a longer multi-pitch demo-day video."""
    if clip_start is None and clip_end is None:
        return cues
    lo = clip_start or 0
    hi = clip_end if clip_end is not None else float("inf")
    out = []
    for c in cues:
        if c["end"] < lo or c["start"] > hi:
            continue
        out.append({"start": round(c["start"] - lo, 2), "end": round(c["end"] - lo, 2), "text": c["text"]})
    return out


def fetch_one(pitch: dict, out_dir: Path, lang: str = "en") -> tuple[bool, str]:
    pid = pitch["id"]
    url = pitch["youtube_url"]
    outtmpl = str(out_dir / f"{pid}.%(ext)s")
    ydl_opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": [lang, f"{lang}-orig"],
        "subtitlesformat": "vtt",
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as exc:  # yt_dlp raises its own DownloadError subclasses
        return False, f"download failed: {exc}"

    candidates = sorted(out_dir.glob(f"{pid}.{lang}*.vtt"))
    if not candidates:
        return False, "no captions found"

    cues = parse_vtt(candidates[0].read_text(encoding="utf-8"))
    for f in candidates:
        f.unlink()

    cues = clip_cues(cues, pitch.get("clip_start_seconds"), pitch.get("clip_end_seconds"))

    record = {
        "id": pid,
        "title": pitch.get("title"),
        "youtube_url": url,
        "competition": pitch.get("competition"),
        "duration_seconds": round(cues[-1]["end"], 1) if cues else None,
        "cues": cues,
    }
    (out_dir / f"{pid}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return True, f"{len(cues)} cues"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", help="Only fetch this pitch id")
    args = parser.parse_args()

    if not CORPUS_PATH.exists():
        sys.exit(f"{CORPUS_PATH} does not exist yet — populate the corpus first.")
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    targets = [p for p in corpus if not args.id or p["id"] == args.id]
    if not targets:
        sys.exit(f"No pitch with id {args.id!r} in {CORPUS_PATH}")

    for pitch in targets:
        ok, msg = fetch_one(pitch, TRANSCRIPTS_DIR)
        print(f"[{'OK' if ok else 'MISSING'}] {pitch['id']}: {msg}")


if __name__ == "__main__":
    main()
