"""Shared taxonomy for coding pitch transcript windows.

Single source of truth for the five rubric dimensions and three rhetorical
appeals from the framework artifact (artifact_framework.html). Used both as
documentation and as the schema handed to whatever codes each transcript
window in Phase 3 (currently: an agent reading the segmented transcript
directly, per the project plan — not a separate LLM API call).
"""

RUBRIC_DIMENSIONS = {
    "problem_fit": "Problem & Product-Market Fit — is there a real problem, and evidence someone already wants it solved.",
    "tech": "Tech — mechanism, defensibility, why the approach works and is hard to copy.",
    "impact_evidence": "Evidence of Impact — data proving the intervention works, plus who it worked for.",
    "scale_sustainability": "Scale & Sustainability — unit economics, distribution, what breaks at 10x.",
    "team": "Team Composition — why these specific people can execute.",
}

RHETORICAL_APPEALS = {
    "pathos": "The stakes — who the problem hurts, and why a stranger should care.",
    "logos": "The logic — mechanism, market math, evidence a judge could verify.",
    "ethos": "The credibility — why this team, this evidence, can be trusted to execute.",
}

# Shape of one entry in a data/coded/<pitch_id>.json file.
SEGMENT_CODING_SCHEMA = {
    "start": "seconds, from the transcript window",
    "end": "seconds, from the transcript window",
    "rubric_dims": "list[str] — zero or more keys from RUBRIC_DIMENSIONS present in this window",
    "dominant_appeal": "str — one key from RHETORICAL_APPEALS, the single most prominent appeal in this window",
    "confidence": "float 0-1 — how confident the coding is for this window",
}
