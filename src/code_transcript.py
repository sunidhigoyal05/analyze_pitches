#!/usr/bin/env python3
"""Code a segmented transcript against the rubric + rhetorical-appeal schema, via the Claude API.

This is the scriptable equivalent of the manual coding pass this project was
originally built with (dispatching Claude Code agents by hand) — lets anyone
with an ANTHROPIC_API_KEY add and code their own pitch, without an AI coding
assistant driving each step.

Requires: pip install anthropic pydantic
Requires: ANTHROPIC_API_KEY set (or another credential source the SDK
resolves — see `ant auth status` if you have the Anthropic CLI installed).

Usage:
    python3 src/code_transcript.py <pitch_id> --mode scored     # judged pitch: rubric_dims + appeal
    python3 src/code_transcript.py <pitch_id> --mode exemplar   # non-pitch control case: appeal + intensity

Run fetch_transcripts.py and segment.py first — this reads
data/transcripts/<pitch_id>.segmented.json.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from rubric_schema import RHETORICAL_APPEALS, RUBRIC_DIMENSIONS

ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPTS_DIR = ROOT / "data" / "transcripts"
CODED_DIR = ROOT / "data" / "coded"
CODED_EXEMPLARS_DIR = ROOT / "data" / "coded_exemplars"

MODEL = "claude-opus-5"

# Keep these two literals in sync with the keys in rubric_schema.py.
RubricDim = Literal["problem_fit", "tech", "impact_evidence", "scale_sustainability", "team"]
Appeal = Literal["pathos", "logos", "ethos"]


class ScoredWindow(BaseModel):
    start: float
    end: float
    rubric_dims: list[RubricDim] = Field(
        description="Zero or more rubric dimensions substantively addressed in this window; "
        "empty for filler/transition/logistics text."
    )
    dominant_appeal: Appeal
    confidence: float = Field(ge=0, le=1)


class ScoredCoding(BaseModel):
    windows: list[ScoredWindow]


class ExemplarWindow(BaseModel):
    start: float
    end: float
    dominant_appeal: Appeal
    intensity: float = Field(
        ge=0, le=1,
        description="Rhetorical intensity of the dominant appeal in this window — not labeling "
        "confidence. A plain transitional sentence is low intensity even if clearly one appeal; "
        "a vivid image or refrain is high.",
    )
    confidence: float = Field(ge=0, le=1)


class ExemplarCoding(BaseModel):
    windows: list[ExemplarWindow]


SCORED_PROMPT = """You are coding a real pitch transcript for a research project studying how a 5-part judging rubric maps onto the classical rhetorical appeals (Ethos, Logos, Pathos) across a pitch.

Rubric dimensions:
{rubric_defs}

Rhetorical appeals:
{appeal_defs}

For EVERY window below (there are {n} windows, in order), decide:
- rubric_dims: which dimension keys are substantively addressed in this window's text — can be empty, one, or multiple. Don't force a dimension onto filler/transition/Q&A-logistics text.
- dominant_appeal: the single most prominent appeal in this window's language.
- confidence: 0-1, your confidence in this window's coding.

This is a real, unscripted human pitch transcript — it will include filler words, false starts, and Q&A exchanges. Code it honestly based on what's actually said, not an idealized structure.

Output exactly {n} entries, one per window, in the same order, with the same start/end values as given below.

Windows:
{windows_json}"""

EXEMPLAR_PROMPT = """You are coding a real speech/keynote transcript for a research project studying the classical rhetorical appeals (Ethos, Logos, Pathos) — used as a non-pitch control case, not scored against any rubric.

Rhetorical appeals:
{appeal_defs}

For EVERY window below (there are {n} windows, in order), decide:
- dominant_appeal: the single most prominent appeal in this window's language.
- intensity: 0-1, how strongly/vividly that appeal is expressed.
- confidence: 0-1, your confidence in this window's coding.

Output exactly {n} entries, one per window, in the same order, with the same start/end values as given below.

Windows:
{windows_json}"""


def format_defs(defs: dict) -> str:
    return "\n".join(f"- {k}: {v}" for k, v in defs.items())


def code_transcript(pitch_id: str, mode: str) -> None:
    seg_path = TRANSCRIPTS_DIR / f"{pitch_id}.segmented.json"
    if not seg_path.exists():
        sys.exit(f"{seg_path} not found — run fetch_transcripts.py and segment.py first.")
    record = json.loads(seg_path.read_text(encoding="utf-8"))
    windows = record["windows"]
    windows_input = [{"start": w["start"], "end": w["end"], "text": w["text"]} for w in windows]

    import anthropic  # deferred: only needed once we're actually calling the API
    client = anthropic.Anthropic()

    if mode == "scored":
        prompt = SCORED_PROMPT.format(
            rubric_defs=format_defs(RUBRIC_DIMENSIONS),
            appeal_defs=format_defs(RHETORICAL_APPEALS),
            n=len(windows_input),
            windows_json=json.dumps(windows_input, indent=1),
        )
        output_model = ScoredCoding
        out_path = CODED_DIR / f"{pitch_id}.json"
    else:
        prompt = EXEMPLAR_PROMPT.format(
            appeal_defs=format_defs(RHETORICAL_APPEALS),
            n=len(windows_input),
            windows_json=json.dumps(windows_input, indent=1),
        )
        output_model = ExemplarCoding
        out_path = CODED_EXEMPLARS_DIR / f"{pitch_id}.json"

    print(f"Coding {len(windows_input)} windows for {pitch_id!r} (mode={mode}) via {MODEL}...")
    response = client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
        output_format=output_model,
    )
    coding = response.parsed_output

    if len(coding.windows) != len(windows_input):
        sys.exit(
            f"Model returned {len(coding.windows)} windows, expected {len(windows_input)} — "
            "not writing output. Structured output occasionally drops/merges entries on very "
            "long transcripts; just try again."
        )

    payload = []
    for w in coding.windows:
        entry = w.model_dump()
        entry["start"] = round(entry["start"], 2)
        entry["end"] = round(entry["end"], 2)
        payload.append(entry)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out_path} ({len(payload)} windows)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "pitch_id",
        help='Pitch id — must have a data/transcripts/<id>.segmented.json (run fetch_transcripts.py + segment.py first)',
    )
    parser.add_argument(
        "--mode",
        choices=["scored", "exemplar"],
        required=True,
        help="'scored' for a judged pitch (rubric_dims + appeal); "
        "'exemplar' for a non-pitch control case (appeal + intensity)",
    )
    args = parser.parse_args()
    code_transcript(args.pitch_id, args.mode)


if __name__ == "__main__":
    main()
