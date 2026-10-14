"""Rule labels describe measured delivery differences, never infer intent."""
RULES = {
    "pitch_range": ("tone", "pitch_monotone", "pitch_excessive", "semitones", 0.8),
    "speech_rate": ("pacing", "pacing_too_slow", "pacing_too_fast", "syllables/s", 0.8),
    "energy_db": ("volume", "volume_too_quiet", "volume_too_loud", "relative dB", 3.0),
    "pause_gap": ("pauses", "pause_missing", "pause_extra", "seconds", 0.15),
    "spectral_flatness": ("clarity", "spectral_change", "spectral_change", "flatness ratio", 0.06),
}


def classify(feature: str, signed_delta: float) -> tuple[str, str]:
    category, low, high, _, _ = RULES[feature]
    return category, high if signed_delta > 0 else low
