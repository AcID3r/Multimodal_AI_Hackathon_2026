"""Bounded duration-weighted rubric scores; avoid counting overlapping regions twice."""
from backend.models.schemas import Flaw

DIMENSIONS = {"tone": "vocal_tone", "pacing": "pacing_rhythm", "volume": "volume_dynamics",
              "pauses": "pause_usage", "clarity": "vocal_clarity"}


def score(flaws: list[Flaw], duration: float) -> tuple[float, dict[str, float]]:
    scores = {}
    for category, dimension in DIMENSIONS.items():
        regions = [f for f in flaws if f.category == category]
        boundaries = sorted({0.0, duration} | {t for f in regions for t in (f.start_time, f.end_time)})
        penalty = 0.0
        for a, b in zip(boundaries, boundaries[1:]):
            severity = max((f.severity for f in regions if f.start_time < b and f.end_time > a), default=0)
            penalty += (b - a) * severity
        scores[dimension] = round(max(1.0, 10 - 9 * penalty / duration), 2)
    return round(sum(scores.values()) / len(scores) * 10, 2), scores
