# The Pitch Score / The Appeal Arc

Studies how a 5-part pitch rubric (Problem & Fit, Tech, Evidence of Impact,
Scale & Sustainability, Team) maps onto the classical rhetorical appeals
(Pathos, Logos, Ethos) — using real judged pitches, four historical VC decks,
and two non-pitch speeches (MLK, Steve Jobs) as a contrast case.

- `artifact_framework.html` — the hypothesis (illustrative, no data dependency)
- `artifact_appeal_arc.html` — the real coding, charted

## How to use this

**Just want to read the results?** Both pages are self-contained HTML — open
the file directly in a browser (double-click it, or `open artifact_appeal_arc.html`
on macOS), no server or build step needed. Or view the currently-published
versions:
- [The Pitch Score](https://claude.ai/code/artifact/93b8d485-a3c9-47dd-b5df-80b53deee08c) — the rubric-to-appeal hypothesis, plain-English summary up top
- [The Appeal Arc](https://claude.ai/code/artifact/36d099d3-4c36-47f2-9394-862c98d3b7a1) — real judged pitches, four VC decks, and MLK/Jobs as contrast, each with a one-line takeaway under the chart

Each chart is hoverable for the exact transcript/slide text behind a given
color; every panel also has a "View as table" toggle if you want the raw
coded rows without interacting with the chart. Every real judged pitch
(and every deck) shows two things stacked: which appeal (Pathos/Logos/Ethos)
dominates each moment, and — right below it, on the same time axis — five
thinner rows showing exactly where each rubric dimension (Problem & Fit,
Tech, Evidence of Impact, Scale & Sustainability, Team) gets addressed.

**The raw numbers instead of the charts** `data/segments_long.csv`,
`data/timeline_by_dimension.csv`, and `data/appeal_by_dimension.csv` (written
by `src/aggregate.py`) are the scored-pitch corpus as plain tables. The
`charts/*.png` files are static renders of everything in the Appeal Arc page,
if you want images instead of the interactive version.

**To add your own pitch or deck, or regenerate everything from source**
See "Adding your own video pitch" / "Adding your own deck" below — that's the
part that needs the API key and Python setup.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # only needed for the coding step
```

`ANTHROPIC_API_KEY` isn't required to fetch/segment transcripts or rebuild
charts from already-coded data — only `src/code_transcript.py` (and
`src/pipeline.py`, which calls it) needs it.

## Project layout

```
data/
  corpus.json           registry of every pitch/exemplar/deck — see schema below
  transcripts/          <id>.json (raw captions) + <id>.segmented.json (~45s windows)
  coded/                <id>.json — scored-pitch coding (rubric_dims + appeal)
  coded_exemplars/       <id>.json — video-exemplar coding (appeal + intensity)
  exemplars/             <id>.json — sparse highlight quotes (video) or full deck analysis (slides)
  appeal_arc_data.json   generated — the blob embedded in artifact_appeal_arc.html
src/
  fetch_transcripts.py       YouTube captions -> data/transcripts/<id>.json
  text_to_transcript.py      plain-text pitch script -> data/transcripts/<id>.json (estimated timing)
  segment.py                 raw captions -> ~45s coding windows
  code_transcript.py         Claude API coding pass (see below)
  aggregate.py / charts.py           scored-corpus stats -> charts/*.png (framework artifact's data)
  build_appeal_arc_data.py   corpus.json -> data/appeal_arc_data.json
  inject_appeal_arc_data.py  splices that JSON into artifact_appeal_arc.html
  render_appeal_arc_charts.py static PNGs matching the artifact
  pipeline.py                 runs the whole video-pitch chain in one command
```

## Adding your own video pitch

1. **Add an entry to `data/corpus.json`:**
   ```json
   {
     "id": "my_pitch_2026",
     "title": "My Pitch — Some Competition 2026",
     "youtube_url": "https://www.youtube.com/watch?v=...",
     "competition": "Some Competition 2026",
     "category": "scored",
     "medium": "video",
     "outcome_tier": "winner",
     "outcome_detail": "Winner, $X prize",
     "rubric_source": "https://..."
   }
   ```
   Use `"category": "exemplar"` instead of `"scored"` for a non-judged
   control case (like MLK or Jobs) — those get coded for appeal + intensity
   only, no rubric dimensions, and render in the closing contrast section
   instead of the scored-pitch comparison.

2. **Run the pipeline:**
   ```bash
   python3 src/pipeline.py my_pitch_2026 --mode scored
   ```
   This fetches captions, segments them, calls Claude to code every window,
   rebuilds `data/appeal_arc_data.json`, splices it into the artifact, and
   re-renders the static charts. Re-publish `artifact_appeal_arc.html`
   afterward to see it live.

3. **If it should count toward the scored-corpus aggregate stats** (the
   `appeal_by_dimension.csv` / `timeline_by_dimension.csv` behind
   `artifact_framework.html`'s charts, not the Appeal Arc page), also run:
   ```bash
   python3 src/aggregate.py && python3 src/charts.py
   ```

Each pipeline step is also runnable standalone (`--id <pitch_id>` on
`fetch_transcripts.py` / `segment.py`) if you want to fetch/segment many
pitches before coding any of them, or re-run just one step.

## Adding your own pitch as plain text (no video)

Don't have a recording — just the pitch script/text itself? Skip the YouTube
step entirely and build a transcript directly from a `.txt` file:

1. **Put your pitch in a plain-text file** — prose, one pitch, no video needed:
   ```bash
   python3 src/text_to_transcript.py my_pitch.txt --id my_pitch_2026 --title "My Pitch — Some Competition 2026" --competition "Some Competition 2026"
   ```
   This writes `data/transcripts/my_pitch_2026.json` in the exact same shape
   `fetch_transcripts.py` produces — one cue per sentence — so every later
   step works unmodified. There's no real recording to time against, so
   timing is *estimated* from a reading pace (default 140 words/minute; pass
   `--wpm` to match your own pace). That's good enough to place moments
   proportionally through the pitch — it's not a claim about actual delivery
   timing, and the artifact doesn't pretend otherwise.

2. **Add the same `data/corpus.json` entry as for a video pitch** (see above),
   except `"youtube_url": null` and `"medium": "text"`.

3. **Run the pipeline, skipping the fetch step** (there's nothing to
   download — you already have the transcript):
   ```bash
   python3 src/pipeline.py my_pitch_2026 --mode scored --skip-fetch
   ```
   Everything from here — segmenting, coding, rebuilding the artifact,
   rendering charts — is identical to the video path.

## Adding your own deck (static slides, no video)

Decks have no transcript or timing data, so they skip the fetch/segment/code
steps entirely — write the JSON by hand, following an existing deck's shape
(see `data/exemplars/airbnb_seed_deck_2008.json` for the fullest example):

```json
{
  "id": "my_deck_2026",
  "title": "My Deck — Series A, 2026",
  "medium": "static slide deck — NOT a recorded/spoken pitch",
  "note_on_medium": "...",
  "sources": ["https://..."],
  "verified_facts": { "year": 2026, "founders": ["..."], "raised": "...", "context": "...", "slide_count_note": "..." },
  "slides": [
    { "slide": "Cover", "rubric_dims": [], "dominant_appeal": "ethos", "note": "..." },
    { "slide": "Problem", "rubric_dims": ["problem_fit"], "dominant_appeal": "pathos", "note": "..." }
  ],
  "summary": "..."
}
```

`rubric_dims` values must be from `src/rubric_schema.py`'s `RUBRIC_DIMENSIONS`
keys (`problem_fit`, `tech`, `impact_evidence`, `scale_sustainability`,
`team`); `dominant_appeal` must be `pathos`, `logos`, or `ethos`. Only claim a
`sources`-backed fact as `verified_facts` — don't fabricate numbers.

Then add a `data/corpus.json` entry with `"category": "exemplar"`,
`"medium": "deck"`, `"youtube_url": null`, and run:

```bash
python3 src/build_appeal_arc_data.py \
  && python3 src/inject_appeal_arc_data.py \
  && python3 src/render_appeal_arc_charts.py
```

## `corpus.json` field reference

| Field | Meaning |
|---|---|
| `id` | Matches the filename stem everywhere else (`data/transcripts/<id>.json`, etc.) |
| `category` | `scored` (judged pitch, counted in stats) / `exemplar` (control case) / `excluded` (coded but kept out of aggregation — see the XPRIZE entry for why) |
| `medium` | `video` (fetch/segment/code from YouTube), `text` (segment/code from a plain-text script via `text_to_transcript.py`, `--skip-fetch`), or `deck` (hand-written JSON, no transcript at all) |
| `youtube_url` | Required for `medium: video`; `null` for decks |
| `outcome_tier` / `outcome_detail` | Shown in the artifact's panel header |
| `rubric_source` | Link to the competition's published judging criteria, if any |
