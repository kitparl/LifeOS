"""Writing rubric dimensions, weights, and overall-score computation."""

from __future__ import annotations

RUBRIC_VERSION = "writing-rubric-v1"
EVALUATION_VERSION = "v1"
PROMPT_VERSION = "writing-feedback-v1"

# Stable dimension keys (canonical JSON uses these camelCase / snake keys).
DIMENSIONS: tuple[str, ...] = (
    "grammar",
    "punctuation",
    "spelling",
    "clarity",
    "readability",
    "vocabulary",
    "sentenceVariety",
    "coherence",
    "structure",
    "conciseness",
    "tone",
    "intentAlignment",
    "audienceAppropriateness",
)

# Equal weights for v1 — change carefully and bump RUBRIC_VERSION.
DIMENSION_WEIGHTS: dict[str, float] = {d: 1.0 for d in DIMENSIONS}


def compute_overall_score(dimensions: dict[str, int | float]) -> int:
    """App-owned overall score from dimension scores + weights. Never trust the LLM total."""
    total_w = 0.0
    weighted = 0.0
    for key, weight in DIMENSION_WEIGHTS.items():
        if key not in dimensions:
            continue
        try:
            score = float(dimensions[key])
        except (TypeError, ValueError):
            continue
        score = max(0.0, min(100.0, score))
        weighted += score * weight
        total_w += weight
    if total_w <= 0:
        return 0
    return int(round(weighted / total_w))


def normalize_dimensions(raw: dict) -> dict[str, int]:
    """Clamp missing/invalid dimensions to 0–100 ints for every rubric key."""
    out: dict[str, int] = {}
    for key in DIMENSIONS:
        val = raw.get(key, 0) if isinstance(raw, dict) else 0
        try:
            n = int(round(float(val)))
        except (TypeError, ValueError):
            n = 0
        out[key] = max(0, min(100, n))
    return out
