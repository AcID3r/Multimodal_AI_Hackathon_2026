"""End-to-end analysis. Full precision for detection; bounded arrays for the dashboard."""
import hashlib
import json
from functools import lru_cache
from pathlib import Path
import numpy as np
from backend.config import ALGORITHM_VERSION, SAMPLE_RATE
from backend.core.alignment import align_transcript, estimate_alignment, map_times, validate_alignment
from backend.core.audio import load_audio
from backend.core.features import extract_features, word_measurements
from backend.core.detector import detect_flaws
from backend.core.scorer import score
from backend.models.schemas import Alignment, AnalysisResult, Series


@lru_cache(maxsize=8)
def baseline_features(audio_path: str, alignment_json: str, modified: int):
    audio = load_audio(audio_path)
    alignment = Alignment.model_validate_json(alignment_json)
    return extract_features(audio, alignment)


def nullable(values):
    return [round(float(v), 5) if np.isfinite(v) else None for v in values]


def analyze(audio_bytes: bytes, baseline_id: str, baseline_path: Path, transcript: str,
            baseline_alignment: Alignment, participant_alignment: Alignment | None = None,
            alignment_mode: str = "forced", threshold: float = 1.5) -> AnalysisResult:
    audio = load_audio(audio_bytes)
    duration = len(audio) / SAMPLE_RATE
    if participant_alignment is None:
        if alignment_mode == "estimated":
            participant_alignment = estimate_alignment(audio, transcript)
        else:
            try:
                participant_alignment = align_transcript(audio, transcript)
            except ImportError as exc:
                raise ValueError("Install the optional WhisperX dependencies or provide alignment JSON") from exc
    validate_alignment(participant_alignment, transcript, duration)
    from backend.core.alignment import tokens
    if len(baseline_alignment.words) != len(participant_alignment.words) or any(tokens(b.word) != tokens(p.word) for b, p in zip(baseline_alignment.words, participant_alignment.words)):
        raise ValueError("Word tokenization differs from the baseline; supply matching word-level timing JSON")
    validate_alignment(baseline_alignment, transcript, len(load_audio(str(baseline_path))) / SAMPLE_RATE)
    b = baseline_features(str(baseline_path), baseline_alignment.model_dump_json(), baseline_path.stat().st_mtime_ns)
    p = extract_features(audio, participant_alignment)
    flaws = detect_flaws(word_measurements(b, baseline_alignment), word_measurements(p, participant_alignment), participant_alignment, threshold)
    overall, rubric = score(flaws, duration)
    # Identity includes every score-affecting input; no random UUID or wall-clock metadata.
    identity = hashlib.sha256(audio_bytes + baseline_path.read_bytes() + json.dumps({
        "algorithm": ALGORITHM_VERSION, "transcript": transcript, "threshold": threshold,
        "baseline": baseline_id, "b_align": baseline_alignment.model_dump(), "p_align": participant_alignment.model_dump(),
    }, sort_keys=True).encode()).hexdigest()[:24]
    warnings = ["Scores are deterministic heuristic delivery comparisons, not validated competition grades.",
                "Syllable counts use an English vowel-group heuristic; spectral changes are not proof of poor articulation."]
    if participant_alignment.method == "estimated" or baseline_alignment.method == "estimated":
        warnings.append("Approximate timing: word positions are estimated, not forced aligned. Flaw boundaries and pacing are provisional.")
    if baseline_alignment.method == "synthetic":
        warnings.append("Controlled synthetic audio fixture: tones test the signal pipeline and do not demonstrate speech evaluation accuracy.")
    if np.isfinite(p.f0).mean() < 0.15:
        warnings.append("Very few frames have reliable voiced pitch. This may be noise or unsuitable audio; tone scores are unreliable.")
    # Interpolate through finite data only, then restore voiced gaps on the participant grid.
    indices = np.unique(np.linspace(0, len(p.times) - 1, min(1200, len(p.times))).astype(int))
    timestamps = p.times[indices]
    mapped = map_times(timestamps, baseline_alignment, participant_alignment)
    series = {}
    for name, unit in [("pitch_relative", "semitones relative to speaker median"), ("energy_db", "relative dB"),
                       ("speech_rate", "syllables/s"), ("f0", "Hz"), ("spectral_centroid", "Hz")]:
        bv, pv = getattr(b, name), getattr(p, name)
        finite = np.isfinite(bv)
        baseline = np.interp(mapped, b.times[finite], bv[finite]) if finite.any() else np.full_like(mapped, np.nan)
        nearest = np.clip(np.searchsorted(b.times, mapped), 0, len(b.times) - 1)
        baseline[~finite[nearest]] = np.nan
        series[name] = Series(timestamps=nullable(timestamps), baseline=nullable(baseline), participant=nullable(pv[indices]), unit=unit)
    return AnalysisResult(analysis_id=identity, algorithm_version=ALGORITHM_VERSION, baseline_id=baseline_id,
        duration_seconds=round(duration, 4), overall_score=overall, rubric_scores=rubric,
        alignment=participant_alignment, warnings=warnings, flaw_regions=flaws, feature_timeseries=series)
