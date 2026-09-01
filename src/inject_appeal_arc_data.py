#!/usr/bin/env python3
"""Splice data/appeal_arc_data.json into artifact_appeal_arc.html's `const DATA = ...` line.

Run this after build_appeal_arc_data.py whenever the underlying coding changes
and the published artifact needs to be regenerated from fresh data, then
republish artifact_appeal_arc.html.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "appeal_arc_data.json"
ARTIFACT_PATH = ROOT / "artifact_appeal_arc.html"
MARKER = "const DATA = "


def main() -> None:
    html = ARTIFACT_PATH.read_text(encoding="utf-8")
    data = DATA_PATH.read_text(encoding="utf-8")

    start = html.index(MARKER) + len(MARKER)
    end = html.index(";\n", start)
    new_html = html[:start] + data + html[end:]

    ARTIFACT_PATH.write_text(new_html, encoding="utf-8")
    print(f"Injected {DATA_PATH.name} ({len(data)} bytes) into {ARTIFACT_PATH.name}")


if __name__ == "__main__":
    main()
