#!/usr/bin/env python3
"""End-to-end pipeline for one video pitch: fetch -> segment -> code -> rebuild
the appeal-arc dataset -> inject it into the artifact -> render static charts.

Run this after adding an entry to data/corpus.json (see README.md for the
entry schema). Requires ANTHROPIC_API_KEY for the coding step.

Usage:
    python3 src/pipeline.py <pitch_id> --mode scored
    python3 src/pipeline.py <pitch_id> --mode exemplar
    python3 src/pipeline.py <pitch_id> --mode scored --skip-fetch   # captions already downloaded,
                                                                     # or built from plain text —
                                                                     # see src/text_to_transcript.py

Static decks (slides, no video) don't go through this pipeline — write their
JSON directly in data/exemplars/ following an existing deck's schema, add a
corpus.json entry with "medium": "deck", then just run:
    python3 src/build_appeal_arc_data.py && python3 src/inject_appeal_arc_data.py \\
      && python3 src/render_appeal_arc_charts.py
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"


def run(*args: str) -> None:
    print(f"$ {' '.join(args)}")
    subprocess.run(args, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pitch_id", help='Pitch id, matching an entry\'s "id" in data/corpus.json')
    parser.add_argument("--mode", choices=["scored", "exemplar"], required=True)
    parser.add_argument(
        "--skip-fetch", action="store_true",
        help="Skip re-downloading captions (reuse existing data/transcripts/<id>.json)",
    )
    args = parser.parse_args()

    python = sys.executable
    if not args.skip_fetch:
        run(python, str(SRC / "fetch_transcripts.py"), "--id", args.pitch_id)
    run(python, str(SRC / "segment.py"), "--id", args.pitch_id)
    run(python, str(SRC / "code_transcript.py"), args.pitch_id, "--mode", args.mode)
    run(python, str(SRC / "build_appeal_arc_data.py"))
    run(python, str(SRC / "inject_appeal_arc_data.py"))
    run(python, str(SRC / "render_appeal_arc_charts.py"))

    print(f"\nDone. Re-publish artifact_appeal_arc.html to see {args.pitch_id!r} live.")
    if args.mode == "scored":
        print("If this pitch should count toward the scored-corpus stats too, re-run src/aggregate.py.")


if __name__ == "__main__":
    main()
