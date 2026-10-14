"""Frame-level signal measurements with explicit units and missing voiced pitch."""
from dataclasses import dataclass
import re
import librosa
import numpy as np
from backend.config import SAMPLE_RATE, HOP_LENGTH, FRAME_LENGTH
from backend.models.schemas import Alignment


@dataclass
class Features:
    times: np.ndarray
    f0: np.ndarray
    pitch_relative: np.ndarray
    energy_rms: np.ndarray
    energy_db: np.ndarray
    mfcc: np.ndarray
    spectral_centroid: np.ndarray
    spectral_rolloff: np.ndarray
    spectral_flatness: np.ndarray
    zcr: np.ndarray
    speech_rate: np.ndarray
    pauses: list[dict]


def syllables(word: str) -> int:
    """English vowel-group heuristic, not a phonetic dictionary."""
    word = re.sub(r"[^a-z]", "", word.lower())
    groups = len(re.findall(r"[aeiouy]+", word))
    if word.endswith("e") and not word.endswith(("le", "ye")) and groups > 1:
        groups -= 1
    return max(1, groups)


def detect_pauses(rms: np.ndarray, times: np.ndarray, duration: float) -> list[dict]:
    cutoff = max(1e-5, float(np.percentile(rms, 90)) * 0.08)
    mask = rms < cutoff
    regions = []
    for start, end in contiguous(mask):
        a, b = float(times[start]), min(duration, float(times[end - 1]) + HOP_LENGTH / SAMPLE_RATE)
        if b - a >= 0.15:
            regions.append({"start": a, "end": b, "duration": b - a})
    return regions


def contiguous(mask: np.ndarray) -> list[tuple[int, int]]:
    bounds = np.diff(np.r_[False, mask, False].astype(int))
    return list(zip(np.flatnonzero(bounds == 1).tolist(), np.flatnonzero(bounds == -1).tolist()))


def extract_features(audio: np.ndarray, alignment: Alignment) -> Features:
    sr, hop, frame = SAMPLE_RATE, HOP_LENGTH, FRAME_LENGTH
    spectrum = np.abs(librosa.stft(audio, n_fft=frame, hop_length=hop))
    rms = librosa.feature.rms(y=audio, frame_length=frame, hop_length=hop)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    # pYIN is optional because it is substantially slower on long CPU recordings.
    # YIN + periodicity/energy gating preserves nulls for unvoiced frames.
    f0 = librosa.yin(audio, fmin=60, fmax=500, sr=sr, frame_length=frame, hop_length=hop)
    blocks = librosa.util.frame(np.pad(audio, (frame // 2, frame // 2)), frame_length=frame, hop_length=hop)
    centered = blocks - blocks.mean(axis=0)
    periodicity = np.zeros(len(f0))
    for i, frequency in enumerate(f0):
        lag = min(frame - 2, max(1, int(round(sr / frequency))))
        x, y = centered[:-lag, i], centered[lag:, i]
        periodicity[i] = np.dot(x, y) / max(1e-12, np.linalg.norm(x) * np.linalg.norm(y))
    voiced = (rms > max(1e-5, np.percentile(rms, 90) * 0.08)) & (periodicity > 0.65)
    f0[~voiced] = np.nan
    pitch = np.full_like(f0, np.nan)
    if voiced.any():
        # Center each voice in semitones but retain modulation range.
        pitch[voiced] = 12 * np.log2(f0[voiced] / np.median(f0[voiced]))
    ref = max(1e-8, float(np.percentile(rms[voiced] if voiced.any() else rms, 75)))
    db = 20 * np.log10(np.maximum(rms, 1e-8) / ref)
    rate = np.zeros(len(times))
    for word in alignment.words:
        # Spread syllables over each actual aligned word duration.
        rate += np.maximum(0, np.minimum(times + 1, word.end) - np.maximum(times - 1, word.start)) * syllables(word.word) / (word.end - word.start) / 2
    return Features(times=times, f0=f0, pitch_relative=pitch, energy_rms=rms, energy_db=db,
        mfcc=librosa.feature.mfcc(S=librosa.power_to_db(librosa.feature.melspectrogram(S=spectrum ** 2, sr=sr)), n_mfcc=13),
        spectral_centroid=librosa.feature.spectral_centroid(S=spectrum, sr=sr)[0],
        spectral_rolloff=librosa.feature.spectral_rolloff(S=spectrum, sr=sr)[0],
        spectral_flatness=librosa.feature.spectral_flatness(S=spectrum)[0],
        zcr=librosa.feature.zero_crossing_rate(audio, frame_length=frame, hop_length=hop)[0],
        speech_rate=rate, pauses=detect_pauses(rms, times, len(audio) / sr))


def word_measurements(features: Features, alignment: Alignment) -> dict[str, np.ndarray]:
    result = {name: [] for name in ("pitch_range", "speech_rate", "energy_db", "pause_gap", "spectral_flatness")}
    for i, word in enumerate(alignment.words):
        lo, hi = max(0, i - 1), min(len(alignment.words), i + 2)
        a, b = alignment.words[lo].start, alignment.words[hi - 1].end
        neighborhood = (features.times >= a) & (features.times <= b)
        pitch = features.pitch_relative[neighborhood]
        pitch = pitch[np.isfinite(pitch)]
        result["pitch_range"].append(float(np.ptp(np.percentile(pitch, [10, 90]))) if len(pitch) >= 3 else np.nan)
        result["speech_rate"].append(sum(syllables(w.word) for w in alignment.words[lo:hi]) / max(0.01, b - a))
        mask = (features.times >= word.start) & (features.times <= word.end) & np.isfinite(features.f0)
        if not mask.any():
            mask = (features.times >= word.start) & (features.times <= word.end)
        result["energy_db"].append(float(np.median(features.energy_db[mask])) if mask.any() else np.nan)
        result["spectral_flatness"].append(float(np.median(features.spectral_flatness[mask])) if mask.any() else np.nan)
        gap = alignment.words[i + 1].start - word.end if i + 1 < len(alignment.words) else 0
        result["pause_gap"].append(max(0, gap))
    return {key: np.array(value) for key, value in result.items()}
