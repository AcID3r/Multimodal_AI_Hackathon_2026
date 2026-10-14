"""Measured evidence plus coaching suggestions; associations are not proof of cause."""
from backend.models.schemas import Delta, Explanation

ADVICE = {
    "pacing_too_fast": "Slow this phrase down and keep the words distinct.",
    "pacing_too_slow": "Practice this phrase with a steadier forward rhythm.",
    "pitch_monotone": "Try changing pitch on one or two key words in this phrase.",
    "pitch_excessive": "Reduce large pitch swings and reserve them for emphasis.",
    "volume_too_quiet": "Keep this phrase audible and support your breath through its ending.",
    "volume_too_loud": "Reduce the local volume spike while preserving intentional emphasis.",
    "pause_missing": "Try a short pause at this word boundary, then listen for clearer phrasing.",
    "pause_extra": "Try joining this phrase without the extra gap.",
    "spectral_change": "Listen for noise or articulation changes; spectral differences alone do not establish clarity.",
}


def explain(kind: str, feature: str, delta: Delta, text: str) -> Explanation:
    label = feature.replace("_", " ")
    summary = f"{label.capitalize()} measured {delta.participant:.2f} {delta.unit}, compared with {delta.baseline:.2f} in the matched baseline phrase."
    math = (f"Paired deviation = (participant - matched baseline) / scale = "
            f"({delta.participant:.3f} - {delta.baseline:.3f}) / {delta.scale:.3f} = {delta.z_score:.2f}. "
            "Scale is the larger of baseline spread and a feature-specific floor. This is a heuristic deviation, not a calibrated probability.")
    return Explanation(summary=summary, mathematical_detail=math,
                       recommendation=f"During '{text}': {ADVICE[kind]}")
