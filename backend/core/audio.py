"""Decode, validate, downmix and resample uploaded audio without saving it."""
import io
import math
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from backend.config import MAX_DURATION_SECONDS, MAX_UPLOAD_BYTES, SAMPLE_RATE


def load_audio(source: bytes | str) -> np.ndarray:
    if isinstance(source, bytes) and len(source) > MAX_UPLOAD_BYTES:
        raise ValueError("Audio exceeds the 50 MB upload limit")
    stream = io.BytesIO(source) if isinstance(source, bytes) else source
    try:
        with sf.SoundFile(stream) as handle:
            sr = handle.samplerate
            if not 8000 <= sr <= 192000:
                raise ValueError("Sample rate must be between 8 and 192 kHz")
            duration = len(handle) / sr
            if not 0.5 <= duration <= MAX_DURATION_SECONDS:
                raise ValueError("Audio must be between 0.5 seconds and 10 minutes")
            if handle.channels > 8:
                raise ValueError("Audio has too many channels")
            audio = handle.read(dtype="float32", always_2d=True).mean(axis=1)
    except (sf.LibsndfileError, RuntimeError) as exc:
        raise ValueError("Cannot decode audio; upload a valid WAV, MP3 or FLAC file") from exc
    if not np.isfinite(audio).all():
        raise ValueError("Audio contains non-finite samples")
    if float(np.sqrt(np.mean(audio ** 2))) < 1e-6:
        raise ValueError("Recording is silent; provide audible speech")
    if sr != SAMPLE_RATE:
        factor = math.gcd(sr, SAMPLE_RATE)
        audio = resample_poly(audio, SAMPLE_RATE // factor, sr // factor).astype(np.float32)
    return audio
